import joblib
import pandas as pd
import os
from sklearn.ensemble import IsolationForest
from app.analytics.features import build_features

# Global cache to store the model once loaded
MODEL_CACHE = None

# Professional Path Handling: Works in Docker (/app/...) and Local Dev
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "../../analytics/models/fraud_model.pkl")

def detect_fraud(df):
    """
    Detects anomalies in payment patterns using a pre-trained Isolation Forest.
    Returns a DataFrame with 'id' and 'fraud_flag'.
    """
    global MODEL_CACHE

    if df.empty:
        return pd.DataFrame(columns=['id', 'fraud_flag'])

    # 1. Load Model with Cache Logic
    if MODEL_CACHE is None:
        if not os.path.exists(MODEL_PATH):
            print(f"⚠️ Warning: Model not found at {MODEL_PATH}. Check training_pipeline logs.")
            # Graceful fallback: mark everything as non-fraud so the UI doesn't break
            return pd.DataFrame({
                'id': df['id'] if 'id' in df.columns else range(len(df)), 
                'fraud_flag': 0
            })
        
        try:
            MODEL_CACHE = joblib.load(MODEL_PATH)
            print(f"✅ Model loaded into cache from {MODEL_PATH}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return pd.DataFrame({'id': df.get('id', range(len(df))), 'fraud_flag': 0})

    # 2. Feature Engineering
    # We call build_features to get the Z-scores and rolling windows
    X, _ = build_features(df)

    # 3. Feature Selection & Alignment
    # These MUST match the features used in your training_pipeline.py
    fraud_features = [
        'payment_ratio', 
        'amount_zscore', 
        'rolling_24h_cnt', 
        'is_night_txn'
    ]
    
    # Ensure all required features exist (fill with 0 if missing)
    for feature in fraud_features:
        if feature not in X.columns:
            X[feature] = 0

    X_fraud = X[fraud_features]

    # 4. Inference
    # IsolationForest returns -1 for outliers (fraud) and 1 for inliers (normal)
    try:
        predictions = MODEL_CACHE.predict(X_fraud)
        fraud_flags = [1 if x == -1 else 0 for x in predictions]
    except Exception as e:
        print(f"❌ Prediction Error: {e}")
        fraud_flags = [0] * len(df)

    # 5. Result Mapping
    if 'id' in df.columns:
        return pd.DataFrame({'id': df['id'], 'fraud_flag': fraud_flags})
    else:
        return pd.DataFrame({'fraud_flag': fraud_flags})

def train_fraud_model(X_train):
    """
    Trains the Isolation Forest model on engineered features.
    Contamination=0.05 assumes roughly 5% of your data might be anomalous.
    """
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X_train)
    return model