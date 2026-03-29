from sklearn.ensemble import IsolationForest
import pandas as pd

def detect_fraud(df):
    """
    Detects anomalies in payment patterns using Isolation Forest.
    Returns a DataFrame with 'id' and 'fraud_flag'.
    """
    # 1. Handle empty or too small datasets (IsolationForest needs multiple samples)
    if df.empty or len(df) < 2:
        # Create an empty result with the correct structure
        return pd.DataFrame(columns=['id', 'fraud_flag'])

    # 2. Work on a copy to avoid SettingWithCopy warnings in the dashboard
    data = df.copy()

    # 3. Feature Selection
    # We use 'paid_amount' and 'total_amount' to find outliers 
    # (e.g., payments much higher than the total due)
    features = data[['paid_amount', 'total_amount']].fillna(0)

    # 4. Model Training
    # contamination=0.05 means we expect ~5% of transactions to be outliers
    model = IsolationForest(contamination=0.05, random_state=42)
    
    # fit_predict returns 1 for normal, -1 for anomalies
    predictions = model.fit_predict(features)

    # 5. Format results
    # Convert: -1 (anomaly) → 1 (fraud_flag), 1 (normal) → 0 (no fraud)
    data['fraud_flag'] = [1 if x == -1 else 0 for x in predictions]

    # 6. Return only the essential columns for merging
    if 'id' in data.columns:
        return data[['id', 'fraud_flag']]
    else:
        # Fallback if 'id' is missing: return a flag for every row
        return pd.DataFrame({'fraud_flag': data['fraud_flag']})