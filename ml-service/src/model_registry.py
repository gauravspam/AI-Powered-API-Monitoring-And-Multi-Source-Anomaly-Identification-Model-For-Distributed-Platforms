"""
Model versioning and registry system
Tracks all trained models with metadata
Enables rollback and A/B testing
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from src.logger import logger
from config.settings import config

class ModelMetadata:
    """
    Stores metadata about a trained model version
    
    Includes:
    - Version number
    - Creation timestamp
    - Performance metrics
    - Feature list
    - Hyperparameters used
    """
    
    def __init__(self, model_name: str, version: str):
        """
        Initialize metadata
        
        Args:
            model_name: Name of model (e.g., 'msif_lstm', 'ple_gru')
            version: Version string (e.g., '1', '2')
        """
        self.model_name = model_name
        self.version = version
        self.created_at = datetime.utcnow().isoformat()
        self.metrics = {}  # Will store: accuracy, precision, recall, f1, auc
        self.features = config.FEATURES.NAMES
        self.hyperparameters = {
            'learning_rate': config.ML_CONFIG.LEARNING_RATE,
            'batch_size': config.ML_CONFIG.BATCH_SIZE,
            'epochs': config.ML_CONFIG.EPOCHS,
            'dropout_rate': config.ML_CONFIG.DROPOUT_RATE
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'model_name': self.model_name,
            'version': self.version,
            'created_at': self.created_at,
            'metrics': self.metrics,
            'features': self.features,
            'hyperparameters': self.hyperparameters
        }
    
    def save(self, path: str) -> None:
        """
        Save metadata to JSON file
        
        Args:
            path: Full path to save metadata file
        """
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved metadata for {self.model_name} v{self.version} to {path}")
    
    @staticmethod
    def load(path: str) -> 'ModelMetadata':
        """
        Load metadata from JSON file
        
        Args:
            path: Full path to metadata file
        
        Returns:
            ModelMetadata instance
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        metadata = ModelMetadata(data['model_name'], data['version'])
        metadata.metrics = data.get('metrics', {})
        return metadata

class ModelRegistry:
    """
    Central registry for all trained models
    
    Responsibilities:
    - Track all model versions
    - Store metadata for each version
    - Compute file integrity hashes
    - Enable version retrieval
    """
    
    def __init__(self, registry_dir: str = None):
        """
        Initialize registry
        
        Args:
            registry_dir: Directory to store registry file (defaults to config.MODEL_DIR)
        """
        self.registry_dir = registry_dir or config.MODEL_DIR
        self.registry_file = os.path.join(self.registry_dir, 'registry.json')
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        """
        Load registry from disk
        
        Returns:
            Registry dict or empty dict if not found
        """
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {'models': {}}
    
    def _save_registry(self) -> None:
        """Save registry to disk"""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def register_model(self, model_name: str, model_path: str, 
                      metrics: Dict[str, float] = None) -> int:
        """
        Register a trained model
        
        Args:
            model_name: Name of model (e.g., 'msif_lstm')
            model_path: Full path to model file (.h5)
            metrics: Dict of performance metrics
        
        Returns:
            Version number assigned
        """
        
        # Compute file hash for integrity checking
        file_hash = self._compute_hash(model_path)
        logger.info(f"File hash (SHA256): {file_hash[:16]}...")
        
        # Get latest version and increment
        latest_version = self._get_latest_version(model_name)
        new_version = latest_version + 1
        
        logger.info(f"Registering {model_name} v{new_version}")
        
        # Create metadata
        metadata = ModelMetadata(model_name, str(new_version))
        if metrics:
            metadata.metrics = metrics
        
        # Save metadata file
        metadata_path = os.path.join(
            self.registry_dir,
            f'{model_name}_v{new_version}_metadata.json'
        )
        metadata.save(metadata_path)
        
        # Update registry
        if model_name not in self.registry['models']:
            self.registry['models'][model_name] = []
        
        self.registry['models'][model_name].append({
            'version': new_version,
            'path': model_path,
            'metadata_path': metadata_path,
            'file_hash': file_hash,
            'created_at': metadata.created_at,
            'metrics': metrics or {}
        })
        
        self._save_registry()
        logger.info(f"✅ Registered {model_name} v{new_version}")
        
        return new_version
    
    def get_model_path(self, model_name: str, version: str = 'latest') -> str:
        """
        Get path to model file
        
        Args:
            model_name: Name of model
            version: Version number or 'latest'
        
        Returns:
            Path to model file
        
        Raises:
            ValueError if model or version not found
        """
        
        if model_name not in self.registry['models']:
            raise ValueError(f"Model {model_name} not found in registry")
        
        versions = self.registry['models'][model_name]
        
        if version == 'latest':
            model_info = versions[-1]
        else:
            matching = [v for v in versions if v['version'] == int(version)]
            if not matching:
                raise ValueError(f"Version {version} not found for {model_name}")
            model_info = matching[0]
        
        path = model_info['path']
        
        # Verify file integrity
        if not self._verify_hash(path, model_info['file_hash']):
            logger.warning(f"⚠️  File hash mismatch for {model_name}. File may be corrupted.")
        
        return path
    
    def _get_latest_version(self, model_name: str) -> int:
        """Get latest version number for a model"""
        if model_name not in self.registry['models']:
            return 0
        versions = self.registry['models'][model_name]
        return versions[-1]['version'] if versions else 0
    
    def _compute_hash(self, filepath: str) -> str:
        """Compute SHA256 hash of file for integrity checking"""
        sha256_hash = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b''):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _verify_hash(self, filepath: str, expected_hash: str) -> bool:
        """Verify file hasn't been corrupted"""
        computed_hash = self._compute_hash(filepath)
        return computed_hash == expected_hash
    
    def list_models(self) -> Dict[str, list]:
        """
        Get all registered models
        
        Returns:
            Dict mapping model names to their version history
        """
        return self.registry['models']
    
    def get_model_stats(self, model_name: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a model
        
        Args:
            model_name: Name of model
        
        Returns:
            Dict with version history and metrics
        """
        if model_name not in self.registry['models']:
            return {}
        
        versions = self.registry['models'][model_name]
        return {
            'total_versions': len(versions),
            'latest_version': versions[-1]['version'],
            'versions': [
                {
                    'version': v['version'],
                    'created_at': v['created_at'],
                    'metrics': v['metrics']
                }
                for v in versions
            ]
        }
