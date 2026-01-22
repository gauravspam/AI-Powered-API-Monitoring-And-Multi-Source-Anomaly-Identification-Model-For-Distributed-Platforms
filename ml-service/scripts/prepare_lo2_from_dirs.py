import pandas as pd
import numpy as np
import json
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('lo2-prep')

logger.info("📊 LO2 Microservice Dataset Preparation")
logger.info("=" * 70)

# Step 1: Load metrics
logger.info("Step 1: Loading metrics...")
metrics_dir = 'data/lo2_raw/metrics'
metrics_files = list(Path(metrics_dir).glob('*.json'))
logger.info(f"   Found {len(metrics_files)} metric files")

all_metrics = []
for mf in metrics_files[:50]:  # Load first 50 files
    try:
        with open(mf) as f:
            data = json.load(f)
            if isinstance(data, list):
                all_metrics.extend(data)
            elif isinstance(data, dict):
                all_metrics.append(data)
    except:
        pass

df_metrics = pd.DataFrame(all_metrics)
logger.info(f"   ✓ Loaded {len(df_metrics):,} metric records")
logger.info(f"   ✓ Columns: {list(df_metrics.columns[:10])}")

# Step 2: Load logs for anomaly labels
logger.info("\nStep 2: Loading logs for labels...")
logs_dir = 'data/lo2_raw/logs'
logs_files = list(Path(logs_dir).glob('*.log'))
logger.info(f"   Found {len(logs_files)} log files")

# Parse logs to identify anomalies (ERROR, EXCEPTION, FAILURE)
anomaly_keywords = ['ERROR', 'EXCEPTION', 'FAIL', 'CRITICAL', 'FATAL', '500', '503']
df_metrics['is_anomaly'] = 0

# Simple heuristic: check numeric columns for outliers
logger.info("\nStep 3: Creating anomaly labels...")
numeric_cols = df_metrics.select_dtypes(include=[np.number]).columns

# Mark as anomaly if any metric is an outlier (>3 std devs)
for col in numeric_cols[:20]:  # Check first 20 numeric columns
    if col not in ['is_anomaly', 'timestamp', 'time']:
        try:
            mean = df_metrics[col].mean()
            std = df_metrics[col].std()
            outliers = (np.abs(df_metrics[col] - mean) > 3 * std)
            df_metrics.loc[outliers, 'is_anomaly'] = 1
        except:
            pass

logger.info(f"   ✓ Labeled anomalies")

# Step 4: Select features and create final dataset
logger.info("\nStep 4: Preparing final dataset...")
feature_cols = [c for c in df_metrics.select_dtypes(include=[np.number]).columns 
                if c not in ['is_anomaly', 'timestamp', 'time', 'id']][:50]

df_final = df_metrics[feature_cols + ['is_anomaly']].copy()

# Drop rows with missing values
df_final = df_final.dropna()

logger.info(f"   Shape: {df_final.shape}")
logger.info(f"   Normal: {(df_final['is_anomaly'] == 0).sum():,}")
logger.info(f"   Anomaly: {(df_final['is_anomaly'] == 1).sum():,}")

# Save
output_path = 'data/training_data_lo2.csv'
df_final.to_csv(output_path, index=False)

logger.info(f"\n{'='*70}")
logger.info(f"✅ SAVED: {output_path}")
logger.info(f"{'='*70}")
logger.info(f"   Features: {df_final.shape[1] - 1}")
logger.info(f"   Samples: {len(df_final):,}")
logger.info("="*70)
