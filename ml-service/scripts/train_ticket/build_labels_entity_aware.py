import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import pandas as pd

try:
    import yaml
except ImportError:
    raise SystemExit('Missing dependency: pyyaml (pip install pyyaml)')

try:
    import zoneinfo
except ImportError:
    zoneinfo = None

DUR_RE = re.compile(r"^(?P<num>\d+)(?P<unit>min|m|s|sec|h|hour|d)$", re.IGNORECASE)


def parse_duration_to_ms(s: str) -> int:
    s = str(s).strip()
    if not s:
        raise ValueError('empty duration')
    m = DUR_RE.match(s)
    if not m:
        raise ValueError(f'Unsupported duration: {s}')
    num = int(m.group('num'))
    unit = m.group('unit').lower()
    mult = {
        's': 1000, 'sec': 1000,
        'm': 60_000, 'min': 60_000,
        'h': 3_600_000, 'hour': 3_600_000,
        'd': 86_400_000,
    }[unit]
    return num * mult


def parse_local_time_to_epoch_ms(s: str, tz: str) -> int:
    # fault list uses format like: 2020/4/11 0:05
    s = str(s).strip()
    if not s:
        raise ValueError('empty time')
    # zero-pad robustness handled by strptime patterns below
    dt = pd.to_datetime(s, format='%Y/%m/%d %H:%M', errors='coerce')
    if pd.isna(dt):
        dt = pd.to_datetime(s, errors='raise')
    if zoneinfo is None:
        # fallback: treat as naive; caller should avoid this in production
        return int(dt.to_datetime64().astype('datetime64[ms]').astype('int64'))
    z = zoneinfo.ZoneInfo(tz)
    dt = dt.to_pydatetime().replace(tzinfo=z)
    return int(dt.timestamp() * 1000)


def load_cfg(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main(cfg_path: str):
    cfg = load_cfg(cfg_path)
    out_dir = Path(cfg['train_ticket']['prepared_dir'])
    out_dir.mkdir(parents=True, exist_ok=True)

    fault_csv = cfg['train_ticket']['fault_list_csv']
    tz = cfg['train_ticket']['timezone']
    win_ms = int(cfg['window']['size_s']) * 1000

    faults = pd.read_csv(fault_csv)

    # choose event time: prefer start_time, else log_time
    tcol = 'start_time' if 'start_time' in faults.columns else None
    if tcol is None:
        raise ValueError('fault list missing start_time')

    def pick_time(row):
        v = row.get('start_time', None)
        if pd.isna(v) or str(v).strip() == '':
            v = row.get('log_time', None)
        return v

    faults['event_time_str'] = faults.apply(pick_time, axis=1)
    faults = faults[~faults['event_time_str'].isna()].copy()

    faults['fault_start_ms'] = faults['event_time_str'].apply(lambda x: parse_local_time_to_epoch_ms(x, tz))
    faults['fault_dur_ms'] = faults['duration'].apply(parse_duration_to_ms)
    faults['fault_end_ms'] = faults['fault_start_ms'] + faults['fault_dur_ms']

    # Normalize keys
    faults['object'] = faults['object'].astype(str).str.strip().str.lower()
    faults['name'] = faults['name'].astype(str).str.strip()

    # Build interval list per entity (object,name)
    intervals = faults[['object','name','fault_start_ms','fault_end_ms']].copy()

    # Also build global intervals (any fault) for convenience
    global_intervals = intervals[['fault_start_ms','fault_end_ms']].values.tolist()

    intervals.to_csv(out_dir/'fault_intervals_entity.csv', index=False)
    pd.DataFrame(global_intervals, columns=['fault_start_ms','fault_end_ms']).to_csv(out_dir/'fault_intervals_global.csv', index=False)

    print('Wrote:')
    print(' -', out_dir/'fault_intervals_entity.csv')
    print(' -', out_dir/'fault_intervals_global.csv')
    print('Fault objects:', sorted(intervals['object'].unique().tolist()))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cfg', required=True)
    args = ap.parse_args()
    main(args.cfg)
