#!/bin/bash
set -e

echo "------------------------------------------------"
echo "🚀 Step 1: Initializing DB & Training Fraud Model"
echo "------------------------------------------------"

python3 -m app.analytics.pipelines.training_pipeline

echo "------------------------------------------------"
echo "🌐 Step 2: Starting FlexiFees FastAPI Server"
echo "------------------------------------------------"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
