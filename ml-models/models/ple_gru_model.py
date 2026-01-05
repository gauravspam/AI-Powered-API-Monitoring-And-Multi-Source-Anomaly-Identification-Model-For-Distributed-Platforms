import numpy as np
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import GRU, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam

class PLEGRU:
    def __init__(self):
        self.model = None
        self.build_model()
    
    def build_model(self):
        self.model = Sequential([
            Input(shape=(1, 10)),
            GRU(128, activation='relu', return_sequences=True),
            Dropout(0.2),
            GRU(64, activation='relu'),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(16, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', 'AUC']
        )
    
    def predict(self, features):
        features_reshaped = features.reshape((features.shape[0], 1, 10))
        predictions = self.model.predict(features_reshaped, verbose=0)
        return predictions.flatten()
    
    def load(self, path):
        self.model = load_model(f'{path}/ple_gru_model.h5')
