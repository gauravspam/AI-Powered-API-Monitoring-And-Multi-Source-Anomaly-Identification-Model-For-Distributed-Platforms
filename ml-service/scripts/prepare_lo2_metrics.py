import pandas as pd
import numpy as np
import logging
from pathlib import Path
from glob import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('lo2-prep')

logger.info("📊 LO2 Microservice Metrics Preparation")
logger.info("=" * 70)

# Step 1: Load all metrics CSV files
logger.info("Step 1: Loading metrics CSV files...")
metrics_files = glob('data/lo2_raw/metrics/*.csv')
logger.info(f"   Found {len(metrics_files)} CSV files")

all_data = []
for i, mf in enumerate(metrics_files[:30]):  # Load first 30 files (~30MB)
    try:
        df = pd.read_csv(mf)
        all_data.append(df)
        if i % 10 == 0:
            logger.info(f"   Loaded {i+1}/{min(30, len(metrics_files))} files...")
    except Exception as e:
        logger.warning(f"   Skipped {mf}: {e}")

df_combined = pd.concat(all_data, ignore_index=True)
logger.info(f"   ✓ Combined {len(df_combined):,} total records")
logger.info(f"   ✓ Columns: {list(df_combined.columns[:15])}")

# Step 2: Parse logs to create anomaly labels
logger.info("\nStep 2: Creating anomaly labels from logs...")
anomaly_keywords = ['400', '500', '503', 'ERROR', 'FAIL', 'EXCEPTION']

# Check if there's a label column
if 'label' in df_combined.columns:
    df_combined['is_anomaly'] = df_combined['label'].apply(lambda x: 1 if x != 'correct' else 0)
    logger.info(f"   ✓ Used 'label' column for anomaly detection")
elif 'scenario' in df_combined.columns:
    df_combined['is_anomaly'] = df_combined['scenario'].apply(
        lambda x: 0 if 'correct' in str(x).lower() else 1
    )
    logger.info(f"   ✓ Used 'scenario' column for anomaly detection")
else:
    # Fallback: use statistical outliers
    numeric_cols = df_combined.select_dtypes(include=[np.number]).columns[:20]
    df_combined['is_anomaly'] = 0
    for col in numeric_cols:
        try:
            z_scores = np.abs((df_combined[col] - df_combined[col].mean()) / df_combined[col].std())
            df_combined.loc[z_scores > 3, 'is_anomaly'] = 1
        except:
            pass
    logger.info(f"   ✓ Used statistical outliers for anomaly detection")

# Step 3: Select numeric features
logger.info("\nStep 3: Selecting features...")
numeric_cols = df_combined.select_dtypes(include=[np.number]).columns
feature_cols = [c for c in numeric_cols if c not in ['is_anomaly', 'timestamp', 'time', 'Unnamed: 0']]
logger.info(f"   ✓ Selected {len(feature_cols)} numeric features")

# Create final dataset
df_final = df_combined[feature_cols + ['is_anomaly']].copy()
df_final = df_final.replace([np.inf, -np.inf], np.nan).dropna()

logger.info(f"\nStep 4: Dataset statistics...")
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
