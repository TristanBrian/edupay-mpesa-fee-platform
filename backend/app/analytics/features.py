import pandas as pd
import numpy as np
from datetime import datetime

def build_features(df):
    """
    High-performance feature engineering for Analytics and ML.
    Fixes the 'on' column ValueError by using a sorted datetime index for rolling windows.
    """
    if df.empty:
        return pd.DataFrame(), pd.Series()

    # 1. Performance: Parse dates and sort for rolling window accuracy
    df['due_date'] = pd.to_datetime(df['due_date'], cache=True)
    df['created_at'] = pd.to_datetime(df['created_at'], cache=True)
    df = df.sort_values('created_at')
    
    today = datetime.now()

    # 2. Vectorized Analytics (Original Logic)
    df['days_to_due'] = (df['due_date'] - df['created_at']).dt.days
    df['payment_ratio'] = df['paid_amount'] / (df['total_amount'] + 1e-5)
    df['hour'] = df['created_at'].dt.hour
    
    # Target variable (y) - cast to int for ML compatibility
    df['late_payment'] = ((df['balance'] > 0) & (df['due_date'] < today)).astype(int)

    # 3. Behavioral ML Features (Fraud Logic)
    # Z-Score: How much does this amount deviate from the student's history?
    group = df.groupby('student_id')['paid_amount']
    df['student_avg'] = group.transform('mean')
    df['student_std'] = group.transform('std').fillna(0)
    
    df['amount_zscore'] = np.where(
        df['student_std'] > 0, 
        (df['paid_amount'] - df['student_avg']) / (df['student_std'] + 1e-5), 
        0
    )

    # Velocity FIX: Use the index for rolling to avoid 'on' column errors
    # Setting the index to created_at allows .rolling('24h') to work implicitly
    temp_df = df.set_index('created_at')
    df['rolling_24h_cnt'] = (
        temp_df.groupby('student_id')
        .rolling('24h')['paid_amount'] # Use any numeric column to count
        .count()
        .reset_index(level=0, drop=True)
        .values
    )

    # Night-time Anomaly (11 PM - 5 AM)
    df['is_night_txn'] = np.where((df['hour'] < 5) | (df['hour'] > 23), 1, 0)

    # School-level relative magnitude
    school_avg = df.groupby('school_id')['paid_amount'].transform('mean')
    df['school_rel_mag'] = df['paid_amount'] / (school_avg + 1e-5)

    # 4. Final Cleanup
    df = df.fillna(0)

    # 5. Return X and y (Maintaining the requested interface)
    feature_columns = [
        'total_amount', 'paid_amount', 'balance', 'days_to_due', 'hour',
        'payment_ratio', 'amount_zscore', 'rolling_24h_cnt', 'is_night_txn', 'school_rel_mag'
    ]
    
    X = df[feature_columns]
    y = df['late_payment']

    return X, y