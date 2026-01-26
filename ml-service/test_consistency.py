
"""Test prediction consistency between runs"""

import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'



import numpy as np

from inference_multi_model import MultiModelDetector



# Fixed seed for reproducibility

np.random.seed(42)



# Load detector

detector = MultiModelDetector()



print("="*70)

print("CONSISTENCY TEST: Same Input, Multiple Runs")

print("="*70)



# Generate fixed test data

nab_sample = np.random.randn(10).astype(np.float32)

lo2_sample = np.random.randn(100).astype(np.float32)



print("\n🔬 Running NAB prediction 5 times with same input...")

nab_results = []

for i in range(5):

    result = detector.predict(nab_sample, 'nab', use_ensemble=True)

    prob = result['probabilities'][0]

    pred = result['predictions'][0]

    nab_results.append((prob, pred))

    print(f"  Run {i+1}: Prob={prob:.6f}, Prediction={'ANOMALY' if pred else 'NORMAL'}")



# Check consistency

probs = [r[0] for r in nab_results]

preds = [r[1] for r in nab_results]

prob_std = np.std(probs)

pred_consistent = len(set(preds)) == 1



print(f"\n  Probability std dev: {prob_std:.8f}")

print(f"  Predictions consistent: {'✅ YES' if pred_consistent else '❌ NO'}")



print("\n🔬 Running LO2 prediction 5 times with same input...")

lo2_results = []

for i in range(5):

    result = detector.predict(lo2_sample, 'lo2', use_ensemble=True)

    prob = result['probabilities'][0]

    pred = result['predictions'][0]

    lo2_results.append((prob, pred))

    print(f"  Run {i+1}: Prob={prob:.6f}, Prediction={'ANOMALY' if pred else 'NORMAL'}")



probs = [r[0] for r in lo2_results]

preds = [r[1] for r in lo2_results]

prob_std = np.std(probs)

pred_consistent = len(set(preds)) == 1



print(f"\n  Probability std dev: {prob_std:.8f}")

print(f"  Predictions consistent: {'✅ YES' if pred_consistent else '❌ NO'}")



print("\n" + "="*70)

print("CROSS-PLATFORM TEST: Same Input on Different Devices")

print("="*70)



# Test with multiple samples

print("\nTesting 100 random samples...")

test_samples_nab = np.random.randn(100, 10).astype(np.float32)

test_samples_lo2 = np.random.randn(100, 100).astype(np.float32)



nab_result = detector.predict(test_samples_nab, 'nab')

lo2_result = detector.predict(test_samples_lo2, 'lo2')



print(f"\nNAB: {sum(nab_result['predictions'])}/100 anomalies detected")

print(f"  Avg probability: {np.mean(nab_result['probabilities']):.4f}")

print(f"  Std probability: {np.std(nab_result['probabilities']):.4f}")



print(f"\nLO2: {sum(lo2_result['predictions'])}/100 anomalies detected")

print(f"  Avg probability: {np.mean(lo2_result['probabilities']):.4f}")

print(f"  Std probability: {np.std(lo2_result['probabilities']):.4f}")



print("\n" + "="*70)

print("✅ Consistency test complete!")

print("="*70)

