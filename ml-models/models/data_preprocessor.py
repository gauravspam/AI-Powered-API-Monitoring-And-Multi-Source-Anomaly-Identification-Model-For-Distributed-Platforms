import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import json

class DataPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = [
            'response_time', 'status_code', 'request_count',
            'error_rate', 'cpu_usage', 'memory_usage',
            'network_io', 'disk_io', 'hour_of_day', 'day_of_week'
        ]
    
    def extract_features(self, log_entry):
        features = []
        
        for feature in self.feature_names:
            value = log_entry.get(feature, 0)
            features.append(float(value))
        
        return np.array(features)
    
    def normalize_features(self, features):
        return self.scaler.transform([features])[0]
    
    def preprocess_batch(self, log_entries):
        features_list = []
        
        for log_entry in log_entries:
            features = self.extract_features(log_entry)
            normalized = self.normalize_features(features)
            features_list.append(normalized)
        
        return np.array(features_list)
