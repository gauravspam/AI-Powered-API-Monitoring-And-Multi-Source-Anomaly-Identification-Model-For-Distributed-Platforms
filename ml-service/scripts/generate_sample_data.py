"""
Generate Synthetic Training Data for Anomaly Detection

Creates realistic synthetic data with:
- Normal operation patterns (95% of data)
- Anomalies (5% of data) - high latency, errors, resource spikes
- Temporal patterns - hour_of_day variations
- Feature correlations

Output:
    data/training_data.csv - CSV with 10,000 samples and is_anomaly lab els

Usage:
    python scripts/generate_sample_data.py \
        --samples 10000 \
        --anomaly-ratio 0.05 \
        --output data/training_data.csv \
        --seed 42
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

# add project root (ml-service) to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from src.logger import logger


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate Synthetic Anomaly Detection Data'
    )

    parser.add_argument(
        '--samples',
        type=int,
        default=10000,
        help='Number of samples to generate (default: 10000)'
    )

    parser.add_argument(
        '--anomaly-ratio',
        type=float,
        default=0.05,
        help='Ratio of anomalies (default: 0.05 = 5%)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='data/training_data.csv',
        help='Output CSV path (default: data/training_data.csv)'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    return parser.parse_args()


def generate_normal_data(n_samples: int,
                        seed: int) -> np.ndarray:
    """
    Generate normal operational data

    Args:
        n_samples: Number of samples
        seed: Random seed

    Returns:
        Data array of shape (n_samples, 10)
    """

    np.random.seed(seed)

    data = np.zeros((n_samples, 10), dtype=np.float32)

    # Feature 0: response_time (normal: 50-500ms, mean ~200ms)
    data[:, 0] = np.random.gamma(shape=5, scale=40, size=n_samples)
    data[:, 0] = np.clip(data[:, 0], 0, 10000)

    # Feature 1: status_code (normal: 200, occasionally 201, 204, 3xx, 4xx)
    # Mostly 200, some 2xx, rare 4xx
    codes = np.random.choice([200, 201, 204, 301, 302, 400, 404, 500],
                            size=n_samples,
                            p=[0.85, 0.05, 0.02, 0.02, 0.02, 0.02, 0.01, 0.01])
    data[:, 1] = codes

    # Feature 2: request_count (normal: 50-200 req/min, mean ~100)
    data[:, 2] = np.random.normal(loc=100, scale=30, size=n_samples)
    data[:, 2] = np.clip(data[:, 2], 0, 100000)

    # Feature 3: error_rate (normal: 0-5%, mean ~1%)
    data[:, 3] = np.random.beta(a=1, b=100, size=n_samples)
    data[:, 3] = np.clip(data[:, 3], 0, 1)

    # Feature 4: cpu_usage (normal: 20-60%, mean ~40%)
    data[:, 4] = np.random.normal(loc=40, scale=15, size=n_samples)
    data[:, 4] = np.clip(data[:, 4], 0, 100)

    # Feature 5: memory_usage (normal: 30-70%, mean ~50%)
    data[:, 5] = np.random.normal(loc=50, scale=15, size=n_samples)
    data[:, 5] = np.clip(data[:, 5], 0, 100)

    # Feature 6: network_io (normal: 100-500 MB/s, mean ~250)
    data[:, 6] = np.random.normal(loc=250, scale=100, size=n_samples)
    data[:, 6] = np.clip(data[:, 6], 0, 10000)

    # Feature 7: disk_io (normal: 50-300 MB/s, mean ~150)
    data[:, 7] = np.random.normal(loc=150, scale=80, size=n_samples)
    data[:, 7] = np.clip(data[:, 7], 0, 10000)

    # Feature 8: hour_of_day (uniform 0-23)
    data[:, 8] = np.random.randint(0, 24, size=n_samples)

    # Feature 9: day_of_week (uniform 0-6)
    data[:, 9] = np.random.randint(0, 7, size=n_samples)

    return data


def generate_anomaly_data(n_samples: int,
                         seed: int) -> np.ndarray:
    """
    Generate anomalous data with multiple anomaly types

    Anomaly types:
    1. High latency + errors (30%)
    2. Resource spike (CPU/Memory high) (30%)
    3. Network/Disk bottleneck (20%)
    4. Combination of issues (20%)

    Args:
        n_samples: Number of anomalies
        seed: Random seed

    Returns:
        Data array of shape (n_samples, 10)
    """

    np.random.seed(seed)

    data = np.zeros((n_samples, 10), dtype=np.float32)

    # Randomly assign anomaly types
    types = np.random.choice([1, 2, 3, 4], size=n_samples, p=[0.3, 0.3, 0.2, 0.2])

    for i in range(n_samples):
        atype = types[i]

        # ============= TYPE 1: High Latency + Errors =============
        if atype == 1:
            data[i, 0] = np.random.uniform(1000, 10000)  # High response time
            data[i, 1] = np.random.choice([500, 502, 503, 504])  # Server errors
            data[i, 2] = np.random.uniform(50, 150)  # Request count drops
            data[i, 3] = np.random.uniform(0.1, 0.3)  # High error rate
            data[i, 4] = np.random.uniform(30, 70)  # CPU normal-high
            data[i, 5] = np.random.uniform(40, 80)  # Memory normal-high
            data[i, 6] = np.random.uniform(200, 400)  # Network normal
            data[i, 7] = np.random.uniform(100, 300)  # Disk normal

        # ============= TYPE 2: Resource Spike =============
        elif atype == 2:
            data[i, 0] = np.random.uniform(300, 800)  # Moderate latency
            data[i, 1] = 200  # Status OK but system struggling
            data[i, 2] = np.random.uniform(80, 200)  # Request count normal-high
            data[i, 3] = np.random.uniform(0.01, 0.05)  # Error rate low
            data[i, 4] = np.random.uniform(80, 100)  # CPU spike
            data[i, 5] = np.random.uniform(85, 100)  # Memory spike
            data[i, 6] = np.random.uniform(250, 500)  # Network normal-high
            data[i, 7] = np.random.uniform(150, 400)  # Disk normal-high

        # ============= TYPE 3: Network/Disk Bottleneck =============
        elif atype == 3:
            data[i, 0] = np.random.uniform(500, 1500)  # Increased latency
            data[i, 1] = 200  # Status OK
            data[i, 2] = np.random.uniform(100, 200)  # Request count high
            data[i, 3] = np.random.uniform(0.02, 0.1)  # Some errors
            data[i, 4] = np.random.uniform(50, 70)  # CPU moderate
            data[i, 5] = np.random.uniform(60, 80)  # Memory moderate
            data[i, 6] = np.random.uniform(8000, 10000)  # Network spike
            data[i, 7] = np.random.uniform(8000, 10000)  # Disk spike

        # ============= TYPE 4: Combination =============
        else:
            data[i, 0] = np.random.uniform(2000, 10000)  # Very high latency
            data[i, 1] = np.random.choice([200, 503, 504])
            data[i, 2] = np.random.uniform(50, 150)  # Request drop
            data[i, 3] = np.random.uniform(0.1, 0.3)  # High error rate
            data[i, 4] = np.random.uniform(70, 100)  # CPU high
            data[i, 5] = np.random.uniform(75, 100)  # Memory high
            data[i, 6] = np.random.uniform(5000, 10000)  # Network issue
            data[i, 7] = np.random.uniform(5000, 10000)  # Disk issue

        # Hour and day (same distribution as normal)
        data[i, 8] = np.random.randint(0, 24)
        data[i, 9] = np.random.randint(0, 7)

    return data


def main():
    """Main data generation"""

    args = parse_arguments()

    logger.info("=" * 60)
    logger.info("Generating Synthetic Training Data")
    logger.info("=" * 60)
    logger.info(f"Samples: {args.samples:,}")
    logger.info(f"Anomaly ratio: {args.anomaly_ratio:.2%}")
    logger.info(f"Output: {args.output}")

    # Calculate split
    n_anomalies = int(args.samples * args.anomaly_ratio)
    n_normal = args.samples - n_anomalies

    logger.info(f"Normal samples: {n_normal:,}")
    logger.info(f"Anomaly samples: {n_anomalies:,}")

    try:
        # Generate data
        logger.info("Generating normal data...")
        normal_data = generate_normal_data(n_normal, args.seed)

        logger.info("Generating anomaly data...")
        anomaly_data = generate_anomaly_data(n_anomalies, args.seed + 1)

        # Combine data
        X = np.vstack([normal_data, anomaly_data])
        y = np.hstack([
            np.zeros(n_normal, dtype=int),
            np.ones(n_anomalies, dtype=int)
        ])

        # Shuffle
        shuffle_idx = np.random.permutation(len(X))
        X = X[shuffle_idx]
        y = y[shuffle_idx]

        # Create DataFrame
        feature_names = [
            'response_time', 'status_code', 'request_count', 'error_rate',
            'cpu_usage', 'memory_usage', 'network_io', 'disk_io',
            'hour_of_day', 'day_of_week'
        ]

        df = pd.DataFrame(X, columns=feature_names)
        df['is_anomaly'] = y

        # Create output directory
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)

        # Save CSV
        df.to_csv(args.output, index=False)

        logger.info("=" * 60)
        logger.info(f"✅ Data generated successfully!")
        logger.info("=" * 60)
        logger.info(f"File: {args.output}")
        logger.info(f"Total samples: {len(df):,}")
        logger.info(f"Normal: {(y == 0).sum():,} ({(y == 0).sum()/len(df)*100:.1f}%)")
        logger.info(f"Anomaly: {(y == 1).sum():,} ({(y == 1).sum()/len(df)*100:.1f}%)")
        logger.info(f"\nFeature statistics:")
        logger.info(df.describe().to_string())

    except Exception as e:
        logger.error(f"Data generation failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
