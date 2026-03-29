from app.analytics.data_loader import load_data

def get_metrics():
    df = load_data()

    total_collected = df['paid_amount'].sum()
    total_outstanding = df['balance'].sum()

    late_payments = df[df['balance'] > 0].shape[0]

    return {
        "total_collected": float(total_collected),
        "total_outstanding": float(total_outstanding),
        "late_payments": int(late_payments)
    }