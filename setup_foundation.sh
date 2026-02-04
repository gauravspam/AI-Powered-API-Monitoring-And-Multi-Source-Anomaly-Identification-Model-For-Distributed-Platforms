#!/bin/bash
# setup_foundation.sh - Create modular architecture

echo "🏗️  Setting up Foundation Phase structure..."

# 1. Modular Model Storage
mkdir -p ml-service/models/encoders/log     # BERT/Transformers
mkdir -p ml-service/models/encoders/metric  # LSTM-VAE
mkdir -p ml-service/models/encoders/trace   # GNN
mkdir -p ml-service/models/fusion           # Final Attention Layer

# 2. Data Lake (Raw Sources)
mkdir -p ml-service/data/raw/loghub         # For HDFS/Thunderbird
mkdir -p ml-service/data/raw/smd            # For Server Machine Dataset
mkdir -p ml-service/data/raw/deathstar      # For Trace Graphs

# 3. Training Scripts (Phase 1)
mkdir -p ml-service/training/pretrain
mkdir -p ml-service/training/fusion

# 4. Create placeholders
touch ml-service/data/raw/loghub/.keep
touch ml-service/models/encoders/log/.keep

echo "✅ Foundation structure created!"
tree ml-service/models ml-service/data
