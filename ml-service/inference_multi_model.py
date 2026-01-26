
"""

Multi-Model Anomaly Detection API

Supports both NAB and LO2 trained models

"""

import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'



import keras

import tensorflow as tf

import numpy as np

import pickle

import json

from typing import Dict, Optional



@keras.saving.register_keras_serializable(package='CustomLosses')

class FocalLoss(keras.losses.Loss):

    def __init__(self, alpha=0.25, gamma=2.0, **kwargs):

        super().__init__(**kwargs)

        self.alpha = alpha

        self.gamma = gamma

    

    def call(self, y_true, y_pred):

        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)

        pt = tf.where(tf.equal(y_true, 1), y_pred, 1 - y_pred)

        alpha_t = tf.where(tf.equal(y_true, 1), self.alpha, 1 - self.alpha)

        focal_loss = -alpha_t * tf.pow(1 - pt, self.gamma) * tf.math.log(pt)

        return tf.reduce_mean(focal_loss)

    

    def get_config(self):

        base_config = super().get_config()

        return {**base_config, 'alpha': self.alpha, 'gamma': self.gamma}



class MultiModelDetector:

    """Anomaly detector supporting multiple trained models"""

    

    def __init__(self):

        self.models = {}

        self.load_all_models()

    

    def load_all_models(self):

        """Load all available model sets"""

        model_dirs = {

            'nab': 'models/nab',

            'lo2': 'models/lo2'

        }

        

        for name, path in model_dirs.items():

            if os.path.exists(path):

                try:

                    self.models[name] = self._load_model_set(path, name)

                    print(f"✅ Loaded {name.upper()} models (F1: {self.models[name]['metadata']['msif_lstm']['f1_score']:.3f})")

                except Exception as e:

                    print(f"❌ Failed to load {name}: {e}")

    

    def _load_model_set(self, model_dir, name):

        """Load a complete model set (MSIF+PLE+scaler+metadata)"""

        msif = keras.models.load_model(

            f'{model_dir}/msif_lstm_model.keras',

            custom_objects={'FocalLoss': FocalLoss}

        )

        ple = keras.models.load_model(

            f'{model_dir}/ple_gru_model.keras',

            custom_objects={'FocalLoss': FocalLoss}

        )

        

        with open(f'{model_dir}/scaler.pkl', 'rb') as f:

            scaler = pickle.load(f)

        

        with open(f'{model_dir}/metadata.json', 'r') as f:

            metadata = json.load(f)

        

        return {

            'msif_model': msif,

            'ple_model': ple,

            'scaler': scaler,

            'metadata': metadata,

            'msif_threshold': metadata['optimal_thresholds']['msif_lstm'],

            'ple_threshold': metadata['optimal_thresholds']['ple_gru'],

            'n_features': metadata['n_features']

        }

    

    def predict(self, features: np.ndarray, model_name='lo2', use_ensemble=True) -> Dict:

        """

        Predict anomalies

        

        Args:

            features: Feature vector (n_samples, n_features) or (n_features,)

            model_name: 'nab' or 'lo2'

            use_ensemble: Use ensemble prediction

        

        Returns:

            Prediction dict with probabilities and classifications

        """

        if model_name not in self.models:

            raise ValueError(f"Model '{model_name}' not available. Available: {list(self.models.keys())}")

        

        model_set = self.models[model_name]

        

        # Validate features

        if features.ndim == 1:

            features = features.reshape(1, -1)

        

        if features.shape[1] != model_set['n_features']:

            raise ValueError(f"Expected {model_set['n_features']} features, got {features.shape[1]}")

        

        # Scale

        features_scaled = model_set['scaler'].transform(features)

        

        # Predict

        msif_proba = model_set['msif_model'].predict(features_scaled, verbose=0).flatten()

        ple_proba = model_set['ple_model'].predict(features_scaled, verbose=0).flatten()

        

        msif_pred = (msif_proba >= model_set['msif_threshold']).astype(int)

        ple_pred = (ple_proba >= model_set['ple_threshold']).astype(int)

        

        if use_ensemble:

            ensemble_proba = (msif_proba + ple_proba) / 2

            ensemble_threshold = (model_set['msif_threshold'] + model_set['ple_threshold']) / 2

            ensemble_pred = (ensemble_proba >= ensemble_threshold).astype(int)

            

            return {

                'model': model_name,

                'predictions': ensemble_pred.tolist(),

                'probabilities': ensemble_proba.tolist(),

                'ensemble_threshold': ensemble_threshold,

                'model_details': {

                    'msif_lstm': {

                        'predictions': msif_pred.tolist(),

                        'probabilities': msif_proba.tolist(),

                        'f1_score': model_set['metadata']['msif_lstm']['f1_score']

                    },

                    'ple_gru': {

                        'predictions': ple_pred.tolist(),

                        'probabilities': ple_proba.tolist(),

                        'f1_score': model_set['metadata']['ple_gru']['f1_score']

                    }

                }

            }

        else:

            return {

                'model': model_name,

                'predictions': msif_pred.tolist(),

                'probabilities': msif_proba.tolist()

            }

    

    def get_model_info(self):

        """Get info about all loaded models"""

        info = {}

        for name, model_set in self.models.items():

            info[name] = {

                'n_features': model_set['n_features'],

                'dataset_size': model_set['metadata']['dataset_size'],

                'training_date': model_set['metadata']['training_date'],

                'msif_f1': model_set['metadata']['msif_lstm']['f1_score'],

                'ple_f1': model_set['metadata']['ple_gru']['f1_score']

            }

        return info



# ============================================================================

# DEMO

# ============================================================================



if __name__ == '__main__':

    print("="*70)

    print("MULTI-MODEL ANOMALY DETECTION API")

    print("="*70)

    

    # Initialize detector

    detector = MultiModelDetector()

    

    # Show available models

    print(f"\n📊 Available Models:")

    for name, info in detector.get_model_info().items():

        print(f"\n  {name.upper()}:")

        print(f"    Features: {info['n_features']}")

        print(f"    Dataset: {info['dataset_size']:,} samples")

        print(f"    MSIF F1: {info['msif_f1']:.3f}")

        print(f"    PLE F1: {info['ple_f1']:.3f}")

    

    # Test NAB (10 features)

    print(f"\n{'='*70}")

    print("TEST: NAB Model (10 features)")

    print("="*70)

    nab_sample = np.random.randn(10).astype(np.float32)

    nab_result = detector.predict(nab_sample, model_name='nab')

    print(f"Prediction: {'🚨 ANOMALY' if nab_result['predictions'][0] else '✅ NORMAL'}")

    print(f"Probability: {nab_result['probabilities'][0]:.4f}")

    

    # Test LO2 (100 features)

    print(f"\n{'='*70}")

    print("TEST: LO2 Model (100 features)")

    print("="*70)

    lo2_sample = np.random.randn(100).astype(np.float32)

    lo2_result = detector.predict(lo2_sample, model_name='lo2')

    print(f"Prediction: {'🚨 ANOMALY' if lo2_result['predictions'][0] else '✅ NORMAL'}")

    print(f"Probability: {lo2_result['probabilities'][0]:.4f}")

    

    print(f"\n{'='*70}")

    print("✅ Multi-Model API Ready!")

    print("="*70)

