"""Streamlit dashboard with KPIs, A/B tests, and churn insights."""
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text
from src.churn_model.features import build_features
from src.utils.db import get_engine

st.set_page_config(page_title="E-commerce Growth Intelligence", layout="wide")
st.title("📈 E-commerce Growth Intelligence Platform")

engine = get_engine()


def run_query(query: str) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


tab1, tab2, tab3 = st.tabs(["KPI Dashboard", "A/B Test Results", "Churn Predictions"])

with tab1:
    st.subheader("Business KPIs")
    kpi = run_query(
        """
        SELECT COUNT(DISTINCT order_id) AS total_orders,
               ROUND(SUM(payment_value), 2) AS total_revenue,
               ROUND(AVG(payment_value), 2) AS avg_payment
        FROM order_payments
        """
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Orders", int(kpi['total_orders'][0]))
    c2.metric("Total Revenue", f"R$ {kpi['total_revenue'][0]:,.2f}")
    c3.metric("Avg Payment", f"R$ {kpi['avg_payment'][0]:,.2f}")

    revenue_by_month = run_query(
        """
        SELECT DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
               SUM(op.payment_value) AS revenue
        FROM orders o
        JOIN order_payments op ON o.order_id = op.order_id
        GROUP BY 1
        ORDER BY 1
        """
    )
    fig = px.line(revenue_by_month, x="month", y="revenue", title="Monthly Revenue")
    st.plotly_chart(fig, use_container_width=True)

    cohort = run_query(
        """
        WITH cohorts AS (
            SELECT c.customer_unique_id,
                   DATE_TRUNC('month', MIN(o.order_purchase_timestamp)) AS cohort_month
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            GROUP BY c.customer_unique_id
        ), activity AS (
            SELECT c.customer_unique_id,
                   DATE_TRUNC('month', o.order_purchase_timestamp) AS order_month
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
        )
        SELECT co.cohort_month,
               EXTRACT(MONTH FROM AGE(a.order_month, co.cohort_month)) AS month_no,
               COUNT(DISTINCT a.customer_unique_id) AS active_customers
        FROM cohorts co
        JOIN activity a ON co.customer_unique_id = a.customer_unique_id
        GROUP BY 1, 2
        HAVING EXTRACT(MONTH FROM AGE(a.order_month, co.cohort_month)) BETWEEN 0 AND 6
        ORDER BY 1, 2
        """
    )
    cohort_fig = px.line(cohort, x="month_no", y="active_customers", color="cohort_month", title="Cohort Curves")
    st.plotly_chart(cohort_fig, use_container_width=True)

with tab2:
    st.subheader("A/B Test Results")
    ab_df = run_query("SELECT * FROM ab_test_results ORDER BY created_at DESC")
    st.dataframe(ab_df, use_container_width=True)
    if not ab_df.empty:
        ab_plot = px.bar(
            ab_df,
            x="experiment_name",
            y=["control_value", "treatment_value"],
            barmode="group",
            title="Control vs Treatment Metrics",
        )
        st.plotly_chart(ab_plot, use_container_width=True)

with tab3:
    st.subheader("Churn Prediction Snapshot")
    churn_df = build_features()
    st.write("Training data sample:")
    st.dataframe(churn_df.head(20), use_container_width=True)
    churn_plot = px.histogram(churn_df, x="recency_days", color="churn_label", barmode="overlay")
    st.plotly_chart(churn_plot, use_container_width=True)
