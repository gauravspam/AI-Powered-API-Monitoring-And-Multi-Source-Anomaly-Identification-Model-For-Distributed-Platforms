#!/usr/bin/env python3
"""
Bulletproof AIOps TrainTicket window builder.
Skips ALL problematic files, limits memory usage.
"""

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def safe_read_csv(path, max_rows=10000):
    encodings = ["gbk", "utf-8", "latin1"]
    for enc in encodings:
        try:
            # Read with nrows limit to avoid memory bombs
            df = pd.read_csv(path, encoding=enc, nrows=max_rows, low_memory=False)

            # Quick sanity check
            if df.empty or df.shape[1] < 2:
                logger.debug(f"Empty CSV: {path}")
                return None

            logger.debug(f"✅ Read {path} ({df.shape[0]} rows)")
            return df
        except Exception as e:
            logger.debug(f"Failed {path} with {enc}: {str(e)[:100]}")
            continue
    logger.warning(f"❌ Skipped {path}")
    return None


def load_fault_intervals(root_fault_csv):
    """Flexible fault parsing."""
    df = safe_read_csv(root_fault_csv)
    if df is None:
        return []

    intervals = []
    time_pairs = [
        ("start_time", "end_time"),
        ("fault_start_ms", "fault_end_ms"),
        ("开始时间", "结束时间"),
        ("log_time", "duration"),
    ]

    for start_col, end_col in time_pairs:
        if start_col in df.columns and end_col in df.columns:
            for _, row in df.iterrows():
                try:
                    start = pd.to_numeric(row[start_col], errors="coerce")
                    end = pd.to_numeric(row[end_col], errors="coerce")
                    if pd.notna(start) and pd.notna(end) and start < end:
                        intervals.append(
                            (int(start * 1000), int(end * 1000), str(start_col))
                        )
                except:
                    continue

    logger.info(f"Loaded {len(intervals)} fault intervals")
    return intervals


def load_metrics(day_dir, window_start, window_end):
    """Safe metrics loading."""
    metrics_dir = day_dir / "metrics_platform"
    if not metrics_dir.exists():
        return []

    all_metrics = []
    csv_count = 0

    for csv_path in list(metrics_dir.glob("*.csv"))[:3]:  # Limit to 3 files
        df = safe_read_csv(csv_path)
        if df is None:
            continue

        ts_col = next((c for c in ["timestamp", "time"] if c in df.columns), None)
        if not ts_col:
            continue

        try:
            df[ts_col] = pd.to_numeric(df[ts_col], errors="coerce")
            df = df[(df[ts_col] >= window_start) & (df[ts_col] < window_end)]

            ts_values = df[ts_col].dropna().astype(int).tolist()
            if not ts_values:
                continue

            # First 3 numeric columns only
            num_cols = 0
            for col in df.columns:
                if col == ts_col or num_cols >= 3:
                    continue
                try:
                    values = pd.to_numeric(df[col], errors="coerce").fillna(0).tolist()
                    if len(values) > 0:
                        all_metrics.append(
                            {
                                "name": f"{csv_path.stem}_{col}",
                                "values": values[:10],  # Limit length
                                "timestamps": ts_values[:10],
                            }
                        )
                        num_cols += 1
                except:
                    continue

            csv_count += 1
        except Exception as e:
            logger.debug(f"Metrics error {csv_path}: {e}")

    logger.debug(f"Loaded {len(all_metrics)} metric series from {csv_count} files")
    return all_metrics


def load_logs(day_dir, window_start, window_end):
    """Safe log loading."""
    log_dir = day_dir / "metrics_business"
    if not log_dir.exists():
        return []

    csv_path = log_dir / "esb.csv"
    df = safe_read_csv(csv_path)
    if df is None:
        return []

    ts_col = next((c for c in ["startTime", "timestamp"] if c in df.columns), None)
    if not ts_col:
        return []

    try:
        df[ts_col] = pd.to_numeric(df[ts_col], errors="coerce")
        df = df[df[ts_col] >= window_start]

        logs = []
        for _, row in df.head(5).iterrows():  # Max 5 logs/window
            logs.append(
                {
                    "timestamp": int(row[ts_col]),
                    "level": "INFO",
                    "message": str(row.iloc[0])[:50],  # First column as message
                    "service": "esb",
                }
            )
        return logs
    except:
        return []


def load_traces(day_dir, window_start, window_end):
    """Safe trace loading - MAX 3 CSVs."""
    traces_dir = day_dir / "traces"
    if not traces_dir.exists():
        return []

    all_traces = []
    csv_files = list(traces_dir.glob("*.csv"))[:3]  # Only first 3

    for csv_path in csv_files:
        df = safe_read_csv(csv_path)
        if df is None:
            continue

        ts_col = next(
            (c for c in ["startTime", "timestamp", "start_time"] if c in df.columns),
            None,
        )
        if not ts_col:
            continue

        try:
            df[ts_col] = pd.to_numeric(df[ts_col], errors="coerce")
            df = df[(df[ts_col] >= window_start) & (df[ts_col] < window_end)]

            for _, row in df.head(10).iterrows():  # Max 10 spans/window
                all_traces.append(
                    {
                        "trace_id": "unknown",
                        "span_id": str(row.get("id", row.index)),
                        "service": csv_path.stem,
                        "operation": "unknown",
                        "duration_ms": 100.0,
                        "status_code": 200,
                        "timestamp": int(row[ts_col]),
                    }
                )
        except Exception as e:
            logger.debug(f"Trace skip {csv_path}: {e}")

    return all_traces


def main(config_path: str, output_path: str):
    with open(config_path) as f:
        cfg = json.load(f)

    root = Path(cfg["trainticket"]["root"])
    window_size_ms = cfg["window"]["sizes"][0]

    fault_csv = Path(cfg["trainticket"]["fault_list_csv"])
    fault_intervals = load_fault_intervals(fault_csv)

    samples = []
    all_days = (
        cfg["splits"].get("train_days", [])
        + cfg["splits"].get("val_days", [])
        + cfg["splits"].get("test_days", [])
    )

    total_windows = 0
    for day in all_days[:2]:  # Limit to first 2 days for testing
        logger.info(f"Processing day: {day}")
        day_dir = root / day

        try:
            m_df = safe_read_csv(day_dir / "metrics_platform" / "os_linux.csv")
            if m_df is None:
                continue

            start_time = int(m_df["timestamp"].min())
            end_time = int(m_df["timestamp"].max())

            current = start_time // window_size_ms * window_size_ms
            window_count = 0

            while current < end_time and window_count < 100:  # Limit for testing
                window_end = current + window_size_ms

                metrics = load_metrics(day_dir, current, window_end)
                logs = load_logs(day_dir, current, window_end)
                traces = load_traces(day_dir, current, window_end)

                label = 1 if fault_intervals else 0  # Default to normal if no faults

                sample = {
                    "window_start": current,
                    "window_end": window_end,
                    "entity_id": f"trainticket-{day}",
                    "metrics": metrics,
                    "logs": logs,
                    "traces": traces,
                    "label": label,
                }

                samples.append(sample)
                window_count += 1
                current += window_size_ms

            logger.info(f"  Generated {window_count} windows")
            total_windows += window_count

        except Exception as e:
            logger.error(f"Failed day {day}: {e}")

    # Save
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    logger.info("=" * 60)
    logger.info(f"TOTAL: {total_windows} windows saved to {output_file}")
    logger.info(
        f"Sample size: {len(samples[0]['metrics']) if samples else 0} metrics/window"
    )
    logger.info(f"Sample size: {len(samples[0]['metrics']) if samples else 0} metrics/window")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    main(args.config, args.output)
