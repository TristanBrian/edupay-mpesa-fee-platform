import sys
import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit_autorefresh import st_autorefresh 

# Import your custom modules
from app.analytics.data_loader import load_data
from app.analytics.metrics import get_metrics
from app.analytics.ml.fraud import detect_fraud

# Ensure base path is included for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# =========================
# Streamlit Page Config
# =========================
st.set_page_config(page_title="FlexiFees Analytics & ML", layout="wide", page_icon="📊")
st.title("📊 FlexiFees Analytics & Fraud Monitor")

# =========================
# Sidebar - Refresh Rate
# =========================
st.sidebar.header("Settings")
refresh_rate = st.sidebar.slider("Auto-Refresh (seconds)", 5, 60, 10)
st_autorefresh(interval=refresh_rate * 1000, key="dashboard_refresh")

# =========================
# LOAD DATA
# =========================
df = load_data()
metrics = get_metrics()

# Clean numeric columns using vectorized operations
df = df.copy()
numeric_cols = ['balance', 'paid_amount', 'total_amount']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# =========================
# TOP LEVEL KPIs
# =========================
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("💰 Total Collected", f"KES {metrics['total_collected']:,.2f}")
with col2:
    st.metric("📉 Outstanding Balance", f"KES {metrics['total_outstanding']:,.2f}")
with col3:
    st.metric("⏰ Late Payments", metrics["late_payments"])

st.divider()

# =========================
# DATA VISUALIZATION
# =========================
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("💡 Payment Distribution")
    fig = px.scatter(
        df, x="total_amount", y="paid_amount", 
        title="Payments vs Total Due",
        color="balance", color_continuous_scale="Viridis",
        hover_data=["student_id", "school_id"]
    )
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.subheader("🏫 Balance by School")
    school_balance = df.groupby("school_id")["balance"].sum().reset_index().sort_values("balance", ascending=False)
    fig2 = px.bar(school_balance, x="school_id", y="balance", color="balance", color_continuous_scale="Reds")
    st.plotly_chart(fig2, use_container_width=True)

# =========================
# 🚨 FRAUD DETECTION (ML LAYER)
# =========================
st.divider()
st.subheader("🚨 Machine Learning: Fraud Detection Insights")

if df.empty:
    st.warning("Waiting for transaction data...")
else:
    # Inference Call: Pass the DF to the ML engine
    fraud_results = detect_fraud(df)

    if not fraud_results.empty:
        # Merge ML results back to main display DF
        df['id'] = df['id'].astype(str)
        fraud_results['id'] = fraud_results['id'].astype(str)
        df_fraud = df.merge(fraud_results[['id', 'fraud_flag']], on="id", how="left")
        df_fraud['fraud_flag'] = df_fraud['fraud_flag'].fillna(0).astype(int)
        
        fraud_count = df_fraud['fraud_flag'].sum()
        risk_rate = (fraud_count / len(df_fraud)) * 100

        # ML Specific Metrics
        f_col1, f_col2, f_col3 = st.columns(3)
        f_col1.metric("⚠️ Flagged Suspicious", int(fraud_count))
        f_col2.metric("✅ Verified Normal", len(df_fraud) - int(fraud_count))
        f_col3.metric("📈 Anomaly Rate", f"{risk_rate:.1f}%", delta=f"{risk_rate:.1f}%", delta_color="inverse")

        # Visualizing Anomaly Distribution
        df_fraud['Status'] = df_fraud['fraud_flag'].map({0: 'Normal', 1: 'Suspicious'})
        fig_pie = px.pie(
            df_fraud, names="Status", 
            color="Status", 
            color_discrete_map={'Normal': '#2ecc71', 'Suspicious': '#e74c3c'},
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        # Actionable Insights Table
        st.subheader("🔍 Suspicious Transaction Details")
        suspicious = df_fraud[df_fraud["fraud_flag"] == 1].copy()
        
        if not suspicious.empty:
            # Add a mock "Reason" for UX - in a real RAG system, 
            # we'd ask the AI to explain the Anomaly Score here.
            suspicious['Risk Reason'] = np.where(
                suspicious['paid_amount'] > suspicious['total_amount'], 
                "Overpayment Anomaly", "Behavioral Outlier"
            )
            st.dataframe(
                suspicious[['id', 'school_id', 'paid_amount', 'balance', 'Risk Reason']], 
                use_container_width=True
            )
        else:
            st.success("No behavioral anomalies detected in the current dataset.")
    else:
        st.info("🔄 ML Model is initializing or refreshing...")

# =========================
# FOOTER - TOP DEBTORS
# =========================
st.divider()
st.subheader("🚨 Top 5 Schools with Highest Debt")
st.table(school_balance.head(5))