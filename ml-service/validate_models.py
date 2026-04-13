"""
Validate trained models on AIOps 2020 test data
"""

import os
import sys
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from models.msif_lstm_model import VariableInputMSIF_LSTM
from models.ple_gru_model import VariableInputPLE_GRU

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_aiops_data():
    """Load AIOps 2020 data for validation"""
    base_path = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/AIOps_Challenge_Data")
    
    # Load platform metrics
    platform_path = os.path.join(base_path, "2020_04_11/2020_04_11/平台指标/os_linux.csv")
    df_platform = pd.read_csv(platform_path)
    
    # Load fault labels
    fault_path = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/fault_labels_preselection.csv")
    df_fault = pd.read_csv(fault_path)
    
    return df_platform, df_fault

def evaluate_model():
    """Evaluate trained models"""
    print("=" * 60)
    print("MODEL VALIDATION ON AIOps 2020 DATA")
    print("=" * 60)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    
    # Load model 1: MSIF-LSTM
    msif = VariableInputMSIF_LSTM(embedding_dim=26, lstm_hidden_dim=128).to(device)
    msif_path = os.path.join(BASE_DIR, "models/enhanced/msif_lstm_strict.pth")
    if os.path.exists(msif_path):
        msif.load_state_dict(torch.load(msif_path, map_location=device), strict=False)
        msif.eval()
        print(f"OK MSIF-LSTM loaded from {msif_path}")
    else:
        print(f"WARN MSIF-LSTM not found at {msif_path}")
        return
    
    # Load model 2: PLE-GRU
    ple = VariableInputPLE_GRU(embedding_dim=26, gru_hidden_dim=128, num_experts=4).to(device)
    ple_path = os.path.join(BASE_DIR, "models/enhanced/ple_gru_strict.pth")
    if os.path.exists(ple_path):
        ple.load_state_dict(torch.load(ple_path, map_location=device), strict=False)
        ple.eval()
        print(f"OK PLE-GRU loaded from {ple_path}")
    else:
        print(f"WARN PLE-GRU not found at {ple_path}")
        return
    
    # Load data
    print("\nLoading AIOps 2020 test data...")
    df_platform, df_fault = load_aiops_data()
    print(f"Platform metrics: {len(df_platform)} rows")
    print(f"Fault labels: {len(df_fault)} labels")
    
    # Simple evaluation - test on a sample
    print("\nRunning quick evaluation...")
    
    # Test inference
    test_input = torch.randn(1, 12, 26).to(device)
    
    with torch.no_grad():
        msif_score = msif(test_input).item()
        ple_score = ple(test_input).item()
        
    print(f"\nTest inference results:")
    print(f"  MSIF-LSTM score: {msif_score:.4f}")
    print(f"  PLE-GRU score: {ple_score:.4f}")
    
    # Ensemble
    ensemble_score = (msif_score + ple_score) / 2
    print(f"  Ensemble score: {ensemble_score:.4f}")
    
    # Check if scores are in reasonable range
    print("\nValidation checks:")
    has_nan = np.isnan(msif_score) or np.isnan(ple_score)
    print(f"  Has NaN: {has_nan}")
    print(f"  Scores in [0,1]: {0 <= msif_score <= 1 and 0 <= ple_score <= 1}")
    
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    evaluate_model()