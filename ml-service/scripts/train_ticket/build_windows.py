#!/usr/bin/env python3
"""
Build structured multimodal windows from TrainTicket dataset.

Output: JSONL file where each line is:
{
  "context": {
    "service_name": "trainticket",
    "window_start_ms": 1234567890000,
    "window_end_ms": 1234567950000,
    "environment": "test"
  },
  "metrics": [
    {"name": "cpu_usage", "values": [0.5, 0.6, ...]},
    ...
  ],
  "logs": [
    {"timestamp": 1234567891000, "level": "ERROR", "template": "..."},
    ...
  ],
  "traces": [
    {"trace_id": "abc", "span_id": "123", "service": "api", ...},
    ...
  ],
  "label": 0  # or 1 for anomaly
}
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_metrics(csv_path, window_start, window_end):
    """Load metrics for window and return List[MetricSeries]"""
    df = pd.read_csv(csv_path)
    df = df[(df['timestamp'] >= window_start) & (df['timestamp'] < window_end)]

    metrics = []
    for col in df.columns:
        if col == 'timestamp':
            continue
        values = df[col].fillna(0).tolist()
        if values:
            metrics.append({
                "name": col,
                "values": values,
                "timestamps": df['timestamp'].tolist()
            })

    return metrics


def load_logs(csv_path, window_start, window_end):
    """Load logs for window and return List[LogEvent]"""
    try:
        df = pd.read_csv(csv_path)
        df = df[(df['startTime'] >= window_start) & (df['startTime'] < window_end)]

        logs = []
        for _, row in df.iterrows():
            logs.append({
                "timestamp": int(row['startTime']),
                "level": str(row.get('level', 'INFO')).upper(),
                "template": str(row.get('message', '')),
                "service": str(row.get('service', 'unknown'))
            })

        return logs
    except Exception as e:
        logger.warning(f"Failed to load logs: {e}")
        return []


def load_traces(csv_path, window_start, window_end):
    """Load traces for window and return List[SpanEvent]"""
    try:
        df = pd.read_csv(csv_path)
        df = df[(df['startTime'] >= window_start) & (df['startTime'] < window_end)]

        traces = []
        for _, row in df.iterrows():
            traces.append({
                "trace_id": str(row.get('traceId', '')),
                "span_id": str(row.get('id', '')),
                "parent_span_id": str(row.get('pid', '')) if pd.notna(row.get('pid')) else None,
                "service": str(row.get('serviceName', 'unknown')),
                "operation": str(row.get('cmdb_id', 'unknown')),
                "duration_ms": float(row.get('elapsedTime', 0)),
                "status_code": 200 if row.get('success', 1) == 1 else 500,
                "is_error": row.get('success', 1) == 0
            })

        return traces
    except Exception as e:
        logger.warning(f"Failed to load traces: {e}")
        return []


def load_fault_intervals(label_csv_path):
    """
    Load fault intervals from label CSV.
    Returns list of (start_ms, end_ms, fault_type) tuples.
    """
    try:
        df = pd.read_csv(label_csv_path)
        intervals = []

        for _, row in df.iterrows():
            start_ms = int(row['fault_start_ms'])
            end_ms = int(row['fault_end_ms'])
            fault_type = str(row.get('fault_type', 'unknown'))
            intervals.append((start_ms, end_ms, fault_type))

        return intervals
    except Exception as e:
        logger.warning(f"Failed to load labels: {e}")
        return []


def is_anomaly_window(window_start, window_end, fault_intervals):
    """Check if window overlaps with any fault interval"""
    for fault_start, fault_end, _ in fault_intervals:
        # Check for overlap
        if not (window_end <= fault_start or window_start >= fault_end):
            return 1  # Anomaly
    return 0  # Normal


def main(config_path: str, output_path: str):
    """Build multimodal windows from TrainTicket dataset"""

    with open(config_path) as f:
        cfg = json.load(f)

    root = Path(cfg['trainticket']['root'])
    window_size_ms = cfg['window']['sizes'][0]  # e.g., 60000 (60s)

    samples = []

    # Iterate over days
    all_days = cfg['splits'].get('train_days', []) + \
               cfg['splits'].get('val_days', []) + \
               cfg['splits'].get('test_days', [])

    for day in all_days:
        logger.info(f"Processing day: {day}")

        day_dir = root / day

        # Data paths
        metric_csv = day_dir / 'metrics_platform' / 'os_linux.csv'
        log_csv = day_dir / 'metrics_business' / 'esb.csv'
        trace_csv = day_dir / 'traces' / 'trace_csf.csv'
        label_csv = day_dir / 'labels' / 'fault_intervals.csv'

        # Check if files exist
        if not metric_csv.exists():
            logger.warning(f"Metrics file not found: {metric_csv}")
            continue

        # Load fault intervals for labeling
        fault_intervals = load_fault_intervals(label_csv) if label_csv.exists() else []

        # Determine time range from metrics
        m_df = pd.read_csv(metric_csv)
        start_time = int(m_df['timestamp'].min())
        end_time = int(m_df['timestamp'].max())

        logger.info(f"  Time range: {start_time} - {end_time} ({(end_time - start_time) / 1000 / 60:.1f} min)")

        # Sliding windows
        current = start_time
        window_count = 0

        while current < end_time:
            window_end = current + window_size_ms

            # Load data for this window
            metrics = load_metrics(metric_csv, current, window_end)
            logs = load_logs(log_csv, current, window_end) if log_csv.exists() else []
            traces = load_traces(trace_csv, current, window_end) if trace_csv.exists() else []

            # Determine label
            label = is_anomaly_window(current, window_end, fault_intervals)

            # Build sample
            sample = {
                "context": {
                    "service_name": "trainticket",
                    "environment": "test",
                    "window_start_ms": current,
                    "window_end_ms": window_end
                },
                "metrics": metrics,
                "logs": logs,
                "traces": traces,
                "label": label
            }

            samples.append(sample)
            window_count += 1
            current += window_size_ms

        logger.info(f"  Generated {window_count} windows")

    # Save as JSONL
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        for sample in samples:
            f.write(json.dumps(sample) + '\n')

    # Statistics
    anomaly_count = sum(1 for s in samples if s['label'] == 1)
    normal_count = len(samples) - anomaly_count

    logger.info(f"\n{'='*60}")
    logger.info(f"Dataset Summary")
    logger.info(f"{'='*60}")
    logger.info(f"Total windows: {len(samples)}")
    logger.info(f"Normal: {normal_count} ({normal_count/len(samples)*100:.1f}%)")
    logger.info(f"Anomaly: {anomaly_count} ({anomaly_count/len(samples)*100:.1f}%)")
    logger.info(f"Output: {output_file}")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='Path to dataset config JSON')
    parser.add_argument('--output', required=True, help='Output JSONL path')

    args = parser.parse_args()
    main(args.config, args.output)
