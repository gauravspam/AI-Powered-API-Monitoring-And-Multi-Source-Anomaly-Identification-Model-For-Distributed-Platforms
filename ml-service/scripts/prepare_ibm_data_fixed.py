import pandas as pd
import numpy as np
import logging
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ibm-prep')

logger.info("📊 IBM Cloud Dataset Preparation (FIXED)")
logger.info("=" * 70)

# Step 1: Read ONLY interval_start to get timestamps
logger.info("Step 1: Reading timestamps...")
df_timestamps = pd.read_parquet('data/ibm_cloud_raw/pivoted_data_all.parquet', 
                                 columns=['interval_start'])
logger.info(f"   ✓ Loaded {len(df_timestamps):,} timestamps")

# Convert to datetime and localize to UTC
df_timestamps['interval_start'] = pd.to_datetime(df_timestamps['interval_start'], unit='s')
# Localize to UTC (timestamps are in seconds since epoch, which is UTC)
df_timestamps['interval_start'] = df_timestamps['interval_start'].dt.tz_localize('UTC')

logger.info(f"   ✓ Date range: {df_timestamps['interval_start'].min()} to {df_timestamps['interval_start'].max()}")

# Step 2: Sample columns to find high-variance features (excluding interval_start)
logger.info("\nStep 2: Sampling to select features...")
pq_file = pq.ParquetFile('data/ibm_cloud_raw/pivoted_data_all.parquet')
all_columns = pq_file.schema_arrow.names
feature_columns = [c for c in all_columns if c != 'interval_start']

# Sample first 1000 feature columns
sample_cols = feature_columns[:1000]
logger.info(f"   Sampling {len(sample_cols)} columns...")

df_sample = pd.read_parquet('data/ibm_cloud_raw/pivoted_data_all.parquet',
                            columns=sample_cols)

# Calculate variance and select top features
variances = df_sample.var().sort_values(ascending=False)
top_features = variances.head(20).index.tolist()  # Use 20 features
logger.info(f"   ✓ Selected top 20 features by variance")

# Step 3: Load only selected features
logger.info("\nStep 3: Loading selected features...")
df_features = pd.read_parquet('data/ibm_cloud_raw/pivoted_data_all.parquet',
                              columns=top_features)
logger.info(f"   ✓ Loaded shape: {df_features.shape}")

# Step 4: Combine timestamps and features
logger.info("\nStep 4: Combining data...")
df = pd.concat([df_timestamps, df_features], axis=1)
logger.info(f"   ✓ Combined shape: {df.shape}")

# Step 5: Label anomalies using interval_start
logger.info("\nStep 5: Labeling anomalies...")
anomaly_windows = pd.read_csv('data/ibm_cloud_raw/anomaly_windows.csv')
df['is_anomaly'] = 0

anomaly_count = 0
for _, row in anomaly_windows.iterrows():
    # Parse timestamps with timezone (they have -0500 or -0400)
    start = pd.to_datetime(row['anomaly_start'])
    end = pd.to_datetime(row['anomaly_end'])
    
    # Convert to UTC to match interval_start
    start_utc = start.tz_convert('UTC')
    end_utc = end.tz_convert('UTC')
    
    # Label samples in this window
    mask = (df['interval_start'] >= start_utc) & (df['interval_start'] <= end_utc)
    matched = mask.sum()
    df.loc[mask, 'is_anomaly'] = 1
    anomaly_count += matched
    
    if matched > 0:
        logger.info(f"   ✓ {row['number']}: {matched} samples ({start} to {end})")

logger.info(f"\n   Total anomaly samples labeled: {anomaly_count}")

# Step 6: Drop timestamp column (keep only features + label)
df_final = df.drop(columns=['interval_start'])

# Handle missing values
df_final = df_final.fillna(df_final.mean())

# Step 7: Save
output_path = 'data/training_data_ibm_fixed.csv'
df_final.to_csv(output_path, index=False)

logger.info(f"\n{'='*70}")
logger.info(f"✅ SAVED: {output_path}")
logger.info(f"{'='*70}")
logger.info(f"   Shape: {df_final.shape}")
logger.info(f"   Features: {df_final.shape[1] - 1}")
logger.info(f"   Normal: {(df_final['is_anomaly'] == 0).sum():,} ({(df_final['is_anomaly'] == 0).sum()/len(df_final)*100:.1f}%)")
logger.info(f"   Anomaly: {(df_final['is_anomaly'] == 1).sum():,} ({(df_final['is_anomaly'] == 1).sum()/len(df_final)*100:.1f}%)")
logger.info(f"   Size: {df_final.memory_usage(deep=True).sum() / 1e6:.1f} MB")
logger.info("="*70)
