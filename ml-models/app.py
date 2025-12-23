"""
ML Service for Anomaly Detection
Provides endpoints for MSFI-LSTM and PLE-GRU model inference
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'ml-service',
        'models': {
            'msfi-lstm': 'available',
            'ple-gru': 'available'
        }
    }), 200

@app.route('/api/v1/models', methods=['GET'])
def list_models():
    """List available ML models"""
    return jsonify({
        'models': [
            {
                'name': 'msfi-lstm-v1',
                'type': 'MSFI-LSTM',
                'status': 'available',
                'description': 'Multi-Scale Feature Integration LSTM model'
            },
            {
                'name': 'ple-gru-v1',
                'type': 'PLE-GRU',
                'status': 'available',
                'description': 'Pattern Learning Enhanced GRU model'
            }
        ]
    }), 200

@app.route('/api/v1/predict', methods=['POST'])
def predict():
    """
    Run anomaly detection on log data
    Expected payload:
    {
        "model_name": "msfi-lstm-v1" or "ple-gru-v1",
        "data": [...],  # Array of log entries
        "sequence_length": 100  # Optional
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'model_name' not in data or 'data' not in data:
            return jsonify({
                'error': 'Invalid request. Required fields: model_name, data'
            }), 400
        
        model_name = data.get('model_name')
        log_data = data.get('data')
        sequence_length = data.get('sequence_length', 100)
        
        # TODO: Implement actual model inference
        # For now, return mock predictions
        predictions = []
        for i, log_entry in enumerate(log_data):
            # Mock anomaly score (replace with actual model inference)
            score = 0.3 + (i % 10) * 0.05  # Mock score between 0.3 and 0.75
            predictions.append({
                'log_index': i,
                'anomaly_score': round(score, 6),
                'is_anomaly': score > 0.7,
                'model_used': model_name
            })
        
        return jsonify({
            'predictions': predictions,
            'model_name': model_name,
            'total_processed': len(log_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/v1/retrain', methods=['POST'])
def retrain():
    """
    Trigger model retraining (async operation)
    Expected payload:
    {
        "model_name": "msfi-lstm-v1" or "ple-gru-v1",
        "training_data_path": "path/to/data"  # Optional
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'model_name' not in data:
            return jsonify({
                'error': 'Invalid request. Required field: model_name'
            }), 400
        
        model_name = data.get('model_name')
        
        # TODO: Implement actual retraining logic
        # For now, return mock response
        return jsonify({
            'status': 'accepted',
            'model_name': model_name,
            'message': 'Retraining job queued',
            'job_id': f'retrain-{model_name}-{os.urandom(8).hex()}'
        }), 202
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)

