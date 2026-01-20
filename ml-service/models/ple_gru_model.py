"""
PLE-GRU Model: Probability Label Estimation GRU
Production-ready implementation with same interface as MSIF-LSTM

Architecture:
- Input: (batch_size, 1, 10) - Lookback window of 1, 10 features
- GRU Layer 1: 128 units, return_sequences=True
- BatchNormalization + Dropout(0.2)
- GRU Layer 2: 64 units, return_sequences=False
- BatchNormalization + Dropout(0.2)
- Dense 1: 32 units, relu
- Dropout(0.2)
- Dense 2: 16 units, relu
- Output: 1 unit, sigmoid (binary anomaly classification)

Compilation:
- Optimizer: Adam (lr=0.001)
- Loss: binary_crossentropy
- Metrics: accuracy, AUC, Precision, Recall

Callbacks:
- EarlyStopping: Stop if val_loss doesn't improve for 5 epochs
- ReduceLROnPlateau: Reduce learning rate if val_loss plateaus

GRU vs LSTM: GRU is simpler (2 gates vs 3) and often faster with similar accuracy
"""

import numpy as np
import os
from typing import Dict, Optional
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import GRU, Dense, Dropout, Input, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from src.logger import logger
from config.settings import config

class PLEGRU:
    """
    Probability Label Estimation GRU Model
    
    Responsibilities:
    - Build GRU-based anomaly detection model
    - Train on labeled data
    - Make predictions
    - Persist/load model weights
    
    Same interface as MSIFLSTM for easy ensemble integration
    
    Key attributes:
    - model: Keras Sequential model
    - is_trained: Boolean flag
    - training_history: Dict with loss/accuracy history
    - input_shape: Tuple (1, 10)
    """
    
    def __init__(self, input_shape: tuple = (1, 10)):
        """
        Initialize PLE-GRU model
        
        Args:
            input_shape: Tuple (lookback_window, feature_count)
                        Default: (1, 10) - no lookback, 10 features
        """
        self.input_shape = input_shape
        self.model = None
        self.is_trained = False
        self.training_history = None
        
        logger.info(f"PLEGRU initialized with input shape {input_shape}")
    
    def build_model(self) -> None:
        """
        Build GRU neural network architecture
        
        Architecture:
        Input (batch, 1, 10)
          ↓
        GRU(128, return_sequences=True) + BatchNorm + Dropout(0.2)
          ↓
        GRU(64, return_sequences=False) + BatchNorm + Dropout(0.2)
          ↓
        Dense(32, relu) + Dropout(0.2)
          ↓
        Dense(16, relu)
          ↓
        Dense(1, sigmoid) → Output [0-1]
        
        Total parameters: ~35k (fewer than LSTM)
        
        Why GRU instead of LSTM?
        - Simpler architecture (2 gates vs 3)
        - Faster training
        - Similar accuracy
        - Good for sequential patterns
        """
        
        logger.info("=" * 60)
        logger.info("Building PLE-GRU Model Architecture")
        logger.info("=" * 60)
        
        self.model = Sequential([
            # Input layer
            Input(shape=self.input_shape),
            
            # First GRU layer - capture short-term patterns
            GRU(
                config.ML_CONFIG.PLE_UNITS[0],  # 128 units
                return_sequences=True,
                activation='relu',
                name='ple_gru_1',
                recurrent_dropout=0.2
            ),
            BatchNormalization(name='ple_bn_1'),
            Dropout(config.ML_CONFIG.DROPOUT_RATE, name='ple_dropout_1'),
            
            # Second GRU layer - capture long-term patterns
            GRU(
                config.ML_CONFIG.PLE_UNITS[1],  # 64 units
                return_sequences=False,
                activation='relu',
                name='ple_gru_2',
                recurrent_dropout=0.2
            ),
            BatchNormalization(name='ple_bn_2'),
            Dropout(config.ML_CONFIG.DROPOUT_RATE, name='ple_dropout_2'),
            
            # Dense layers - learning representations
            Dense(
                config.ML_CONFIG.PLE_UNITS[2],  # 32 units
                activation='relu',
                name='ple_dense_1'
            ),
            Dropout(config.ML_CONFIG.DROPOUT_RATE, name='ple_dropout_3'),
            
            Dense(
                config.ML_CONFIG.PLE_UNITS[3],  # 16 units
                activation='relu',
                name='ple_dense_2'
            ),
            
            # Output layer - binary classification
            Dense(1, activation='sigmoid', name='ple_output')
        ])
        
        # Compile with same config as MSIF
        self.model.compile(
            optimizer=Adam(learning_rate=config.ML_CONFIG.LEARNING_RATE),
            loss='binary_crossentropy',
            metrics=['accuracy', 'AUC', 'Precision', 'Recall']
        )
        
        total_params = self.model.count_params()
        logger.info(f"✅ PLE-GRU model built successfully")
        logger.info(f"   Total parameters: {total_params:,}")
        logger.info(f"   Learning rate: {config.ML_CONFIG.LEARNING_RATE}")
        logger.info(f"   Dropout rate: {config.ML_CONFIG.DROPOUT_RATE}")
        
        # Print summary
        logger.debug("Model summary:")
        self.model.summary(print_fn=lambda x: logger.debug(x))
    
    def train(self,
              X_train: np.ndarray,
              y_train: np.ndarray,
              X_val: np.ndarray = None,
              y_val: np.ndarray = None,
              epochs: int = None,
              batch_size: int = None) -> Dict[str, list]:
        """
        Train PLE-GRU on labeled anomaly data
        
        Args:
            X_train: Training features (n_samples, feature_count)
                    Will be reshaped to (n_samples, 1, feature_count)
            y_train: Training labels (n_samples,) - 0 or 1
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            epochs: Number of epochs (default from config)
            batch_size: Batch size (default from config)
        
        Returns:
            Training history dict
        
        Example:
            >>> ple = PLEGRU()
            >>> ple.build_model()
            >>> history = ple.train(X_train, y_train, X_val, y_val)
        """
        
        if self.model is None:
            logger.warning("Model not built. Building now...")
            self.build_model()
        
        epochs = epochs or config.ML_CONFIG.EPOCHS
        batch_size = batch_size or config.ML_CONFIG.BATCH_SIZE
        
        # Reshape
        if X_train.ndim == 2:
            X_train = X_train.reshape((X_train.shape[0], 1, X_train.shape[1]))
            logger.info(f"Reshaped X_train to {X_train.shape}")
        
        if X_val is not None and X_val.ndim == 2:
            X_val = X_val.reshape((X_val.shape[0], 1, X_val.shape[1]))
            logger.info(f"Reshaped X_val to {X_val.shape}")
        
        logger.info("=" * 60)
        logger.info("Starting PLE-GRU Training")
        logger.info("=" * 60)
        logger.info(f"Epochs: {epochs}")
        logger.info(f"Batch size: {batch_size}")
        logger.info(f"Training samples: {X_train.shape[0]:,}")
        if X_val is not None:
            logger.info(f"Validation samples: {X_val.shape[0]:,}")
        
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True,
                verbose=1,
                mode='min'
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                min_lr=1e-6,
                verbose=1,
                mode='min'
            )
        ]
        
        validation_data = (X_val, y_val) if X_val is not None else None
        
        try:
            history = self.model.fit(
                X_train, y_train,
                validation_data=validation_data,
                epochs=epochs,
                batch_size=batch_size,
                callbacks=callbacks,
                verbose=1
            )
            
            self.training_history = history.history
            self.is_trained = True
            
            logger.info("=" * 60)
            logger.info("✅ PLE-GRU Training Completed")
            logger.info("=" * 60)
            logger.info(f"Final train loss: {history.history['loss'][-1]:.4f}")
            if validation_data:
                logger.info(f"Final val loss: {history.history['val_loss'][-1]:.4f}")
            
            return self.training_history
        
        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
            raise
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """
        Make anomaly predictions
        
        Args:
            features: np.ndarray of shape (n_samples, feature_count)
                     or (n_samples, 1, feature_count)
        
        Returns:
            Anomaly scores np.ndarray of shape (n_samples,)
            Values in [0, 1] where 0=normal, 1=anomaly
        
        Raises:
            RuntimeError if model not built
        """
        
        if self.model is None:
            raise RuntimeError(
                "Model not built! Call build_model() or load() first."
            )
        
        if features.ndim == 2:
            features = features.reshape((features.shape[0], 1, features.shape[1]))
        
        predictions = self.model.predict(features, verbose=0)
        return predictions.flatten()
    
    def save(self, path: str) -> None:
        """
        Save trained model to disk
        
        Creates: trained_models/ple_gru_model.h5
        
        Args:
            path: Directory path to save model
        
        Raises:
            RuntimeError if no model built
        """
        
        if self.model is None:
            raise RuntimeError("No model to save! Train or build model first.")
        
        os.makedirs(path, exist_ok=True)
        model_path = os.path.join(path, 'ple_gru_model.h5')
        
        try:
            self.model.save(model_path)
            logger.info(f"✅ PLE-GRU model saved to {model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}", exc_info=True)
            raise
    
    def load(self, path: str) -> None:
        """
        Load pre-trained model from disk
        
        Expects: trained_models/ple_gru_model.h5
        
        Args:
            path: Directory path where model is saved
        
        Raises:
            FileNotFoundError if model not found
        """
        
        model_path = os.path.join(path, 'ple_gru_model.h5')
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                f"Make sure to train and save model first."
            )
        
        try:
            self.model = load_model(model_path)
            self.is_trained = True
            logger.info(f"✅ PLE-GRU model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise
