
import pandas as pd

import numpy as np

from pathlib import Path



def transform_kaggle_api_to_training_format(input_csv, output_csv):

    """Transform WITHOUT data leakage"""

    

    df = pd.read_csv(input_csv)

    transformed = pd.DataFrame()

    

    # Use ONLY original features, don't derive from labels

    transformed['response_time'] = df['inter_api_access_duration(sec)'] * 1000

    transformed['status_code'] = 200  # Default - no label info!

    transformed['request_count'] = df['sequence_length(count)']

    transformed['error_rate'] = 0.0  # Default - no label info!

    

    # Resource metrics from session data (legitimate)

    session_scale = df['num_sessions'] / df['num_sessions'].max()

    transformed['cpu_usage'] = 30 + session_scale * 60

    

    duration_scale = df['vsession_duration(min)'] / df['vsession_duration(min)'].max()

    transformed['memory_usage'] = 40 + duration_scale * 50

    

    transformed['network_io'] = df['api_access_uniqueness'] * df['num_unique_apis'] * 100

    transformed['disk_io'] = df['vsession_duration(min)'] * 10

    

    # Temporal features

    np.random.seed(42)

    transformed['hour_of_day'] = np.random.randint(0, 24, len(df))

    transformed['day_of_week'] = np.random.randint(0, 7, len(df))

    

    # Label (keep separate)

    transformed['is_anomaly'] = (df['classification'] == 'outlier').astype(int)

    

    # Clip outliers

    for col in ['response_time', 'disk_io', 'network_io']:

        transformed[col] = transformed[col].clip(upper=transformed[col].quantile(0.99))

    

    transformed.to_csv(output_csv, index=False)

    print(f"✅ Fixed dataset saved to: {output_csv}")

    return transformed



if __name__ == '__main__':

    transform_kaggle_api_to_training_format(

        'kaggle_api_dataset/supervised_dataset.csv',

        'data/training_data_kaggle_api_fixed.csv'

    )

