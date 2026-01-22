import pandas as pd
import numpy as np
import logging
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ibm-prep')

logger.info("📊 IBM Cloud Dataset Preparation (Memory-Efficient)")
logger.info("=" * 70)

# Read parquet metadata first (no loading)
parquet_file = pq.ParquetFile('data/ibm_cloud_raw/pivoted_data_all.parquet')
logger.info(f"Parquet metadata loaded")
logger.info(f"   Rows: {parquet_file.metadata.num_rows:,}")
logger.info(f"   Columns: {parquet_file.metadata.num_columns:,}")

# Strategy: Read column names, select features, then read only those columns
logger.info("\nReading column names...")
schema = parquet_file.schema_arrow
column_names = schema.names

logger.info(f"   Total columns: {len(column_names):,}")

# Read first 1000 rows to calculate variance for feature selection
logger.info("\nSampling 5,000 rows to select features...")
sample_df = pd.read_parquet('data/ibm_cloud_raw/pivoted_data_all.parquet', 
                             engine='pyarrow',
                             columns=column_names[:1000])  # First 1000 columns for speed

variances = sample_df.var().sort_values(ascending=False)
top_features = variances.head(10).index.tolist()  # Use only 10 features to save memory

logger.info(f"   Selected top 10 high-variance features")

# Now read ONLY selected columns (much smaller memory footprint)
logger.info("\nLoading selected features from parquet...")
ibm_data = pd.read_parquet('data/ibm_cloud_raw/pivoted_data_all.parquet',
                           columns=top_features,
                           engine='pyarrow')

logger.info(f"   ✓ Loaded shape: {ibm_data.shape}")

# Load anomaly labels
anomaly_windows = pd.read_csv('data/ibm_cloud_raw/anomaly_windows.csv')
logger.info(f"   ✓ Anomaly windows: {len(anomaly_windows)}")

# Create labels
ibm_data['is_anomaly'] = 0

# Convert timestamps
if not isinstance(ibm_data.index, pd.DatetimeIndex):
    try:
        ibm_data.index = pd.to_datetime(ibm_data.index)
    except:
        logger.warning("Could not parse timestamps, using row numbers")

for _, row in anomaly_windows.iterrows():
    try:
        start = pd.to_datetime(row['start_time'])
        end = pd.to_datetime(row['end_time'])
        mask = (ibm_data.index >= start) & (ibm_data.index <= end)
        ibm_data.loc[mask, 'is_anomaly'] = 1
    except Exception as e:
        logger.warning(f"Skipping anomaly window: {e}")

# Fill NaN
ibm_data = ibm_data.fillna(ibm_data.mean())

# Save
output_path = 'data/training_data_ibm.csv'
ibm_data.to_csv(output_path)

logger.info(f"\n✅ Saved to {output_path}")
logger.info(f"   Shape: {ibm_data.shape}")
logger.info(f"   Normal: {(ibm_data['is_anomaly'] == 0).sum():,}")
logger.info(f"   Anomaly: {(ibm_data['is_anomaly'] == 1).sum()}")
logger.info(f"   Size: {ibm_data.memory_usage(deep=True).sum() / 1e6:.1f} MB")
