import argparse
from pathlib import Path
import numpy as np
import pandas as pd

try:
    import yaml
except ImportError:
    raise SystemExit('Missing dependency: pyyaml (pip install pyyaml)')

try:
    import requests
except ImportError:
    raise SystemExit('Missing dependency: requests (pip install requests)')

try:
    from sklearn.metrics import average_precision_score, f1_score, accuracy_score
except Exception:
    raise SystemExit('Missing dependency: scikit-learn (pip install scikit-learn)')


def load_cfg(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def call_endpoint(url: str, timeout_s: int, metrics: float, logs: float, traces: float) -> dict:
    payload = {'metrics': float(metrics), 'logs': float(logs), 'traces': float(traces)}
    r = requests.post(url, json=payload, timeout=timeout_s)
    r.raise_for_status()
    return r.json()


def choose_threshold(y_true: np.ndarray, scores: np.ndarray) -> float:
    # maximize F1 on val
    ts = np.unique(scores)
    if len(ts) > 500:
        ts = np.quantile(scores, np.linspace(0.0, 1.0, 501))
    best_t, best_f1 = 0.5, -1.0
    for t in ts:
        y_pred = (scores >= t).astype(int)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        if f1 > best_f1:
            best_f1, best_t = f1, float(t)
    return best_t


def eval_split(df: pd.DataFrame, score_col: str, thr: float) -> dict:
    y = df['y'].to_numpy().astype(int)
    s = df[score_col].to_numpy().astype(float)
    yhat = (s >= thr).astype(int)
    return {
        'n': int(len(df)),
        'pos': int(y.sum()),
        'ap': float(average_precision_score(y, s)) if len(np.unique(y)) > 1 else float('nan'),
        'f1': float(f1_score(y, yhat, zero_division=0)),
        'acc': float(accuracy_score(y, yhat)),
    }


def main(cfg_path: str):
    cfg = load_cfg(cfg_path)
    url = cfg['endpoint']['url']
    timeout_s = int(cfg['endpoint']['timeout_s'])

    out_dir = Path(cfg['train_ticket']['prepared_dir'])
    out_dir.mkdir(parents=True, exist_ok=True)

    samples = pd.read_csv(out_dir/'samples_60s.csv')
    samples = samples.reset_index(drop=True)

    # Call endpoint
    msif_scores, ple_scores, fusion_scores = [], [], []
    for i, r in samples.iterrows():
        resp = call_endpoint(url, timeout_s, r['metrics'], r['logs'], r['traces'])
        msif_scores.append(resp['details']['msif_score'])
        ple_scores.append(resp['details']['ple_score'])
        fusion_scores.append(resp['final_score'])

    samples['msif_score'] = np.array(msif_scores, dtype=float)
    samples['ple_score'] = np.array(ple_scores, dtype=float)
    samples['fusion_score'] = np.array(fusion_scores, dtype=float)

    pred_path = out_dir/'predictions_60s.csv'
    samples.to_csv(pred_path, index=False)

    # Thresholds from val only (per score type)
    val = samples[samples['split'] == 'val']
    if len(val) == 0:
        raise SystemExit('No val split rows; check cfg splits')

    thr = {
        'msif_score': choose_threshold(val['y'].to_numpy().astype(int), val['msif_score'].to_numpy().astype(float)),
        'ple_score': choose_threshold(val['y'].to_numpy().astype(int), val['ple_score'].to_numpy().astype(float)),
        'fusion_score': choose_threshold(val['y'].to_numpy().astype(int), val['fusion_score'].to_numpy().astype(float)),
    }

    rows = []
    for split in ['train','val','test']:
        part = samples[samples['split'] == split]
        if len(part) == 0:
            continue
        for score_col in ['msif_score','ple_score','fusion_score']:
            m = eval_split(part, score_col, thr[score_col])
            rows.append({
                'dataset': 'train_ticket',
                'split': split,
                'score': score_col,
                'threshold': thr[score_col],
                **m,
            })

    perf = pd.DataFrame(rows)
    perf_path = out_dir/'perf_table_binary.csv'
    perf.to_csv(perf_path, index=False)

    print('Wrote:')
    print(' -', pred_path)
    print(' -', perf_path)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cfg', required=True)
    args = ap.parse_args()
    main(args.cfg)
