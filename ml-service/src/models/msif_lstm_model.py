"""
MSIF-LSTM Model: Multi-Source Information Fusion LSTM
Production-ready implementation with full refinements (v2.0 - FIXED)

HOTFIX APPLIED: Removed ReduceLROnPlateau (incompatible with LearningRateSchedule)

Architecture:
- Input: (batch_size, 1, 10) - Lookback window of 1, 10 features
- LSTM Layer 1: 128 units, return_sequences=True
- BatchNormalization + Dropout(0.2)
- LSTM Layer 2: 64 units, return_sequences=False
- BatchNormalization + Dropout(0.2)
- Dense 1: 32 units, relu
- Dropout(0.2)
- Dense 2: 16 units, relu
- Output: 1 unit, sigmoid (binary anomaly classification)

Compilation:
- Optimizer: Adam (lr=0.001) with optional learning rate schedule
- Loss: binary_crossentropy
- Metrics: accuracy, AUC, Precision, Recall

Callbacks:
- EarlyStopping: Stop if val_loss doesn't improve for 5 epochs
- (ReduceLROnPlateau removed - incompatible with LearningRateSchedule)

Refinements Added (v2.0):
✅ Input validation layer
✅ Class imbalance handling with automatic weights
✅ Comprehensive evaluation metrics (PR-AUC, ROC-AUC, F1)
✅ Threshold-based prediction for imbalanced data
✅ Learning rate scheduling (optional)
✅ Enhanced logging and error handling
"""

import os
from typing import Dict, Optional, Tuple

import numpy as np
from config.settings import config
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from src.logger import logger
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import LSTM, BatchNormalization, Dense, Dropout, Input
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.optimizers.schedules import PolynomialDecay


class MSIFLSTM:
    """
    Multi-Source Information Fusion LSTM Model (v2.0 - Refined)

    Responsibilities:
    - Build bidirectional LSTM architecture
    - Validate input features before prediction
    - Train on labeled anomaly data with class imbalance handling
    - Make predictions on normalized features
    - Evaluate with comprehensive metrics
    - Persist/load model weights

    Key attributes:
    - model: Keras Sequential model
    - is_trained: Boolean flag
    - training_history: Dict with loss/accuracy history
    - input_shape: Tuple (1, 10) - lookback window, feature count
    - validation_stats: Dict tracking prediction statistics

    Example:
        >>> msif = MSIFLSTM()
        >>> msif.build_model(use_lr_schedule=True)
        >>> history = msif.train(X_train, y_train, X_val, y_val, auto_class_weight=True)
        >>> eval_results = msif.evaluate(X_test, y_test, threshold=0.6)
        >>> result = msif.predict_with_threshold(X_test, threshold=0.6)
    """

    def __init__(self, input_shape: tuple = (1, 10)):
        """
        Initialize MSIF-LSTM model

        Args:
            input_shape: Tuple (lookback_window, feature_count)
                        Default: (1, 10) - no lookback, 10 features
        """
        self.input_shape = input_shape
        self.model = None
        self.is_trained = False
        self.training_history = None
        self.class_weights = None

        logger.info(f"MSIFLSTM v2.0 initialized with input shape {input_shape}")

    # ============= VALIDATION LAYER =============

    def _validate_features(self, features: np.ndarray) -> np.ndarray:
        """Validate input features before prediction"""

        if not isinstance(features, np.ndarray):
            try:
                features = np.array(features, dtype=np.float32)
                logger.debug(f"Converted input to numpy array, shape: {features.shape}")
            except Exception as e:
                raise TypeError(f"Cannot convert input to numpy array: {e}")

        if features.dtype != np.float32 and features.dtype != np.float64:
            features = features.astype(np.float32)

        if features.ndim not in [1, 2, 3]:
            raise ValueError(
                f"Expected 1D, 2D, or 3D array, got {features.ndim}D. "
                f"Shape: {features.shape}"
            )

        if features.ndim == 3 and features.shape[1] == 1:
            features = features.reshape((features.shape[0], features.shape[2]))

        if features.shape[-1] != 10:
            raise ValueError(
                f"Expected 10 features, got {features.shape[-1]}. "
                f"Shape: {features.shape}. "
                f"Ensure DataPreprocessor outputs exactly 10 features."
            )

        if np.any(np.isnan(features)):
            nan_count = np.sum(np.isnan(features))
            raise ValueError(
                f"Input contains {nan_count} NaN values. "
                f"Check for missing data in preprocessing."
            )

        if np.any(np.isinf(features)):
            inf_count = np.sum(np.isinf(features))
            raise ValueError(
                f"Input contains {inf_count} Inf values. "
                f"Check for division by zero or extreme values."
            )

        max_abs_value = np.max(np.abs(features))
        if max_abs_value > 5.0:
            logger.warning(
                f"⚠️  Input contains values outside normalized range [-1, 1]. "
                f"Max absolute value: {max_abs_value:.2f}. "
                f"Model was trained on normalized data [-1, 1]. "
                f"Predictions may be unreliable."
            )

        if features.ndim > 1:
            feature_std = np.std(features, axis=0)
            zero_var_idx = np.where(feature_std < 0.01)[0]

            if len(zero_var_idx) > 0:
                logger.warning(
                    f"⚠️  Features {zero_var_idx.tolist()} have near-zero variance "
                    f"(std < 0.01). This may indicate missing data, constant values, "
                    f"or insufficient normalization."
                )

        return features

    # ============= MODEL BUILDING =============

    def build_model(self, use_lr_schedule: bool = True) -> None:
        """Build LSTM neural network architecture with optional learning rate scheduling"""

        logger.info("=" * 60)
        logger.info("Building MSIF-LSTM Model Architecture (v2.0)")
        logger.info("=" * 60)

        self.model = Sequential([
            Input(shape=self.input_shape),

            LSTM(
                config.ML_CONFIG.MSIF_UNITS[0],
                return_sequences=True,
                activation='relu',
                name='msif_lstm_1',
                recurrent_dropout=0.2
            ),
            BatchNormalization(name='msif_bn_1'),
            Dropout(config.ML_CONFIG.DROPOUT_RATE, name='msif_dropout_1'),

            LSTM(
                config.ML_CONFIG.MSIF_UNITS[1],
                return_sequences=False,
                activation='relu',
                name='msif_lstm_2',
                recurrent_dropout=0.2
            ),
            BatchNormalization(name='msif_bn_2'),
            Dropout(config.ML_CONFIG.DROPOUT_RATE, name='msif_dropout_2'),

            Dense(
                config.ML_CONFIG.MSIF_UNITS[2],
                activation='relu',
                name='msif_dense_1'
            ),
            Dropout(config.ML_CONFIG.DROPOUT_RATE, name='msif_dropout_3'),

            Dense(
                config.ML_CONFIG.MSIF_UNITS[3],
                activation='relu',
                name='msif_dense_2'
            ),

            Dense(1, activation='sigmoid', name='msif_output')
        ])

        if use_lr_schedule:
            lr_schedule = PolynomialDecay(
                initial_learning_rate=0.0001,
                decay_steps=1000,
                end_learning_rate=0.001,
                power=1.0
            )
            optimizer = Adam(learning_rate=lr_schedule)
            logger.info("✅ Learning rate schedule: Polynomial decay (0.0001 → 0.001)")
        else:
            optimizer = Adam(learning_rate=config.ML_CONFIG.LEARNING_RATE)
            logger.info(f"✅ Fixed learning rate: {config.ML_CONFIG.LEARNING_RATE}")

        self.model.compile(
            optimizer=optimizer,
            loss='binary_crossentropy',
            metrics=['accuracy', 'AUC', 'Precision', 'Recall']
        )

        total_params = self.model.count_params()
        logger.info(f"✅ MSIF-LSTM model built successfully")
        logger.info(f"   Total parameters: {total_params:,}")
        logger.info(f"   Dropout rate: {config.ML_CONFIG.DROPOUT_RATE}")

        logger.debug("Model summary:")
        self.model.summary(print_fn=lambda x: logger.debug(x))

    # ============= TRAINING =============

    def train(self,
              X_train: np.ndarray,
              y_train: np.ndarray,
              X_val: np.ndarray = None,
              y_val: np.ndarray = None,
              epochs: int = None,
              batch_size: int = None,
              auto_class_weight: bool = True,
              patience: int = None,
              min_delta: float = 0.0001) -> Dict[str, list]:
        """Train MSIF-LSTM on labeled anomaly data with class imbalance handling"""

        if self.model is None:
            logger.warning("Model not built. Building now...")
            self.build_model()

        epochs = epochs or config.ML_CONFIG.EPOCHS
        batch_size = batch_size or config.ML_CONFIG.BATCH_SIZE

        if patience is None:
            patience = 5 if len(X_train) < 10000 else 8

        if X_train.ndim == 2:
            X_train = X_train.reshape((X_train.shape[0], 1, X_train.shape[1]))
            logger.info(f"Reshaped X_train to {X_train.shape}")

        if X_val is not None and X_val.ndim == 2:
            X_val = X_val.reshape((X_val.shape[0], 1, X_val.shape[1]))
            logger.info(f"Reshaped X_val to {X_val.shape}")

        class_weights = None
        if auto_class_weight:
            n_samples = len(y_train)
            n_anomalies = np.sum(y_train)
            n_normal = n_samples - n_anomalies

            if n_anomalies == 0:
                logger.warning("⚠️  No anomalies in training data! Class weighting disabled.")
            else:
                weight_normal = n_samples / (2 * n_normal)
                weight_anomaly = n_samples / (2 * n_anomalies)

                class_weights = {0: float(weight_normal), 1: float(weight_anomaly)}
                self.class_weights = class_weights

                anomaly_rate = n_anomalies / n_samples
                weight_ratio = weight_anomaly / weight_normal

                logger.info("")
                logger.info("=" * 60)
                logger.info("CLASS IMBALANCE ANALYSIS")
                logger.info("=" * 60)
                logger.info(f"Total samples: {n_samples:,}")
                logger.info(f"Normal samples (0): {n_normal:,} ({(1-anomaly_rate):.2%})")
                logger.info(f"Anomaly samples (1): {n_anomalies:,} ({anomaly_rate:.2%})")
                logger.info("")
                logger.info("Class weights (applied during training):")
                logger.info(f"  Normal class (0): {weight_normal:.4f}")
                logger.info(f"  Anomaly class (1): {weight_anomaly:.4f}")
                logger.info(f"  Weight ratio (anomaly/normal): {weight_ratio:.1f}x")
                logger.info("=" * 60)
                logger.info("")

        logger.info("=" * 60)
        logger.info("Starting MSIF-LSTM Training")
        logger.info("=" * 60)
        logger.info(f"Epochs: {epochs}")
        logger.info(f"Batch size: {batch_size}")
        logger.info(f"Early stopping patience: {patience} epochs")
        logger.info(f"Min delta (improvement threshold): {min_delta}")
        logger.info(f"Training samples: {X_train.shape[0]:,}")
        if X_val is not None:
            logger.info(f"Validation samples: {X_val.shape[0]:,}")
        logger.info("")

        # HOTFIX: Only use EarlyStopping (ReduceLROnPlateau incompatible with LearningRateSchedule)
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=patience,
                restore_best_weights=True,
                verbose=1,
                mode='min',
                min_delta=min_delta
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
                class_weight=class_weights,
                verbose=1
            )

            self.training_history = history.history
            self.is_trained = True

            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ MSIF-LSTM Training Completed Successfully")
            logger.info("=" * 60)
            logger.info(f"Final train loss: {history.history['loss'][-1]:.4f}")
            logger.info(f"Final train accuracy: {history.history['accuracy'][-1]:.4f}")
            if validation_data:
                logger.info(f"Final val loss: {history.history['val_loss'][-1]:.4f}")
                logger.info(f"Final val accuracy: {history.history['val_accuracy'][-1]:.4f}")
            logger.info("=" * 60)

            return self.training_history

        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
            raise

    # ============= PREDICTION =============

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Make anomaly predictions on normalized features with validation"""

        if self.model is None:
            raise RuntimeError(
                "Model not built! Call build_model() or load() first."
            )

        features = self._validate_features(features)

        if features.ndim == 2:
            features = features.reshape((features.shape[0], 1, features.shape[1]))

        predictions = self.model.predict(features, verbose=0)

        return predictions.flatten()

    def predict_with_threshold(self,
                               features: np.ndarray,
                               threshold: float = 0.5) -> Dict:
        """Make predictions with custom threshold for imbalanced data"""

        if self.model is None:
            raise RuntimeError("Model not built! Call build_model() or load() first.")

        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be in [0.0, 1.0], got {threshold}")

        features = self._validate_features(features)
        raw_scores = self.predict(features)
        predictions = (raw_scores > threshold).astype(int)
        confidence = np.abs(raw_scores - 0.5) * 2

        return {
            'raw_scores': raw_scores,
            'predictions': predictions,
            'threshold': threshold,
            'confidence': confidence,
            'anomaly_count': int(np.sum(predictions))
        }

    # ============= EVALUATION =============

    def evaluate(self,
                 X_test: np.ndarray,
                 y_test: np.ndarray,
                 threshold: float = 0.5) -> Dict:
        """Comprehensive evaluation with metrics for imbalanced data"""

        if self.model is None:
            raise RuntimeError("Model not built! Call build_model() or load() first.")

        X_test = self._validate_features(X_test)

        if X_test.ndim == 2:
            X_test = X_test.reshape((X_test.shape[0], 1, X_test.shape[1]))

        raw_scores = self.model.predict(X_test, verbose=0).flatten()
        predictions = (raw_scores > threshold).astype(int)

        accuracy = accuracy_score(y_test, predictions)
        precision = precision_score(y_test, predictions, zero_division=0)
        recall = recall_score(y_test, predictions, zero_division=0)
        f1 = f1_score(y_test, predictions, zero_division=0)

        try:
            roc_auc = roc_auc_score(y_test, raw_scores)
        except Exception as e:
            logger.warning(f"ROC-AUC calculation failed: {e}")
            roc_auc = 0.0

        try:
            precision_curve, recall_curve, _ = precision_recall_curve(y_test, raw_scores)
            pr_auc = auc(recall_curve, precision_curve)
        except Exception as e:
            logger.warning(f"PR-AUC calculation failed: {e}")
            pr_auc = 0.0

        try:
            tn, fp, fn, tp = confusion_matrix(y_test, predictions).ravel()
        except Exception as e:
            logger.error(f"Confusion matrix calculation failed: {e}")
            tn = fp = fn = tp = 0

        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

        results = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'roc_auc': float(roc_auc),
            'pr_auc': float(pr_auc),
            'specificity': float(specificity),
            'threshold': threshold,
            'confusion_matrix': {
                'true_negatives': int(tn),
                'false_positives': int(fp),
                'false_negatives': int(fn),
                'true_positives': int(tp)
            }
        }

        logger.info("")
        logger.info("=" * 60)
        logger.info("MSIF-LSTM Evaluation Results")
        logger.info("=" * 60)
        logger.info(f"Threshold: {threshold:.2f}")
        logger.info("")
        logger.info("Classification Metrics:")
        logger.info(f"  Accuracy:    {accuracy:.4f} (overall correctness)")
        logger.info(f"  Precision:   {precision:.4f} (of detected anomalies, how many true)")
        logger.info(f"  Recall:      {recall:.4f} (of actual anomalies, how many detected)")
        logger.info(f"  F1 Score:    {f1:.4f} (balance precision & recall)")
        logger.info(f"  Specificity: {specificity:.4f} (true negative rate)")
        logger.info("")
        logger.info("Threshold-Independent Ranking:")
        logger.info(f"  ROC-AUC:     {roc_auc:.4f} (0.5=random, 1.0=perfect)")
        logger.info(f"  PR-AUC:      {pr_auc:.4f} (best for imbalanced data)")
        logger.info("")
        logger.info("Confusion Matrix:")
        logger.info(f"  TP (detected anomalies):    {tp:,}")
        logger.info(f"  TN (correct normal):        {tn:,}")
        logger.info(f"  FP (false alarms):          {fp:,}")
        logger.info(f"  FN (missed anomalies):      {fn:,}")
        logger.info("=" * 60)
        logger.info("")

        return results

    # ============= PERSISTENCE =============

    def save(self, path: str) -> None:
        """Save trained model weights to disk"""

        if self.model is None:
            raise RuntimeError("No model to save! Train or build model first.")

        os.makedirs(path, exist_ok=True)
        model_path = os.path.join(path, 'msif_lstm_model.h5')

        try:
            self.model.save(model_path)
            logger.info(f"✅ MSIF-LSTM model saved to {model_path}")
            logger.info(f"   Trained: {self.is_trained}")
            if self.class_weights:
                logger.info(f"   Class weights: {self.class_weights}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}", exc_info=True)
            raise

    def load(self, path: str) -> None:
        """Load pre-trained model weights from disk"""

        model_path = os.path.join(path, 'msif_lstm_model.h5')

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                f"Make sure to train and save model first."
            )

        try:
            self.model = load_model(model_path)
            self.is_trained = True
            logger.info(f"✅ MSIF-LSTM model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise
