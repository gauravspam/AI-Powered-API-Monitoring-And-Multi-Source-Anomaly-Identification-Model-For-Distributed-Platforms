import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def load_labeled_data():
    """
    Load data from your databases and label anomalies.
    You'll need to manually label or use existing anomaly flags.
    """
    # Example: Load from PostgreSQL + OpenSearch
    # This is pseudocode - adapt to your actual data access

    logs = load_logs_from_opensearch()
    metrics = load_metrics_from_postgres()
    traces = load_traces_from_postgres()

    # Merge by time windows
    dataset = merge_by_time_window(logs, metrics, traces, window_size=60)

    # Label anomalies (CRITICAL: This is your ground truth)
    dataset['is_anomaly'] = label_anomalies(dataset)

    return dataset

def label_anomalies(dataset):
    """
    Labeling strategy:
    1. Use existing anomaly flags from AnomalyRecord table
    2. Manual labeling by domain experts
    3. Rule-based heuristics (e.g., error_rate > 10%)
    """
    labels = []
    for row in dataset.itertuples():
        # Example heuristic
        if row.error_rate > 10 or "CRITICAL" in row.log_text:
            labels.append(1)
        else:
            labels.append(0)
    return labels

if __name__ == "__main__":
    dataset = load_labeled_data()

    # Split train/test
    train, test = train_test_split(dataset, test_size=0.2, stratify=dataset['is_anomaly'])

    train.to_csv('data/train.csv', index=False)
    test.to_csv('data/test.csv', index=False)

    print(f"✅ Created {len(train)} train, {len(test)} test samples")
    print(f"Anomaly rate: {dataset['is_anomaly'].mean():.2%}")
