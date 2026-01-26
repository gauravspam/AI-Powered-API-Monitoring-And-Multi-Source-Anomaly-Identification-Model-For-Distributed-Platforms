import json
from pathlib import Path

import numpy as np
import pandas as pd

def load_metrics_for_experiment(experiment_dir):
    """Load all service metrics for one experiment run"""
    metrics_dir = Path(experiment_dir) / "metrics"
    all_metrics = []

    for csv_file in metrics_dir.glob("*.csv"):
        service_name = csv_file.stem
        df = pd.read_csv(csv_file)
        df["service"] = service_name
        all_metrics.append(df)

    merged = pd.concat(all_metrics, ignore_index=True)
    merged["timestamp"] = pd.to_datetime(merged["timestamp"], unit="s")
    return merged


def load_fault_labels(fault_file):
    """Load ground truth fault annotations"""
    with open(fault_file, "r") as f:
        fault_data = json.load(f)

    faults = []
    for fault in fault_data["faults"]:
        faults.append(
            {
                "service": fault["name"],
                "fault_type": fault["fault"],
                "start": fault["start"],
                "end": fault["start"] + fault["duration"],
            }
        )

    return pd.DataFrame(faults), fault_data["start"], fault_data["end"]


def label_anomalies(metrics_df, faults_df):
    """Add binary anomaly labels to metrics"""
    metrics_df["is_anomaly"] = 0
    metrics_df["fault_type"] = "normal"

    for _, fault in faults_df.iterrows():
        fault_start = pd.Timestamp(fault["start"], unit="s")
        fault_end = pd.Timestamp(fault["end"], unit="s")

        service_key = (
            fault["service"].split("-")[1]
            if "-" in fault["service"]
            else fault["service"]
        )

        mask = (
            (metrics_df["service"].str.contains(service_key, case=False))
            & (metrics_df["timestamp"] >= fault_start)
            & (metrics_df["timestamp"] <= fault_end)
        )
        metrics_df.loc[mask, "is_anomaly"] = 1
        metrics_df.loc[mask, "fault_type"] = fault["fault_type"]

    return metrics_df


def process_experiment(experiment_dir, fault_file):
    """Process one complete experiment run"""
    print(f"Processing {experiment_dir.name}...")

    metrics_df = load_metrics_for_experiment(experiment_dir)
    print(
        f"  Loaded {len(metrics_df)} metric samples from {metrics_df['service'].nunique()} services"
    )

    faults_df, exp_start, exp_end = load_fault_labels(fault_file)
    print(f"  Loaded {len(faults_df)} fault injections")

    metrics_df = label_anomalies(metrics_df, faults_df)

    # Aggregate per timestamp across all services
    features = (
        metrics_df.groupby("timestamp")
        .agg(
            {
                "cpu_usage_system": ["mean", "std", "max"],
                "cpu_usage_total": ["mean", "std", "max"],
                "cpu_usage_user": ["mean", "std", "max"],
                "memory_usage": ["mean", "std", "max"],
                "memory_working_set": ["mean", "std", "max"],
                "rx_bytes": ["sum", "mean", "std"],
                "tx_bytes": ["sum", "mean", "std"],
                "is_anomaly": "max",
                "fault_type": lambda x: x.mode()[0] if len(x) > 0 else "normal",
            }
        )
        .reset_index()
    )

    features.columns = ["_".join(col).strip("_") for col in features.columns.values]

    print(
        f"  Result: {len(features)} samples, {features['is_anomaly_max'].sum()} anomalies ({features['is_anomaly_max'].mean() * 100:.1f}%)\n"
    )

    return features


if __name__ == "__main__":
    base_dir = Path(
        "data/external_datasets/microservices_icse2023/social_network/SN Dataset/data"
    )
    output_dir = Path("data/Microservices_ICSE2023")
    output_dir.mkdir(exist_ok=True)

    all_experiments = []

    for exp_dir in sorted(base_dir.glob("SN.2022*")):
        exp_name = exp_dir.name
        fault_file = base_dir / f"SN.fault-{exp_name.replace('SN.', '')}.json"

        if fault_file.exists():
            try:
                features = process_experiment(exp_dir, fault_file)
                features["experiment"] = exp_name
                all_experiments.append(features)
            except Exception as e:
                print(f"  ERROR: {e}\n")
                import traceback

                traceback.print_exc()
                continue

    if len(all_experiments) == 0:
        print("ERROR: No experiments processed successfully")
        exit(1)

    full_dataset = pd.concat(all_experiments, ignore_index=True)
    full_dataset.to_parquet(
        output_dir / "social_network_processed.parquet", index=False
    )

    print(f"{'=' * 60}")
    print(f"Processing Complete")
    print(f"{'=' * 60}")
    print(f"Total samples: {len(full_dataset)}")
    print(
        f"Anomaly samples: {full_dataset['is_anomaly_max'].sum()} ({full_dataset['is_anomaly_max'].mean() * 100:.1f}%)"
    )
    print(
        f"Feature columns: {len([c for c in full_dataset.columns if c not in ['timestamp', 'is_anomaly_max', 'fault_type_<lambda>', 'experiment']])}"
    )
    print(f"\nFault distribution:")
    print(full_dataset["fault_type_<lambda>"].value_counts())
    print(f"\nFault distribution:")
    print(full_dataset['fault_type_<lambda>'].value_counts())
    print(f"\nExperiments: {full_dataset['experiment'].nunique()}")
    print(f"\nSaved to: {output_dir / 'social_network_processed.parquet'}")
