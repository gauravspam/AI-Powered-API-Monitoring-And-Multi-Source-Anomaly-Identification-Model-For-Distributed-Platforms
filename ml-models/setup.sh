echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Creating model directories..."
mkdir -p models/saved

echo "Training models..."
python train_models.py

echo "Setup complete! Starting API server..."
python api_server.py
