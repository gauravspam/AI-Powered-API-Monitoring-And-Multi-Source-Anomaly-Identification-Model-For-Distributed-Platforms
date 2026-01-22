"""
PLE-GRU Model: Parametric Long Short-Term Memory GRU
Production-ready implementation (v2.0 - FIXED)

HOTFIX APPLIED: Removed ReduceLROnPlateau (incompatible with LearningRateSchedule)

Key fix: When using PolynomialDecay LearningRateSchedule, do NOT use ReduceLROnPlateau
because it tries to modify learning_rate directly, which is not allowed.

Solution: Use only EarlyStopping callback with LR schedule
"""

import os
from typing import Dict

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
from tensorflow.keras.layers import GRU, BatchNormalization, Dense, Dropout, Input
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.optimizers.schedules import PolynomialDecay


class PLEGRU:
    """Parametric Long Short-Term Memory GRU Model (v2.0 - Refined)"""

    def __init__(self, input_shape: tuple = (1, 10)):
        self.input_shape = input_shape
        self.model = None
        self.is_trained = False
        self.training_history = None
        self.class_weights = None
        logger.info(f"PLEGRU v2.0 initialized with input shape {input_shape}")

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
            raise ValueError(f"Expected 1D, 2D, or 3D array, got {features.ndim}D. Shape: {features.shape}")

        if features.ndim == 3 and features.shape[1] == 1:
            features = features.reshape((features.shape[0], features.shape[2]))

        if features.shape[-1] != 10:
            raise ValueError(f"Expected 10 features, got {features.shape[-1]}. Shape: {features.shape}.")

        if np.any(np.isnan(features)):
            raise ValueError(f"Input contains {np.sum(np.isnan(features))} NaN values.")

        if np.any(np.isinf(features)):
            raise ValueError(f"Input contains {np.sum(np.isinf(features))} Inf values.")

        max_abs_value = np.max(np.abs(features))
        if max_abs_value > 5.0:
            logger.warning(f"⚠️  Input max value {max_abs_value:.2f} outside [-1,1] range.")

        if features.ndim > 1:
            feature_std = np.std(features, axis=0)
            zero_var_idx = np.where(feature_std < 0.01)[0]
            if len(zero_var_idx) > 0:
                logger.warning(f"⚠️  Features {zero_var_idx.tolist()} have near-zero variance.")

        return features

    def build_model(self, use_lr_schedule: bool = True) -> None:
        """Build GRU neural network architecture"""

        logger.info("=" * 60)
        logger.info("Building PLE-GRU Model Architecture (v2.0)")
        logger.info("=" * 60)

        self.model = Sequential([
            Input(shape=self.input_shape),

            GRU(
                config.ML_CONFIG.PLE_UNITS[0],
                return_sequences=True,
                activation='relu',
                name='ple_gru_1',
                recurrent_dropout=0.2
            ),
            BatchNormalization(name='ple_bn_1'),
            Dropout(config.ML_CONFIG.DROPOUT_RATE, name='ple_dropout_1'),

            GRU(
                config.ML_CONFIG.PLE_UNITS[1],
                return_sequences=False,
                activation='relu',
                name='ple_gru_2',
                recurrent_dropout=0.2
            ),
            BatchNormalization(name='ple_bn_2'),
            Dropout(config.ML_CONFIG.DROPOUT_RATE, name='ple_dropout_2'),

            Dense(config.ML_CONFIG.PLE_UNITS[2], activation='relu', name='ple_dense_1'),
            Dropout(config.ML_CONFIG.DROPOUT_RATE, name='ple_dropout_3'),

            Dense(config.ML_CONFIG.PLE_UNITS[3], activation='relu', name='ple_dense_2'),

            Dense(1, activation='sigmoid', name='ple_output')
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
        logger.info(f"✅ PLE-GRU model built successfully")
        logger.info(f"   Total parameters: {total_params:,}")
        logger.info(f"   Dropout rate: {config.ML_CONFIG.DROPOUT_RATE}")

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
        """Train PLE-GRU with class imbalance handling"""

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

            if n_anomalies > 0:
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
        logger.info("Starting PLE-GRU Training")
        logger.info("=" * 60)
        logger.info(f"Epochs: {epochs}")
        logger.info(f"Batch size: {batch_size}")
        logger.info(f"Early stopping patience: {patience} epochs")
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
            logger.info("✅ PLE-GRU Training Completed Successfully")
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

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Make anomaly predictions on normalized features"""

        if self.model is None:
            raise RuntimeError("Model not built! Call build_model() or load() first.")

        features = self._validate_features(features)

        if features.ndim == 2:
            features = features.reshape((features.shape[0], 1, features.shape[1]))

        predictions = self.model.predict(features, verbose=0)
        return predictions.flatten()

    def predict_with_threshold(self, features: np.ndarray, threshold: float = 0.5) -> Dict:
        """Make predictions with custom threshold"""

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

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray, threshold: float = 0.5) -> Dict:
        """Comprehensive evaluation with metrics"""

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
        except:
            roc_auc = 0.0

        try:
            precision_curve, recall_curve, _ = precision_recall_curve(y_test, raw_scores)
            pr_auc = auc(recall_curve, precision_curve)
        except:
            pr_auc = 0.0

        try:
            tn, fp, fn, tp = confusion_matrix(y_test, predictions).ravel()
        except:
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

        logger.info("=" * 60)
        logger.info("PLE-GRU Evaluation Results")
        logger.info("=" * 60)
        logger.info(f"Threshold: {threshold:.2f}")
        logger.info(f"  Accuracy:    {accuracy:.4f}")
        logger.info(f"  Precision:   {precision:.4f}")
        logger.info(f"  Recall:      {recall:.4f}")
        logger.info(f"  F1 Score:    {f1:.4f}")
        logger.info(f"  ROC-AUC:     {roc_auc:.4f}")
        logger.info(f"  PR-AUC:      {pr_auc:.4f}")
        logger.info(f"  Specificity: {specificity:.4f}")
        logger.info(f"  TP/FP/FN/TN: {tp}/{fp}/{fn}/{tn}")
        logger.info("=" * 60)

        return results

    def save(self, path: str) -> None:
        """Save trained model"""

        if self.model is None:
            raise RuntimeError("No model to save!")

        os.makedirs(path, exist_ok=True)
        model_path = os.path.join(path, 'ple_gru_model.h5')

        try:
            self.model.save(model_path)
            logger.info(f"✅ PLE-GRU model saved to {model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}", exc_info=True)
            raise

    def load(self, path: str) -> None:
        """Load pre-trained model"""

        model_path = os.path.join(path, 'ple_gru_model.h5')

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")

        try:
            self.model = load_model(model_path)
            self.is_trained = True
            logger.info(f"✅ PLE-GRU model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise
