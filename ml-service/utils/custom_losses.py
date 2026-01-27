
"""Custom loss functions for model loading"""

import tensorflow as tf

from tensorflow import keras



@keras.saving.register_keras_serializable(package="CustomLosses")

class FocalLoss(keras.losses.Loss):

    """Focal Loss for handling class imbalance"""

    def __init__(self, alpha=0.25, gamma=2.0, **kwargs):

        super().__init__(**kwargs)

        self.alpha = alpha

        self.gamma = gamma

    

    def call(self, y_true, y_pred):

        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)

        bce = y_true * tf.math.log(y_pred) + (1 - y_true) * tf.math.log(1 - y_pred)

        p_t = y_true * y_pred + (1 - y_true) * (1 - y_pred)

        focal_weight = (1 - p_t) ** self.gamma

        alpha_weight = y_true * self.alpha + (1 - y_true) * (1 - self.alpha)

        return -tf.reduce_mean(alpha_weight * focal_weight * bce)

    

    def get_config(self):

        config = super().get_config()

        config.update({"alpha": self.alpha, "gamma": self.gamma})

        return config

