
import pandas as pd

import numpy as np



# Load transformed data

df = pd.read_csv('data/training_data_kaggle_api.csv')



print(f"Original shape: {df.shape}")

print(f"\nBefore clipping:")

print(df[['response_time', 'disk_io']].describe())



# Clip extreme outliers to 99th percentile

df['response_time'] = df['response_time'].clip(upper=df['response_time'].quantile(0.99))

df['disk_io'] = df['disk_io'].clip(upper=df['disk_io'].quantile(0.99))

df['network_io'] = df['network_io'].clip(upper=df['network_io'].quantile(0.99))



print(f"\nAfter clipping:")

print(df[['response_time', 'disk_io']].describe())



# Save clipped version

df.to_csv('data/training_data_kaggle_api_clipped.csv', index=False)

print(f"\n✅ Saved clipped data to: data/training_data_kaggle_api_clipped.csv")

