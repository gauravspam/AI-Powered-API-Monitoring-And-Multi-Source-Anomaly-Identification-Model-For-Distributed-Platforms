"""
API Routes for ML Service
Matches Java backend expectations
"""
from flask import request, jsonify
import logging
from datetime import datetime
from config.settings import config

logger = logging.getLogger(__name__)

def register_routes(app):
    """Register all API routes"""
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'UP',
            'service': config.SERVICE_NAME,
            'version': config.VERSION,
            'timestamp': datetime.now().isoformat(),
            'models_loaded': True
        }), 200
    
    @app.route('/api/predict', methods=['POST'])
    def predict_anomaly():
        """
        Main prediction endpoint called by Java backend
        
        Expected Request Body:
        {
            "apiId": 1,
            "apiName": "api_1",
            "method": "AGGREGATE",  # or "MSIF_ONLY" or "PLE_ONLY"
            "msifFeatures": [[...60 timesteps...]], # 60x5 array
            "pleFeatures": [[...1440 timesteps...]], # 1440x7 array (optional)
            "timestamp": "2026-01-17T14:00:00"
        }
        
        Response:
        {
            "apiId": 1,
            "apiName": "api_1",
            "msifScore": 0.65,
            "pleScore": 0.42,
            "hybridScore": 0.55,
            "severity": "MEDIUM",
            "confidence": "HIGH",
            "timestamp": "2026-01-17T14:00:00"
        }
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'error': 'No data provided',
                    'message': 'Request body must be JSON'
                }), 400
            
            # Extract required fields
            api_id = data.get('apiId')
            api_name = data.get('apiName')
            method = data.get('method', 'AGGREGATE')
            msif_features = data.get('msifFeatures')
            ple_features = data.get('pleFeatures')
            timestamp = data.get('timestamp', datetime.now().isoformat())
            
            logger.info(f"Received prediction request for {api_name} (method={method})")
            
            # Call detector
            result = app.detector.predict(
                msif_features=msif_features,
                ple_features=ple_features,
                method=method
            )
            
            # Build response matching AnomalyScoresResponse DTO
            response = {
                'apiId': api_id,
                'apiName': api_name,
                'msifScore': result['msif_score'],
                'pleScore': result['ple_score'],
                'hybridScore': result['hybrid_score'],
                'severity': result['severity'],
                'confidence': result['confidence'],
                'timestamp': timestamp
            }
            
            logger.info(f"Prediction complete: hybrid_score={result['hybrid_score']:.3f}, severity={result['severity']}")
            
            return jsonify(response), 200
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return jsonify({
                'error': 'Invalid input',
                'message': str(e)
            }), 400
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    
    @app.route('/api/model-info', methods=['GET'])
    def model_info():
        """Get model information"""
        return jsonify({
            'service': config.SERVICE_NAME,
            'version': config.VERSION,
            'models': {
                'msif_lstm': {
                    'name': 'Multi-Scale Isolation Forest + LSTM',
                    'window_size': config.MSIF_WINDOW_SIZE,
                    'features': config.MSIF_FEATURES,
                    'description': '60-minute window anomaly detection'
                },
                'ple_gru': {
                    'name': 'Probabilistic Label Enhancement + GRU',
                    'window_size': config.PLE_WINDOW_SIZE,
                    'features': config.PLE_FEATURES,
                    'description': '24-hour window anomaly detection'
                }
            },
            'fusion': {
                'method': 'Hybrid weighted combination',
                'msif_weight': config.MSIF_WEIGHT,
                'ple_weight': config.PLE_WEIGHT,
                'threshold': config.FUSION_THRESHOLD
            }
        }), 200
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested endpoint does not exist'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

