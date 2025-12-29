import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GRU, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam

class PLEGRU:
    def __init__(self, input_shape=(10,)):
        self.model = None
        self.input_shape = input_shape
        self.build_model()
    
    def build_model(self):
        self.model = Sequential([
            Input(shape=(1, self.input_shape)),
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
    
    def train(self, X_train, y_train, epochs=30, batch_size=32):
        X_reshaped = X_train.reshape((X_train.shape[0], 1, X_train.shape[1]))
        
        history = self.model.fit(
            X_reshaped, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1
        )
        return history
    
    def predict(self, features):
        features_reshaped = features.reshape((features.shape[0], 1, features.shape[1]))
        predictions = self.model.predict(features_reshaped, verbose=0)
        return predictions.flatten()
    
    def save(self, path):
        self.model.save(f'{path}/ple_gru_model.h5')
    
    def load(self, path):
        from tensorflow.keras.models import load_model
        self.model = load_model(f'{path}/ple_gru_model.h5')
