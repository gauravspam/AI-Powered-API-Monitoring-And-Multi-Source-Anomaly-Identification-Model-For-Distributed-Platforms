
"""Validate LO2 models performance"""

import json



print("="*70)

print("LO2 MODELS STATUS CHECK")

print("="*70)



# Load metadata

with open('models/lo2/metadata.json') as f:

    meta = json.load(f)



print(f"\n📊 LO2 Model Metadata:")

print(f"  Dataset: {meta.get('dataset', 'Unknown')}")

print(f"  Training Date: {meta.get('training_date', 'Unknown')}")

print(f"  Dataset Size: {meta.get('dataset_size', 'Unknown'):,}")

print(f"  Features: {meta.get('n_features', 'Unknown')}")



if 'msif_lstm' in meta:

    print(f"\n🔵 LO2 MSIF-LSTM:")

    print(f"  F1:        {meta['msif_lstm'].get('f1_score', 0):.4f}")

    print(f"  Precision: {meta['msif_lstm'].get('precision', 0):.4f}")

    print(f"  Recall:    {meta['msif_lstm'].get('recall', 0):.4f}")

    print(f"  AUC:       {meta['msif_lstm'].get('auc', 0):.4f}")

    

    f1 = meta['msif_lstm'].get('f1_score', 0)

    if f1 > 0.95:

        print("  Status: ✅ EXCELLENT")

    elif f1 > 0.90:

        print("  Status: ✅ GOOD")

    elif f1 > 0.80:

        print("  Status: ⚠️ MODERATE")

    else:

        print("  Status: ❌ NEEDS IMPROVEMENT")



if 'ple_gru' in meta:

    print(f"\n🟢 LO2 PLE-GRU:")

    print(f"  F1:        {meta['ple_gru'].get('f1_score', 0):.4f}")

    print(f"  Precision: {meta['ple_gru'].get('precision', 0):.4f}")

    print(f"  Recall:    {meta['ple_gru'].get('recall', 0):.4f}")

    print(f"  AUC:       {meta['ple_gru'].get('auc', 0):.4f}")

    

    f1 = meta['ple_gru'].get('f1_score', 0)

    if f1 > 0.95:

        print("  Status: ✅ EXCELLENT")

    elif f1 > 0.90:

        print("  Status: ✅ GOOD")

    elif f1 > 0.80:

        print("  Status: ⚠️ MODERATE")

    else:

        print("  Status: ❌ NEEDS IMPROVEMENT")



print("\n" + "="*70)

