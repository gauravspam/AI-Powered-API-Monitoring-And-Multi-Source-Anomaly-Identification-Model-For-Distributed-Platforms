
"""

Sequence generator for temporal models



Converts flat feature arrays into sliding window sequences:

  Input:  (8000, 10) - 8000 samples, 10 features each

  Output: (7991, 10, 10) - 7991 sequences, 10 timesteps, 10 features



Usage:

  X_seq, y_seq = create_sequences(X_train, y_train, window_size=10)

"""



import numpy as np

from typing import Tuple

import logging



logger = logging.getLogger(__name__)



def create_sequences(X: np.ndarray,

                     y: np.ndarray,

                     window_size: int = 10,

                     stride: int = 1) -> Tuple[np.ndarray, np.ndarray]:

    """

    Convert flat features to sliding window sequences



    Args:

        X: Feature array (n_samples, n_features)

        y: Labels (n_samples,)

        window_size: Lookback timesteps (default: 10)

        stride: Step size for sliding window (default: 1)



    Returns:

        X_seq: (n_sequences, window_size, n_features)

        y_seq: (n_sequences,) - label of last timestep in each window

    """

    if X.shape[0] != y.shape[0]:

        raise ValueError(f"X and y length mismatch: {X.shape[0]} vs {y.shape[0]}")



    if window_size > X.shape[0]:

        raise ValueError(

            f"Window size {window_size} larger than dataset {X.shape[0]}"

        )



    n_samples = X.shape[0]

    n_features = X.shape[1]



    # Calculate number of sequences

    n_sequences = (n_samples - window_size) // stride + 1



    X_seq = np.zeros((n_sequences, window_size, n_features), dtype=np.float32)

    y_seq = np.zeros(n_sequences, dtype=np.int32)



    for i in range(n_sequences):

        start_idx = i * stride

        end_idx = start_idx + window_size



        X_seq[i] = X[start_idx:end_idx]

        y_seq[i] = y[end_idx - 1]  # Label of last timestep



    print(f"✅ Created sequences:")

    print(f"   Original: {X.shape} → Sequences: {X_seq.shape}")

    print(f"   Window size: {window_size}, Stride: {stride}")

    print(f"   Lost {n_samples - n_sequences} samples due to windowing")



    return X_seq, y_seq





def validate_sequence_distribution(X_seq: np.ndarray,

                                    y_seq: np.ndarray) -> dict:

    """

    Validate sequence data quality



    Returns:

        Dict with statistics

    """

    stats = {

        'n_sequences': X_seq.shape[0],

        'window_size': X_seq.shape[1],

        'n_features': X_seq.shape[2],

        'anomaly_rate': float(np.mean(y_seq)),

        'mean_values': float(np.mean(X_seq)),

        'std_values': float(np.std(X_seq)),

        'nan_count': int(np.sum(np.isnan(X_seq))),

        'inf_count': int(np.sum(np.isinf(X_seq)))

    }



    print("="*60)

    print("SEQUENCE DATA VALIDATION")

    print("="*60)

    print(f"Sequences: {stats['n_sequences']:,}")

    print(f"Shape: ({stats['window_size']} timesteps, {stats['n_features']} features)")

    print(f"Anomaly rate: {stats['anomaly_rate']:.2%}")

    print(f"Feature statistics:")

    print(f"  Mean: {stats['mean_values']:.4f}")

    print(f"  Std:  {stats['std_values']:.4f}")



    if stats['nan_count'] > 0:

        print(f"⚠️ Found {stats['nan_count']} NaN values!")

    if stats['inf_count'] > 0:

        print(f"⚠️ Found {stats['inf_count']} Inf values!")



    print("="*60)



    return stats
