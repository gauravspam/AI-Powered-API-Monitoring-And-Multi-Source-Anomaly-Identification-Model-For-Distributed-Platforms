import numpy as np
from models.msif_lstm_model import MSIFLSTM
from models.ple_gru_model import PLEGRU
import os
# In train_models.py - replace create_synthetic_data()
def load_realistic_data():
    import json
    with open('synthetic_logs.json', 'r') as f:
        logs = json.load(f)
    
    X = []
    y = []
    
    for log in logs:
        features = np.array([
            log['response_time'], log['status_code'], log['request_count'],
            log['error_rate'], log['cpu_usage'], log['memory_usage'],
            log['network_io'], log['disk_io'], log['hour_of_day'], log['day_of_week']
        ])
        X.append(features)
        
        # Label based on response_time + error_rate (simple heuristic)
        if log['response_time'] > 2000 or log['error_rate'] > 0.3:
            y.append(1)  # Anomaly
        else:
            y.append(0)  # Normal
    
    return np.array(X), np.array(y)


def train_models():
    print("Loading realistic synthetic data...")
    X, y = load_realistic_data()
    
    print("X shape:", X.shape, "y shape:", y.shape)
    
    os.makedirs("models/saved", exist_ok=True)
    
    print("\nTraining MSIF-LSTM Model...")
    msif_lstm = MSIFLSTM(input_shape=10)
    msif_lstm.train(X, y, epochs=25, batch_size=32)
    msif_lstm.save("models/saved")
    print("MSIF-LSTM saved!")
    
    print("\nTraining PLE-GRU Model...")
    ple_gru = PLEGRU(input_shape=10)
    ple_gru.train(X, y, epochs=25, batch_size=32)
    ple_gru.save("models/saved")
    print("PLE-GRU saved!")
    
    print("\nAll models trained and saved!")

if __name__ == "__main__":
    train_models()
