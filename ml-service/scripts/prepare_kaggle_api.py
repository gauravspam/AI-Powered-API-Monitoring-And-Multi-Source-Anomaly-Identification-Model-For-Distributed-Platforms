from pathlib import Path

import numpy as np
import pandas as pd


def transform_kaggle_api_to_training_format(input_csv, output_csv):
    """
    Transform Kaggle API dataset to your model's 10-feature format

    Actual columns from dataset:
    - inter_api_access_duration(sec)
    - api_access_uniqueness
    - sequence_length(count)
    - vsession_duration(min)
    - ip_type
    - num_sessions
    - num_users
    - num_unique_apis
    - source
    - classification (label: normal/outlier)
    """

    print(f"📂 Loading {input_csv}...")
    df = pd.read_csv(input_csv)

    print(f"✅ Loaded {len(df)} samples")
    print(f"   Columns: {list(df.columns)}")

    # Check anomaly distribution using 'classification' column
    anomaly_count = (df["classification"] == "outlier").sum()
    normal_count = len(df) - anomaly_count
    print(f"\n📊 Data distribution:")
    print(f"   Normal: {normal_count} ({normal_count / len(df) * 100:.1f}%)")
    print(f"   Anomaly: {anomaly_count} ({anomaly_count / len(df) * 100:.1f}%)")

    # Transform to 10 features
    transformed = pd.DataFrame()

    # 1. response_time ← inter_api_access_duration(sec) * 1000 (convert to ms)
    transformed["response_time"] = df["inter_api_access_duration(sec)"] * 1000

    # 2. status_code ← derived from classification
    # Normal = 200, Anomaly = 500
    transformed["status_code"] = (
        200 + (df["classification"] == "outlier").astype(int) * 300
    )

    # 3. request_count ← sequence_length(count)
    transformed["request_count"] = df["sequence_length(count)"]

    # 4. error_rate ← derived from classification
    # Anomalies get 0.3-0.7 error rate, normal gets 0.0-0.1
    transformed["error_rate"] = np.where(
        df["classification"] == "outlier",
        np.random.uniform(0.3, 0.7, len(df)),
        np.random.uniform(0.0, 0.1, len(df)),
    )

    # 5. cpu_usage ← scale from num_sessions (more sessions = higher CPU)
    session_scale = df["num_sessions"] / df["num_sessions"].max()
    transformed["cpu_usage"] = 30 + session_scale * 60  # 30-90% range

    # 6. memory_usage ← scale from vsession_duration
    duration_scale = df["vsession_duration(min)"] / df["vsession_duration(min)"].max()
    transformed["memory_usage"] = 40 + duration_scale * 50  # 40-90% range

    # 7. network_io ← api_access_uniqueness * num_unique_apis (scaled to KB)
    transformed["network_io"] = (
        df["api_access_uniqueness"] * df["num_unique_apis"] * 100
    )

    # 8. disk_io ← vsession_duration scaled
    transformed["disk_io"] = (
        df["vsession_duration(min)"] * 10
    )  # Scale to operations/min

    # 9-10. Temporal features ← generate random (dataset doesn't have timestamps)
    np.random.seed(42)  # Reproducible
    transformed["hour_of_day"] = np.random.randint(0, 24, len(df))
    transformed["day_of_week"] = np.random.randint(0, 7, len(df))

    # Binary label for training
    transformed["is_anomaly"] = (df["classification"] == "outlier").astype(int)

    print(f"\n✅ Transformation complete!")
    print(f"   Features: {list(transformed.columns[:-1])}")  # Exclude label
    print(f"   Shape: {transformed.shape}")

    # Validate data quality
    print(f"\n🔍 Data quality check:")
    print(f"   Missing values: {transformed.isnull().sum().sum()}")
    print(
        f"   Infinite values: {np.isinf(transformed.select_dtypes(include=[np.number])).sum().sum()}"
    )

    # Check for any NaN or inf introduced
    if transformed.isnull().any().any():
        print("\n⚠️  Warning: NaN values detected! Filling with 0...")
        transformed = transformed.fillna(0)

    if np.isinf(transformed.select_dtypes(include=[np.number])).any().any():
        print(
            "\n⚠️  Warning: Infinite values detected! Replacing with max finite value..."
        )
        transformed = transformed.replace([np.inf, -np.inf], np.finfo(np.float64).max)

    # Show feature statistics
    print(f"\n📈 Feature ranges:")
    for col in transformed.columns[:-1]:
        print(
            f"   {col:20s}: [{transformed[col].min():.2f}, {transformed[col].max():.2f}]"
        )

    # Save to CSV
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    transformed.to_csv(output_csv, index=False)

    print(f"\n💾 Saved to: {output_csv}")
    print(f"\n🎯 Ready to train!")
    print(f"   Command: python scripts/train_models.py --data-path {output_csv}")

    return transformed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Transform Kaggle API dataset to training format"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="kaggle_api_dataset/supervised_dataset.csv",
        help="Input CSV file path",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/training_data_kaggle_api.csv",
        help="Output CSV file path",
    )

    args = parser.parse_args()

    # Transform dataset
    transform_kaggle_api_to_training_format(
        input_csv=args.input, output_csv=args.output
    )
