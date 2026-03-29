import pandas as pd
from app.analytics.data_loader import load_data
from app.analytics.features import build_features
from app.analytics.ml.fraud import detect_fraud
from app.analytics.ml.model_registry import save_model

def run_pipeline():
    
    df = load_data()
    
    if df.empty:
        print("⚠️ No data found in database. Skipping pipeline.")
        return

    X, y = build_features(df)

    
    fraud_features = [
        'payment_ratio', 
        'amount_zscore', 
        'rolling_24h_cnt', 
        'is_night_txn',
        'school_rel_mag' 
    ]
    
    
    available_features = [f for f in fraud_features if f in X.columns]
    X_fraud = X[available_features]

    from app.analytics.ml.fraud import train_fraud_model
    model = train_fraud_model(X_fraud)
    
    
    save_model(model)

    print("✅ Training pipeline complete: Model registered in /models")

if __name__ == "__main__":
    run_pipeline()