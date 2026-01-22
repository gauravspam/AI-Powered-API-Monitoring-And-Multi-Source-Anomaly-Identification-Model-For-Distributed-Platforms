import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ibm-prep')

logger.info("📊 IBM Cloud Dataset Preparation")
logger.info("=" * 70)

# Load parquet (large file, may take 1-2 min)
logger.info("Loading pivoted_data_all.parquet...")
ibm_data = pd.read_parquet('data/ibm_cloud_raw/pivoted_data_all.parquet')
logger.info(f"✓ Shape: {ibm_data.shape}")

# Load anomaly labels
anomaly_windows = pd.read_csv('data/ibm_cloud_raw/anomaly_windows.csv')
logger.info(f"✓ Anomaly windows: {len(anomaly_windows)}")

# Select top 100 features by variance (117K is too many)
logger.info("\nSelecting top 100 features by variance...")
variances = ibm_data.var().sort_values(ascending=False)
top_features = variances.head(100).index.tolist()

training_data = ibm_data[top_features].copy()

# Create binary anomaly labels
training_data['is_anomaly'] = 0
ibm_data.index = pd.to_datetime(ibm_data.index)

for _, row in anomaly_windows.iterrows():
    start = pd.to_datetime(row['start_time'])
    end = pd.to_datetime(row['end_time'])
    mask = (training_data.index >= start) & (training_data.index <= end)
    training_data.loc[mask, 'is_anomaly'] = 1

# Handle missing values
training_data = training_data.fillna(training_data.mean())

# Save CSV for training
output_path = 'data/training_data_ibm_full.csv'
training_data.to_csv(output_path)

logger.info(f"\n✅ Saved to {output_path}")
logger.info(f"   Shape: {training_data.shape}")
logger.info(f"   Normal: {(training_data['is_anomaly'] == 0).sum():,}")
logger.info(f"   Anomaly: {(training_data['is_anomaly'] == 1).sum()}")
logger.info(f"   Anomaly %: {(training_data['is_anomaly'] == 1).sum() / len(training_data) * 100:.2f}%")
