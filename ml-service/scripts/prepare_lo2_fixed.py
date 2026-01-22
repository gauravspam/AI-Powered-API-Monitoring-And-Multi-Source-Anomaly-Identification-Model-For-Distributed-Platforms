import pandas as pd
import numpy as np
import logging
from glob import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('lo2-prep')

logger.info("📊 LO2 OAuth2 Microservice Dataset Preparation")
logger.info("=" * 70)

# Load all metrics CSV files
logger.info("Step 1: Loading metrics CSV files...")
metrics_files = glob('data/lo2_raw/metrics/*.csv')
logger.info(f"   Found {len(metrics_files)} CSV files")

all_data = []
for i, mf in enumerate(metrics_files[:50]):  # Load first 50 files
    try:
        df = pd.read_csv(mf, low_memory=False)
        all_data.append(df)
        if (i+1) % 10 == 0:
            logger.info(f"   Loaded {i+1} files...")
    except Exception as e:
        logger.warning(f"   Skipped {mf}: {e}")

df_combined = pd.concat(all_data, ignore_index=True)
logger.info(f"   ✓ Combined {len(df_combined):,} records")

# Step 2: Create anomaly labels from test_name
logger.info("\nStep 2: Creating anomaly labels...")
df_combined['is_anomaly'] = df_combined['test_name'].apply(
    lambda x: 0 if 'correct' in str(x).lower() else 1
)

logger.info(f"   ✓ Labeled using test_name column")
logger.info(f"   Normal (correct): {(df_combined['is_anomaly']==0).sum():,}")
logger.info(f"   Anomaly (errors): {(df_combined['is_anomaly']==1).sum():,}")

# Step 3: Select relevant features
logger.info("\nStep 3: Selecting features...")

# Focus on key metric categories
feature_patterns = [
    # Application metrics
    'go_goroutines', 'go_memstats', 'go_gc_duration',
    # System metrics  
    'node_cpu_seconds_total', 'node_memory', 'node_disk', 'node_network',
    'node_load', 'process_cpu', 'process_resident_memory'
]

# Select columns matching patterns
feature_cols = []
for col in df_combined.columns:
    if any(pattern in col for pattern in feature_patterns) and col not in ['is_anomaly', 'test_name']:
        feature_cols.append(col)

# Limit to 100 most important features (randomly sampled for now)
feature_cols = feature_cols[:100]
logger.info(f"   ✓ Selected {len(feature_cols)} features")

# Create final dataset
df_final = df_combined[feature_cols + ['is_anomaly']].copy()

# Drop non-numeric columns
df_final = df_final.select_dtypes(include=[np.number])

# Handle inf and NaN
df_final = df_final.replace([np.inf, -np.inf], np.nan)
df_final = df_final.fillna(df_final.mean())  # Fill NaN with mean instead of dropping
df_final = df_final.dropna()  # Drop remaining NaN rows

logger.info(f"\nStep 4: Final dataset statistics...")
logger.info(f"   Shape: {df_final.shape}")
logger.info(f"   Normal: {(df_final['is_anomaly'] == 0).sum():,} ({(df_final['is_anomaly'] == 0).sum()/len(df_final)*100:.1f}%)")
logger.info(f"   Anomaly: {(df_final['is_anomaly'] == 1).sum():,} ({(df_final['is_anomaly'] == 1).sum()/len(df_final)*100:.1f}%)")

# Save
output_path = 'data/training_data_lo2.csv'
df_final.to_csv(output_path, index=False)

logger.info(f"\n{'='*70}")
logger.info(f"✅ SAVED: {output_path}")
logger.info(f"{'='*70}")
logger.info(f"   Features: {df_final.shape[1] - 1}")
logger.info(f"   Samples: {len(df_final):,}")
logger.info(f"   Size: {df_final.memory_usage(deep=True).sum() / 1e6:.1f} MB")
logger.info("="*70)
