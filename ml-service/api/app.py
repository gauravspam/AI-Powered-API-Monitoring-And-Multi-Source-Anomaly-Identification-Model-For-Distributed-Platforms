"""
Flask ML Service for Anomaly Detection
Provides /api/predict endpoint for Java backend
"""
import logging
import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import config
from models.hybrid_fusion import HybridAnomalyDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })

    # Initialize detector
    logger.info("Initializing HybridAnomalyDetector...")
    app.detector = HybridAnomalyDetector()
    logger.info("ML Service initialized successfully")

    # Register routes
    from api.routes import register_routes
    register_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()
    logger.info(f"Starting ML Service on {config.HOST}:{config.PORT}")
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )

