import argparse
from pathlib import Path
import pandas as pd
import numpy as np

try:
    import yaml
except ImportError:
    raise SystemExit('Missing dependency: pyyaml (pip install pyyaml)')


def load_cfg(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def floor_window(ts_ms: pd.Series, win_ms: int) -> pd.Series:
    return (ts_ms // win_ms) * win_ms


def intervals_overlap_any(win_start: int, win_end: int, starts: np.ndarray, ends: np.ndarray) -> bool:
    # any interval intersects [win_start, win_end)
    # overlap if start < win_end and end > win_start
    return bool(np.any((starts < win_end) & (ends > win_start)))


def main(cfg_path: str):
    cfg = load_cfg(cfg_path)
    win_ms = int(cfg['window']['size_s']) * 1000

    root = Path(cfg['train_ticket']['root'])
    out_dir = Path(cfg['train_ticket']['prepared_dir'])
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load fault intervals
    entity_intervals = pd.read_csv(out_dir/'fault_intervals_entity.csv')
    global_intervals = pd.read_csv(out_dir/'fault_intervals_global.csv')
    g_starts = global_intervals['fault_start_ms'].to_numpy()
    g_ends = global_intervals['fault_end_ms'].to_numpy()

    # Pre-index entity intervals for quick access
    by_entity = {}
    for (obj, name), g in entity_intervals.groupby(['object','name']):
        by_entity[(obj, name)] = (g['fault_start_ms'].to_numpy(), g['fault_end_ms'].to_numpy())

    rows = []

    # ---- ESB (business metrics): per serviceName 60s rows
    # NOTE: fault list entities (db_003/docker_003/os_018) do NOT map to serviceName (e.g., osb_001),
    # so we label ESB at GLOBAL level per window to avoid incorrect entity mapping.
    for day in cfg['train_ticket']['days']:
        esb_path = root/day/'metrics_business'/'esb.csv'
        if not esb_path.exists():
            continue
        df = pd.read_csv(esb_path)
        if not {'serviceName','startTime'}.issubset(df.columns):
            continue

        df['window_start_ms'] = floor_window(df['startTime'].astype('int64'), win_ms)

        # Aggregate duplicates per (serviceName, window)
        num_cols = [c for c in df.columns if c not in ('serviceName','startTime','window_start_ms')]
        agg = df.groupby(['serviceName','window_start_ms'], as_index=False)[num_cols].mean(numeric_only=True)

        # metrics scalar: mean of absolute values across numeric cols
        if num_cols:
            metrics_scalar = agg[num_cols].abs().mean(axis=1)
        else:
            metrics_scalar = pd.Series(0.0, index=agg.index)

        # global label by window
        y = []
        for ws in agg['window_start_ms'].tolist():
            y.append(1 if intervals_overlap_any(ws, ws+win_ms, g_starts, g_ends) else 0)

        split = ('train' if day in cfg['splits']['train_days'] else
                 'val' if day in cfg['splits']['val_days'] else
                 'test' if day in cfg['splits']['test_days'] else
                 'ignore')

        for i in range(len(agg)):
            rows.append({
                'dataset': 'train_ticket',
                'subsystem': 'esb',
                'split': split,
                'day': day,
                'entity_type': 'service',
                'entity_id': str(agg.loc[i,'serviceName']),
                'window_start_ms': int(agg.loc[i,'window_start_ms']),
                'y': int(y[i]),
                'metrics': float(metrics_scalar.iloc[i]),
                'logs': 0.0,
                'traces': 0.0,
            })

    # ---- Platform metrics: entity-aware by cmdb_id, aggregated per KPI name
    for day in cfg['train_ticket']['days']:
        plat_dir = root/day/'metrics_platform'
        if not plat_dir.exists():
            continue
        for csv_path in plat_dir.glob('*.csv'):
            df = pd.read_csv(csv_path)
            if not {'timestamp','cmdb_id','name','value'}.issubset(df.columns):
                continue

            df = df.dropna(subset=['timestamp','cmdb_id','name','value']).copy()
            df['timestamp'] = df['timestamp'].astype('int64')
            df['window_start_ms'] = floor_window(df['timestamp'], win_ms)
            df['cmdb_id'] = df['cmdb_id'].astype(str).str.strip()
            df['obj'] = df['cmdb_id'].str.split('_').str[0].str.lower()  # db/docker/os/mw

            # Aggregate within minute per (cmdb_id, window, kpi)
            g = df.groupby(['cmdb_id','obj','window_start_ms','name'], as_index=False)['value'].mean(numeric_only=True)

            # Reduce to scalar per (cmdb_id, window)
            # metrics_scalar = mean(abs(value)) across KPIs
            scalar = g.groupby(['cmdb_id','obj','window_start_ms'], as_index=False)['value'].apply(lambda s: float(np.mean(np.abs(s.to_numpy()))))
            scalar = scalar.rename(columns={'value':'metrics_scalar'})

            # Labels: entity-aware by (obj, cmdb_id)
            ys = []
            for _, r in scalar.iterrows():
                key = (str(r['obj']).lower(), str(r['cmdb_id']))
                starts, ends = by_entity.get(key, (np.array([],dtype='int64'), np.array([],dtype='int64')))
                ws = int(r['window_start_ms'])
                y = 1 if (len(starts) and intervals_overlap_any(ws, ws+win_ms, starts, ends)) else 0
                ys.append(y)

            split = ('train' if day in cfg['splits']['train_days'] else
                     'val' if day in cfg['splits']['val_days'] else
                     'test' if day in cfg['splits']['test_days'] else
                     'ignore')

            for i in range(len(scalar)):
                rows.append({
                    'dataset': 'train_ticket',
                    'subsystem': f"platform:{csv_path.stem}",
                    'split': split,
                    'day': day,
                    'entity_type': str(scalar.loc[i,'obj']),
                    'entity_id': str(scalar.loc[i,'cmdb_id']),
                    'window_start_ms': int(scalar.loc[i,'window_start_ms']),
                    'y': int(ys[i]),
                    'metrics': float(scalar.loc[i,'metrics_scalar']),
                    'logs': 0.0,
                    'traces': 0.0,
                })

    out = pd.DataFrame(rows)
    out = out[out['split'] != 'ignore']

    # Persist
    out_path = out_dir/'samples_60s.csv'
    out.to_csv(out_path, index=False)
    print('Wrote:', out_path, 'rows=', len(out))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cfg', required=True)
    args = ap.parse_args()
    main(args.cfg)
