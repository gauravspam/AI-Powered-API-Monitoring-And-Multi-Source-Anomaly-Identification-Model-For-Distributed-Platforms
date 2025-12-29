import numpy as np
from models.msif_lstm_model import MSIFLSTM
from models.ple_gru_model import PLEGRU
from models.data_preprocessor import DataPreprocessor

class AnomalyDetectionEngine:
    def __init__(self):
        self.msif_lstm = MSIFLSTM()
        self.ple_gru = PLEGRU()
        self.preprocessor = DataPreprocessor()
        
        try:
            self.msif_lstm.load('models/saved')
            self.ple_gru.load('models/saved')
            print("Models loaded successfully")
        except:
            print("Models not found. Train them first.")
    
    def detect_anomaly(self, log_entry):
        features = self.preprocessor.extract_features(log_entry)
        normalized_features = self.preprocessor.normalize_features(features)
        
        stage1_score = self.msif_lstm.predict(np.array([normalized_features]))[0]
        
        result = {
            'stage': 1,
            'model': 'MSIF-LSTM',
            'anomaly_score': float(stage1_score),
            'confidence': float(abs(0.5 - stage1_score)) * 2
        }
        
        if 0.3 < stage1_score < 0.7:
            stage2_score = self.ple_gru.predict(np.array([normalized_features]))[0]
            
            result['stage'] = 2
            result['stage2_model'] = 'PLE-GRU'
            result['stage2_score'] = float(stage2_score)
            
            final_score = (stage1_score + stage2_score) / 2
            result['final_anomaly_score'] = float(final_score)
        else:
            result['final_anomaly_score'] = float(stage1_score)
        
        final_score = result.get('final_anomaly_score', stage1_score)
        
        if final_score > 0.7:
            result['status'] = 'ANOMALY_DETECTED'
            result['severity'] = 'HIGH' if final_score > 0.85 else 'MEDIUM'
        elif final_score > 0.5:
            result['status'] = 'SUSPICIOUS'
            result['severity'] = 'LOW'
        else:
            result['status'] = 'NORMAL'
            result['severity'] = 'INFO'
        
        return result
    
    def batch_detect(self, log_entries):
        results = []
        for log_entry in log_entries:
            result = self.detect_anomaly(log_entry)
            results.append(result)
        return results
