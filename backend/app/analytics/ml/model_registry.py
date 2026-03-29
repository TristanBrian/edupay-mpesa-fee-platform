import os
import joblib
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../models"))

def save_model(model, model_name="fraud_model"):
    """
    Saves a trained machine learning model with versioning and metadata.
    Updates the 'latest' alias for production inference.
    """
    
    os.makedirs(MODELS_DIR, exist_ok=True)

    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    versioned_filename = f"{model_name}_{timestamp}.pkl"
    versioned_path = os.path.join(MODELS_DIR, versioned_filename)
    
    latest_path = os.path.join(MODELS_DIR, f"{model_name}.pkl")

    joblib.dump(model, versioned_path)
    joblib.dump(model, latest_path)

    
    metadata = {
        "train_date": datetime.now().isoformat(),
        "version": versioned_filename,
        "model_type": type(model).__name__,
        "expected_features": [
            "payment_ratio", 
            "amount_zscore", 
            "rolling_24h_cnt", 
            "is_night_txn"
        ]
    }
    
    metadata_path = os.path.join(MODELS_DIR, f"{model_name}_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)

    print(f"📦 Model saved: {versioned_filename}")
    print(f"🔗 Production alias updated: {latest_path}")
    print(f"📄 Metadata updated: {metadata_path}")

def load_latest_model(model_name="fraud_model"):
    """
    Helper function to load the most recent model.
    (Currently used by fraud.py, but good to have centralized here).
    """
    latest_path = os.path.join(MODELS_DIR, f"{model_name}.pkl")
    if os.path.exists(latest_path):
        return joblib.load(latest_path)
    else:
        raise FileNotFoundError(f"No model found at {latest_path}. Run the training pipeline.")