"""
Production Flask API for AI-Powered Anomaly Detection System
Exposes HybridAnomalyDetector as REST endpoints with monitoring

Endpoints:
- GET  /health              Health check + model status
- POST /predict             Predict anomalies on normalized features
- GET  /metrics             Prometheus metrics
- GET  /stats               System statistics
- POST /predict-batch       Batch predictions (10-1000 samples)

Features:
- Pydantic request/response validation
- Error handling with trace IDs
- Request logging with trace correlation
- Performance monitoring
- Model status checks
- Batch processing support

Production Ready:
- CORS enabled
- Request rate limiting hooks
- Comprehensive logging
- Prometheus metrics integration
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
import time
from datetime import datetime
from typing import Dict, List

import numpy as np
from config.settings import config
from flask import Flask, jsonify, request
from flask_cors import CORS
from models.data_preprocessor import DataPreprocessor
from models.hybrid_fusion import HybridAnomalyDetector
from models.schemas import (
    ErrorResponse,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
    ValidationErrorResponse,
)
from pydantic import ValidationError

# Local imports
from src.logger import logger
from src.model_registry import ModelRegistry

# ============= FLASK APP INITIALIZATION =============

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize globally
detector = None
preprocessor = None
registry = None

# Prometheus metrics
prediction_count = 0
anomaly_count = 0
error_count = 0
total_processing_time = 0.0


def initialize_app():
    """Initialize app with models and preprocessor"""
    global detector, preprocessor, registry

    logger.info("=" * 60)
    logger.info("Initializing API Application")
    logger.info("=" * 60)

    try:
        # Initialize model registry for versioning
        registry_path = os.path.join(config.MODEL_DIR, 'registry.json')
        registry = ModelRegistry(registry_path)
        logger.info(f"Model registry loaded from {registry_path}")

        # Initialize detector (loads trained models)
        model_path = config.MODEL_DIR  # Use MODEL_DIR instead
        detector = HybridAnomalyDetector(model_path)

        if not detector.models_loaded:
            logger.warning(
                "⚠️  Models not loaded. API will return errors until models are trained."
            )
        else:
            logger.info("✅ Models loaded successfully")

        # Initialize preprocessor (loads scaler)
        preprocessor = DataPreprocessor()
        preprocessor.load(model_path)
        logger.info("✅ Data preprocessor loaded")

        logger.info("=" * 60)
        logger.info("✅ API Initialization Complete")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Failed to initialize API: {e}", exc_info=True)
        raise


# ============= UTILITY FUNCTIONS =============

def generate_trace_id():
    """Generate unique trace ID for request correlation"""
    import uuid
    return str(uuid.uuid4())[:8]


def format_error_response(error: str, message: str = None, trace_id: str = None):
    """Format error response following schema"""
    return {
        'error': error,
        'message': message,
        'trace_id': trace_id
    }


# ============= HEALTH CHECK ENDPOINT =============

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint - returns service status and model information

    Response (HealthResponse schema):
    {
        "status": "healthy" or "unhealthy",
        "version": "1.0.0",
        "models_loaded": true,
        "models_info": {
            "msif": {"loaded": true, "type": "LSTM"},
            "ple": {"loaded": true, "type": "GRU"}
        },
        "timestamp": "2026-01-19T12:30:45Z"
    }

    Status codes:
    - 200: Service healthy
    - 503: Service unhealthy (models not loaded)
    """

    trace_id = generate_trace_id()

    try:
        if detector is None or preprocessor is None:
            status = "unhealthy"
            status_code = 503
        else:
            status = "healthy" if detector.models_loaded else "unhealthy"
            status_code = 200 if detector.models_loaded else 503

        response = HealthResponse(
            status=status,
            version=config.API_VERSION,
            models_loaded=detector.models_loaded if detector else False,
            models_info={
                'msif': {
                    'loaded': detector.msif.is_trained if detector else False,
                    'type': 'LSTM'
                },
                'ple': {
                    'loaded': detector.ple.is_trained if detector else False,
                    'type': 'GRU'
                },
                'hybrid': {
                    'loaded': detector.models_loaded if detector else False,
                    'type': 'Weighted Ensemble'
                }
            },
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )

        logger.info(
            f"Health check: status={status}, "
            f"models_loaded={detector.models_loaded if detector else False}, "
            f"trace_id={trace_id}"
        )

        return response.dict(), status_code

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return format_error_response(
            'health_check_failed',
            str(e),
            trace_id
        ), 500


# ============= MAIN PREDICTION ENDPOINT =============

@app.route('/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint - predict anomalies on single request

    Request (PredictionRequest schema):
    {
        "response_time": 250,
        "status_code": 200,
        "request_count": 100,
        "error_rate": 0.02,
        "cpu_usage": 50,
        "memory_usage": 60,
        "network_io": 300,
        "disk_io": 100,
        "hour_of_day": 14,
        "day_of_week": 1,
        "context": {
            "hour_of_day": 14,
            "endpoint_type": "api",
            "traffic_level": "high"
        },
        "trace_id": "trace-12345"
    }

    Response (PredictionResponse schema):
    {
        "msif_score": 0.23,
        "ple_score": 0.18,
        "hybrid_score": 0.21,
        "severity": "LOW",
        "confidence": 0.95,
        "weights_used": {"msif": 0.35, "ple": 0.65},
        "fusion_method": "weighted_agreement",
        "models_loaded": true,
        "processing_time_ms": 45.2,
        "trace_id": "trace-12345"
    }

    Status codes:
    - 200: Prediction successful
    - 400: Validation error (invalid input)
    - 503: Models not loaded
    - 500: Server error
    """

    global prediction_count, anomaly_count, error_count, total_processing_time
    trace_id = generate_trace_id()
    start_time = time.time()

    try:
        # ============= STEP 1: Parse and validate request =============

        try:
            request_data = PredictionRequest(**request.json)
        except ValidationError as e:
            error_count += 1
            logger.warning(f"Validation error: {e.json()}, trace_id={trace_id}")

            return {
                'error': 'validation_error',
                'details': e.errors(),
                'trace_id': trace_id
            }, 400

        # ============= STEP 2: Check models loaded =============

        if not detector or not detector.models_loaded:
            error_count += 1
            logger.error(f"Models not loaded, trace_id={trace_id}")

            return format_error_response(
                'models_not_loaded',
                'Trained models not available. Run training first.',
                trace_id
            ), 503

        # ============= STEP 3: Extract and normalize features =============

        try:
            # Extract features from request
            features = preprocessor.extract_features(request_data.dict())

            # Normalize features
            normalized = preprocessor.normalize_features(features)

            logger.debug(f"Features extracted and normalized, trace_id={trace_id}")

        except Exception as e:
            error_count += 1
            logger.error(f"Feature extraction failed: {e}, trace_id={trace_id}",
                        exc_info=True)

            return format_error_response(
                'feature_extraction_failed',
                str(e),
                trace_id
            ), 400

        # ============= STEP 4: Make prediction =============

        try:
            # Get prediction from hybrid detector
            prediction = detector.predict(
                normalized,
                context=request_data.context
            )

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            prediction['processing_time_ms'] = processing_time_ms
            prediction['trace_id'] = request_data.trace_id or trace_id

            # Update metrics
            prediction_count += 1
            total_processing_time += processing_time_ms
            if prediction['severity'] in ['HIGH', 'CRITICAL']:
                anomaly_count += 1

            logger.info(
                f"Prediction successful: "
                f"score={prediction['hybrid_score']:.3f}, "
                f"severity={prediction['severity']}, "
                f"time={processing_time_ms:.1f}ms, "
                f"trace_id={trace_id}"
            )

        except Exception as e:
            error_count += 1
            logger.error(f"Prediction failed: {e}, trace_id={trace_id}",
                        exc_info=True)

            return format_error_response(
                'prediction_failed',
                str(e),
                trace_id
            ), 500

        # ============= STEP 5: Validate and return response =============

        try:
            response = PredictionResponse(**prediction)
            return response.dict(), 200

        except ValidationError as e:
            error_count += 1
            logger.error(
                f"Response validation failed: {e.json()}, trace_id={trace_id}",
                exc_info=True
            )

            return format_error_response(
                'response_validation_failed',
                'Internal error formatting response',
                trace_id
            ), 500

    except Exception as e:
        error_count += 1
        logger.error(f"Unexpected error: {e}, trace_id={trace_id}", exc_info=True)

        return format_error_response(
            'internal_server_error',
            'An unexpected error occurred',
            trace_id
        ), 500


# ============= BATCH PREDICTION ENDPOINT =============

@app.route('/predict-batch', methods=['POST'])
def predict_batch():
    """
    Batch prediction endpoint - predict multiple samples at once

    Request:
    {
        "predictions": [
            {...PredictionRequest...},
            {...PredictionRequest...},
            ...
        ]
    }

    Response:
    {
        "predictions": [
            {...PredictionResponse...},
            {...PredictionResponse...},
            ...
        ],
        "total": 100,
        "anomalies": 5,
        "processing_time_ms": 450.2,
        "trace_id": "trace-12345"
    }

    Limits:
    - Max 1000 samples per batch
    - Returns 400 if exceeds limit

    Status codes:
    - 200: All predictions successful
    - 207: Partial success (some failed)
    - 400: Invalid request
    - 503: Models not loaded
    """

    trace_id = generate_trace_id()
    start_time = time.time()

    try:
        data = request.json
        predictions_data = data.get('predictions', [])

        # Validate batch size
        if len(predictions_data) == 0:
            return format_error_response(
                'empty_batch',
                'predictions list is empty',
                trace_id
            ), 400

        if len(predictions_data) > 1000:
            return format_error_response(
                'batch_too_large',
                f'Max 1000 samples, got {len(predictions_data)}',
                trace_id
            ), 400

        if not detector or not detector.models_loaded:
            return format_error_response(
                'models_not_loaded',
                'Models not available',
                trace_id
            ), 503

        # Process batch
        results = []
        errors = []
        anomaly_count_batch = 0

        for i, pred_data in enumerate(predictions_data):
            try:
                request_obj = PredictionRequest(**pred_data)
                features = preprocessor.extract_features(request_obj.dict())
                normalized = preprocessor.normalize_features(features)

                prediction = detector.predict(normalized, context=request_obj.context)
                prediction['processing_time_ms'] = 0.0  # Set per-batch
                prediction['trace_id'] = request_obj.trace_id or f"{trace_id}-{i}"

                response = PredictionResponse(**prediction)
                results.append(response.dict())

                if prediction['severity'] in ['HIGH', 'CRITICAL']:
                    anomaly_count_batch += 1

            except Exception as e:
                logger.warning(f"Batch item {i} failed: {e}")
                errors.append({
                    'index': i,
                    'error': str(e)
                })

        # Calculate batch processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Determine status code
        if len(errors) == 0:
            status_code = 200
        elif len(results) > 0:
            status_code = 207  # Partial success
        else:
            status_code = 400  # All failed

        response = {
            'predictions': results,
            'total': len(predictions_data),
            'successful': len(results),
            'failed': len(errors),
            'errors': errors if errors else None,
            'anomalies': anomaly_count_batch,
            'processing_time_ms': processing_time_ms,
            'trace_id': trace_id
        }

        logger.info(
            f"Batch prediction: {len(results)}/{len(predictions_data)} successful, "
            f"time={processing_time_ms:.1f}ms, trace_id={trace_id}"
        )

        return response, status_code

    except Exception as e:
        logger.error(f"Batch prediction failed: {e}", exc_info=True)
        return format_error_response(
            'batch_prediction_failed',
            str(e),
            trace_id
        ), 500


# ============= METRICS ENDPOINT =============

@app.route('/metrics', methods=['GET'])
def metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus format:
    - api_predictions_total: Total predictions made
    - api_anomalies_total: Total anomalies detected
    - api_errors_total: Total errors
    - api_processing_time_avg_ms: Average processing time
    - api_anomaly_rate: Current anomaly detection rate

    Example output:
    # HELP api_predictions_total Total predictions made
    # TYPE api_predictions_total counter
    api_predictions_total 1234

    api_anomalies_total 45
    api_errors_total 2
    api_processing_time_avg_ms 48.5
    api_anomaly_rate 0.036
    """

    try:
        avg_time = (
            total_processing_time / prediction_count
            if prediction_count > 0
            else 0.0
        )

        anomaly_rate = (
            anomaly_count / prediction_count
            if prediction_count > 0
            else 0.0
        )

        metrics_output = f"""# HELP api_predictions_total Total predictions made
# TYPE api_predictions_total counter
api_predictions_total {prediction_count}

# HELP api_anomalies_total Total anomalies detected
# TYPE api_anomalies_total counter
api_anomalies_total {anomaly_count}

# HELP api_errors_total Total prediction errors
# TYPE api_errors_total counter
api_errors_total {error_count}

# HELP api_processing_time_avg_ms Average processing time in milliseconds
# TYPE api_processing_time_avg_ms gauge
api_processing_time_avg_ms {avg_time:.2f}

# HELP api_anomaly_rate Current anomaly detection rate
# TYPE api_anomaly_rate gauge
api_anomaly_rate {anomaly_rate:.4f}

# HELP api_detector_status Model status (1=loaded, 0=not loaded)
# TYPE api_detector_status gauge
api_detector_status {1 if detector and detector.models_loaded else 0}
"""

        return metrics_output, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}", exc_info=True)
        return "# Error generating metrics\n", 500, {'Content-Type': 'text/plain'}


# ============= STATISTICS ENDPOINT =============

@app.route('/stats', methods=['GET'])
def stats():
    """
    System statistics endpoint

    Returns:
    {
        "detector": {
            "total_predictions": 1234,
            "anomalies_detected": 45,
            "anomaly_rate": 0.036,
            "models_loaded": true,
            "msif_status": "trained",
            "ple_status": "trained"
        },
        "api": {
            "total_requests": 1234,
            "total_errors": 2,
            "error_rate": 0.0016,
            "avg_processing_time_ms": 48.5
        },
        "timestamp": "2026-01-19T12:30:45Z"
    }
    """

    try:
        if detector is None:
            detector_stats = {}
        else:
            detector_stats = detector.get_stats()

        avg_time = (
            total_processing_time / prediction_count
            if prediction_count > 0
            else 0.0
        )

        error_rate = (
            error_count / prediction_count
            if prediction_count > 0
            else 0.0
        )

        response = {
            'detector': detector_stats,
            'api': {
                'total_requests': prediction_count,
                'total_errors': error_count,
                'error_rate': error_rate,
                'avg_processing_time_ms': avg_time
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        return response, 200

    except Exception as e:
        logger.error(f"Stats endpoint failed: {e}", exc_info=True)
        return format_error_response(
            'stats_failed',
            str(e)
        ), 500


# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found"""
    trace_id = generate_trace_id()
    logger.warning(f"404 Not Found: {request.path}, trace_id={trace_id}")
    return format_error_response(
        'not_found',
        f'Endpoint {request.path} not found',
        trace_id
    ), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed"""
    trace_id = generate_trace_id()
    logger.warning(
        f"405 Method Not Allowed: {request.method} {request.path}, "
        f"trace_id={trace_id}"
    )
    return format_error_response(
        'method_not_allowed',
        f'Method {request.method} not allowed for {request.path}',
        trace_id
    ), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error"""
    trace_id = generate_trace_id()
    logger.error(f"500 Internal Server Error: {error}, trace_id={trace_id}")
    return format_error_response(
        'internal_server_error',
        'An unexpected error occurred',
        trace_id
    ), 500


# ============= APPLICATION ENTRY POINT =============

if __name__ == '__main__':
    # Initialize before starting server
    initialize_app()

    # Start Flask app
    port = int(os.getenv('PORT', 9000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting Flask API on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=False  # Important: prevents double initialization
    )
