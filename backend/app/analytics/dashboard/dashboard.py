import sys
import os
import streamlit as st
import pandas as pd
from app.analytics.data_loader import load_data
from app.analytics.metrics import get_metrics
from app.analytics.ml.fraud import detect_fraud
import plotly.express as px
# 1. New import for the refresh component
from streamlit_autorefresh import st_autorefresh 

# Ensure base path is included
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# =========================
# Streamlit Page Config
# =========================
st.set_page_config(page_title="FlexiFees Analytics", layout="wide")
st.title("📊 FlexiFees Analytics Dashboard")

# =========================
# Sidebar - Refresh Rate
# =========================
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 5, 60, 10)

# 2. FIXED: Use the dedicated autorefresh component
# This handles the "rerun" logic internally based on the interval
st_autorefresh(interval=refresh_rate * 1000, key="dashboard_refresh")

# =========================
# LOAD DATA
# =========================
df = load_data()
metrics = get_metrics()

# Clean numeric columns
# Using .copy() ensures we don't get SettingWithCopy warnings
df = df.copy() 
df['balance'] = pd.to_numeric(df['balance'], errors='coerce').fillna(0)
df['paid_amount'] = pd.to_numeric(df['paid_amount'], errors='coerce').fillna(0)
df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce').fillna(0)

# =========================
# KPIs
# =========================
col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Collected", f"KES {metrics['total_collected']:,.2f}")
col2.metric("📉 Outstanding Balance", f"KES {metrics['total_outstanding']:,.2f}")
col3.metric("⏰ Late Payments", metrics["late_payments"])

st.divider()

# =========================
# PAYMENT DISTRIBUTION
# =========================
st.subheader("💡 Payment Distribution")
# Note: Ensure 'total_amount' and 'paid_amount' are in your df
fig = px.scatter(
    df,
    x="total_amount",
    y="paid_amount",
    title="Payments vs Total Amount",
    hover_data=["school_id"],
    labels={"total_amount": "Total Due", "paid_amount": "Amount Paid"}
)
fig.update_layout(template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# =========================
# BALANCE BY SCHOOL
# =========================
st.subheader("🏫 Outstanding Balance by School")
school_balance = (
    df.groupby("school_id")["balance"]
    .sum()
    .reset_index()
    .sort_values(by="balance", ascending=False)
)
fig2 = px.bar(
    school_balance,
    x="school_id",
    y="balance",
    title="Outstanding Balance by School",
    color="balance",
    color_continuous_scale="Reds"
)
fig2.update_layout(
    xaxis_title="School ID",
    yaxis_title="Total Outstanding Balance",
    template="plotly_white"
)
st.plotly_chart(fig2, use_container_width=True)

# =========================
# 🚨 FRAUD DETECTION
# =========================
# =========================
# 🚨 FRAUD DETECTION
# =========================
st.subheader("🚨 Fraud Detection Insights")

if df.empty:
    st.warning("No data available yet. Please make some payments.")
else:
    # 1. Get fraud results (this returns a small df with 'id' and 'fraud_flag')
    fraud_results = detect_fraud(df)

    if not fraud_results.empty and 'id' in fraud_results.columns:
        # 2. Safety Step: Ensure 'id' types match to avoid merge failures
        df['id'] = df['id'].astype(str)
        fraud_results['id'] = fraud_results['id'].astype(str)

        # 3. Merge results back into the main dataframe
        # We use 'left' so we keep all original data even if fraud_results is missing a row
        df_fraud = df.merge(fraud_results[['id', 'fraud_flag']], on="id", how="left")
        
        # 4. Fill NaNs (for any rows that didn't get a flag) and calculate count
        df_fraud['fraud_flag'] = df_fraud['fraud_flag'].fillna(0).astype(int)
        fraud_count = df_fraud['fraud_flag'].sum()

        # 5. UI Metrics
        f_col1, f_col2 = st.columns(2)
        f_col1.metric("⚠️ Fraudulent Transactions", int(fraud_count))
        f_col2.metric("✅ Normal Transactions", len(df_fraud) - int(fraud_count))

        # 6. Fraud Pie Chart
        # Mapping 0/1 to human-readable labels for the legend
        df_fraud['Status'] = df_fraud['fraud_flag'].map({0: 'Normal', 1: 'Suspicious'})
        
        fig3 = px.pie(
            df_fraud,
            names="Status",
            title="Fraud vs Normal Transactions",
            color="Status",
            color_discrete_map={'Normal': 'green', 'Suspicious': 'red'}
        )
        st.plotly_chart(fig3, use_container_width=True)

        # 7. Suspicious Table
        st.subheader("🔍 Flagged Suspicious Transactions")
        suspicious = df_fraud[df_fraud["fraud_flag"] == 1]
        
        if not suspicious.empty:
            # Show only relevant columns to keep the UI clean
            cols_to_show = ['id', 'school_id', 'total_amount', 'paid_amount', 'balance']
            st.dataframe(suspicious[cols_to_show].head(10), use_container_width=True)
        else:
            st.success("No suspicious transactions detected in this batch.")
    else:
        st.info("The fraud detection model needs more data to generate insights.")

st.divider()
# =========================
# TOP DEBTORS
# =========================
st.subheader("🚨 Top 5 Schools with Highest Debt")
st.table(school_balance.head(5)) # Table looks cleaner for small "Top X" lists