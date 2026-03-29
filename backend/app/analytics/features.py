import pandas as pd
from datetime import datetime

def build_features(df):
    df['due_date'] = pd.to_datetime(df['due_date'])
    df['created_at'] = pd.to_datetime(df['created_at'])

    df['days_to_due'] = (df['due_date'] - df['created_at']).dt.days
    df['payment_ratio'] = df['paid_amount'] / df['total_amount']
    df['hour'] = df['created_at'].dt.hour

    today = datetime.now()
    df['late_payment'] = (df['balance'] > 0) & (df['due_date'] < today)

    df = df.fillna(0)

    X = df[['total_amount', 'paid_amount', 'balance', 'days_to_due', 'hour']]
    y = df['late_payment']

    return X, y