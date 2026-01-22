
import pandas as pd

import numpy as np

from pathlib import Path

import json



def transform_nab_to_training_format(nab_data_path, nab_labels_path, output_csv):

    """Transform NAB time-series to 10-feature format"""

    

    print(f"📂 Loading NAB data from {nab_data_path}")

    df = pd.read_csv(nab_data_path, parse_dates=['timestamp'])

    

    with open(nab_labels_path, 'r') as f:

        labels = json.load(f)

    

    filename = Path(nab_data_path).relative_to(Path(nab_data_path).parents[1])

    anomaly_windows = labels.get(str(filename), [])

    

    print(f"✅ Loaded {len(df)} samples with {len(anomaly_windows)} known anomaly windows")

    

    transformed = pd.DataFrame()

    transformed['response_time'] = df['value'] * 100

    transformed['status_code'] = np.where(df['value'] > df['value'].quantile(0.90), 500, 200)

    transformed['request_count'] = df['value'].rolling(window=5, min_periods=1).sum()

    transformed['error_rate'] = df['value'].rolling(window=10, min_periods=1).std() / (df['value'].mean() + 1e-6)

    transformed['error_rate'] = transformed['error_rate'].clip(0, 1)

    

    value_norm = (df['value'] - df['value'].min()) / (df['value'].max() - df['value'].min() + 1e-6)

    transformed['cpu_usage'] = 20 + value_norm * 70

    

    transformed['memory_usage'] = df['value'].shift(1).fillna(df['value'])

    transformed['memory_usage'] = (transformed['memory_usage'] - transformed['memory_usage'].min()) / (transformed['memory_usage'].max() - transformed['memory_usage'].min() + 1e-6) * 60 + 30

    

    transformed['network_io'] = df['value'].diff().fillna(0).abs() * 1000

    transformed['disk_io'] = df['value'].cumsum() / 100

    transformed['hour_of_day'] = df['timestamp'].dt.hour

    transformed['day_of_week'] = df['timestamp'].dt.dayofweek

    

    # Create labels - FIX: Handle anomaly windows properly

    transformed['is_anomaly'] = 0

    

    for window in anomaly_windows:

        # Each window is [start_timestamp, end_timestamp]

        if isinstance(window, list) and len(window) == 2:

            start_ts = pd.to_datetime(window[0])

            end_ts = pd.to_datetime(window[1])

            

            # Mark all timestamps within window as anomalies

            mask = (df['timestamp'] >= start_ts) & (df['timestamp'] <= end_ts)

            transformed.loc[mask, 'is_anomaly'] = 1

        else:

            # Single timestamp - mark it and next 5 samples

            anomaly_ts = pd.to_datetime(window)

            idx = df[df['timestamp'] == anomaly_ts].index

            if len(idx) > 0:

                start = idx[0]

                end = min(start + 5, len(df))

                transformed.loc[start:end, 'is_anomaly'] = 1

    

    transformed = transformed.replace([np.inf, -np.inf], np.nan)

    transformed = transformed.fillna(0)

    

    print(f"\n📊 Data distribution:")

    anomaly_count = (transformed['is_anomaly'] == 1).sum()

    normal_count = (transformed['is_anomaly'] == 0).sum()

    print(f"   Normal: {normal_count} ({normal_count/len(transformed)*100:.1f}%)")

    print(f"   Anomaly: {anomaly_count} ({anomaly_count/len(transformed)*100:.1f}%)")

    

    output_path = Path(output_csv)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    transformed.to_csv(output_csv, index=False)

    

    print(f"\n💾 Saved to: {output_csv}")

    print(f"   Shape: {transformed.shape}")

    print(f"\n🎯 Ready to train!")

    

    return transformed



if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('--nab-data', type=str, required=True)

    parser.add_argument('--nab-labels', type=str, default='NAB/labels/combined_windows.json')

    parser.add_argument('--output', type=str, default='data/training_data_nab.csv')

    args = parser.parse_args()

    transform_nab_to_training_format(args.nab_data, args.nab_labels, args.output)

