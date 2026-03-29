from app.analytics.data_loader import load_data
from app.analytics.features import build_features
from app.analytics.ml.train import train_model
from app.analytics.ml.model_registry import save_model

def run_pipeline():
    df = load_data()
    X, y = build_features(df)

    model = train_model(X, y)
    save_model(model)

    print("✅ Training pipeline complete")

if __name__ == "__main__":
    run_pipeline()