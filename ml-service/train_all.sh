
#!/bin/bash



echo "═══════════════════════════════════════════════════════════════════════"

echo "    MULTI-DATASET MODEL TRAINING SUITE (Universal)"

echo "═══════════════════════════════════════════════════════════════════════"



echo ""

echo "Available Datasets:"

echo "  1) IBM     - 34M  (150k samples) - Best for production      [~25 min]"

echo "  2) LO2     - 6.7M (30k samples)  - Balanced performance     [~8 min]"

echo "  3) NAB     - 464K (2k samples)   - Benchmark/research       [~3 min]"

echo "  4) Kaggle  - 174K (1k samples)   - Quick prototyping        [~2 min]"

echo "  5) ALL     - Train on all datasets sequentially             [~40 min]"

echo ""

read -p "Select dataset [1-5]: " choice



case $choice in

    1)

        echo "🚀 Training on IBM dataset..."

        python training_scripts/train_universal.py data/training_data_ibm_improved.csv ibm

        ;;

    2)

        echo "🚀 Training on LO2 dataset..."

        python training_scripts/train_universal.py data/training_data_lo2.csv lo2

        ;;

    3)

        echo "🚀 Training on NAB dataset..."

        python training_scripts/train_universal.py data/training_data_nab_aws.csv nab

        ;;

    4)

        echo "🚀 Training on Kaggle dataset..."

        python training_scripts/train_universal.py data/training_data_kaggle_api_fixed.csv kaggle

        ;;

    5)

        echo "🚀 Training on ALL datasets..."

        echo ""

        echo "[1/4] Training IBM..."

        python training_scripts/train_universal.py data/training_data_ibm_improved.csv ibm

        echo ""

        echo "[2/4] Training LO2..."

        python training_scripts/train_universal.py data/training_data_lo2.csv lo2

        echo ""

        echo "[3/4] Training NAB..."

        python training_scripts/train_universal.py data/training_data_nab_aws.csv nab

        echo ""

        echo "[4/4] Training Kaggle..."

        python training_scripts/train_universal.py data/training_data_kaggle_api_fixed.csv kaggle

        echo ""

        echo "✅ ALL DATASETS TRAINED!"

        ;;

    *)

        echo "❌ Invalid choice"

        exit 1

        ;;

esac



echo ""

echo "═══════════════════════════════════════════════════════════════════════"

echo "    TRAINING COMPLETE!"

echo "═══════════════════════════════════════════════════════════════════════"

echo ""

echo "📁 Trained models:"

ls -d models/*/ 2>/dev/null | while read dir; do

    if [ -f "$dir/metadata.json" ]; then

        echo "   ✅ $dir"

    fi

done

