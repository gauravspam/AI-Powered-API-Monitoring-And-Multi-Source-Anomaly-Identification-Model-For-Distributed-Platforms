import pandas as pd
import numpy as np
import logging
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ibm-prep')

logger.info("📊 IBM Cloud Dataset Preparation (IMPROVED)")
logger.info("=" * 70)

# Step 1: Read timestamps
logger.info("Step 1: Reading timestamps...")
df_timestamps = pd.read_parquet('data/ibm_cloud_raw/pivoted_data_all.parquet', 
                                 columns=['interval_start'])
df_timestamps['interval_start'] = pd.to_datetime(df_timestamps['interval_start'], unit='s')
df_timestamps['interval_start'] = df_timestamps['interval_start'].dt.tz_localize('UTC')
logger.info(f"   ✓ Date range: {df_timestamps['interval_start'].min()} to {df_timestamps['interval_start'].max()}")

# Step 2: Sample MORE columns for better feature selection
logger.info("\nStep 2: Sampling to select features...")
pq_file = pq.ParquetFile('data/ibm_cloud_raw/pivoted_data_all.parquet')
all_columns = pq_file.schema_arrow.names
feature_columns = [c for c in all_columns if c != 'interval_start']

# Sample 5000 columns (instead of 1000)
sample_cols = feature_columns[:5000]
logger.info(f"   Sampling {len(sample_cols)} columns...")

df_sample = pd.read_parquet('data/ibm_cloud_raw/pivoted_data_all.parquet',
                            columns=sample_cols)

# Select top 50 features by variance (instead of 20)
variances = df_sample.var().sort_values(ascending=False)
top_features = variances.head(50).index.tolist()
logger.info(f"   ✓ Selected top 50 features by variance")

# Also select features with 'response_time', 'error', 'request' in name (if available)
important_keywords = ['response', 'error', 'request', 'latency', 'count']
keyword_features = [c for c in sample_cols if any(kw in c.lower() for kw in important_keywords)][:20]
logger.info(f"   ✓ Added {len(keyword_features)} keyword-based features")

# Combine and deduplicate
all_selected = list(set(top_features + keyword_features))[:60]  # Max 60 features
logger.info(f"   ✓ Total features selected: {len(all_selected)}")

# Step 3: Load selected features
logger.info("\nStep 3: Loading selected features...")
df_features = pd.read_parquet('data/ibm_cloud_raw/pivoted_data_all.parquet',
                              columns=all_selected)
logger.info(f"   ✓ Loaded shape: {df_features.shape}")

# Step 4: Combine
logger.info("\nStep 4: Combining data...")
df = pd.concat([df_timestamps, df_features], axis=1)
logger.info(f"   ✓ Combined shape: {df.shape}")

# Step 5: Label anomalies
logger.info("\nStep 5: Labeling anomalies...")
anomaly_windows = pd.read_csv('data/ibm_cloud_raw/anomaly_windows.csv')
df['is_anomaly'] = 0

anomaly_count = 0
for _, row in anomaly_windows.iterrows():
    start = pd.to_datetime(row['anomaly_start']).tz_convert('UTC')
    end = pd.to_datetime(row['anomaly_end']).tz_convert('UTC')
    mask = (df['interval_start'] >= start) & (df['interval_start'] <= end)
    matched = mask.sum()
    df.loc[mask, 'is_anomaly'] = 1
    anomaly_count += matched
    if matched > 0:
        logger.info(f"   ✓ {row['number']}: {matched} samples")

logger.info(f"\n   Total anomaly samples: {anomaly_count}")

# Step 6: Drop timestamp
df_final = df.drop(columns=['interval_start'])

# Handle missing values
df_final = df_final.fillna(df_final.mean())

# Step 7: Save
output_path = 'data/training_data_ibm_improved.csv'
df_final.to_csv(output_path, index=False)

logger.info(f"\n{'='*70}")
logger.info(f"✅ SAVED: {output_path}")
logger.info(f"{'='*70}")
logger.info(f"   Shape: {df_final.shape}")
logger.info(f"   Features: {df_final.shape[1] - 1}")
logger.info(f"   Normal: {(df_final['is_anomaly'] == 0).sum():,} ({(df_final['is_anomaly'] == 0).sum()/len(df_final)*100:.1f}%)")
logger.info(f"   Anomaly: {(df_final['is_anomaly'] == 1).sum():,} ({(df_final['is_anomaly'] == 1).sum()/len(df_final)*100:.1f}%)")
logger.info("="*70)
