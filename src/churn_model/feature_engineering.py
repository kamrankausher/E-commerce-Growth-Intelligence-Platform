"""
Feature engineering for churn prediction — LEAK-FREE temporal split.

Uses a proper temporal split to prevent data leakage:
  - Observation window: all orders BEFORE cutoff_date
  - Prediction window: last 90 days of dataset
  - Features computed from observation window ONLY
  - Churn label: 1 if customer made NO purchase in prediction window

Features created:
  - Frequency (total orders in observation window)
  - Monetary (total spend)
  - Average order value
  - Average review score
  - Avg installments, payment diversity
  - Tenure (days between first and last purchase)
  - Avg days between orders (temporal pattern)
  - State (geographic feature)
"""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)

CHURN_WINDOW_DAYS = 90  # prediction window length


def build_features_from_csv(data_dir: str) -> pd.DataFrame:
    """
    Build customer-level features using temporal split (no data leakage).

    The dataset is split temporally:
      - Observation: orders before (max_date - CHURN_WINDOW_DAYS)
      - Prediction:  orders after that cutoff
      - Churn = 1 if customer has NO orders in the prediction window

    Returns:
        DataFrame with engineered features and churn label.
    """
    logger.info("Building features from CSV files in %s...", data_dir)

    customers = pd.read_csv(os.path.join(data_dir, "olist_customers_dataset.csv"))
    orders = pd.read_csv(os.path.join(data_dir, "olist_orders_dataset.csv"))
    payments = pd.read_csv(os.path.join(data_dir, "olist_order_payments_dataset.csv"))
    reviews = pd.read_csv(os.path.join(data_dir, "olist_order_reviews_dataset.csv"))

    orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
    delivered = orders[orders["order_status"] == "delivered"].copy()

    # ─── Temporal split ───
    reference_date = delivered["order_purchase_timestamp"].max()
    cutoff_date = reference_date - pd.Timedelta(days=CHURN_WINDOW_DAYS)

    obs_orders = delivered[delivered["order_purchase_timestamp"] <= cutoff_date].copy()
    pred_orders = delivered[delivered["order_purchase_timestamp"] > cutoff_date].copy()

    logger.info("Temporal split — Observation: %d orders, Prediction: %d orders",
                len(obs_orders), len(pred_orders))

    # Merge customer info into observation orders
    obs_merged = obs_orders.merge(customers, on="customer_id", how="left")

    # Only customers who have at least 1 order in observation window
    if obs_merged.empty:
        raise ValueError("No orders in observation window — check data dates")

    # ─── Aggregated features from OBSERVATION window only ───
    agg = obs_merged.groupby("customer_unique_id").agg(
        customer_state=("customer_state", "first"),
        frequency=("order_id", "nunique"),
        last_obs_purchase=("order_purchase_timestamp", "max"),
        first_purchase=("order_purchase_timestamp", "min"),
    ).reset_index()

    # Payment features (observation window only)
    obs_order_ids = obs_orders[["order_id"]].drop_duplicates()
    pay_merged = obs_order_ids.merge(payments, on="order_id", how="left")
    pay_merged = pay_merged.merge(
        obs_merged[["order_id", "customer_unique_id"]].drop_duplicates(),
        on="order_id", how="left"
    )
    pay_agg = pay_merged.groupby("customer_unique_id").agg(
        monetary=("payment_value", "sum"),
        avg_order_value=("payment_value", "mean"),
        avg_installments=("payment_installments", "mean"),
        payment_type_count=("payment_type", "nunique"),
    ).reset_index()

    # Review features (observation window only)
    rev_merged = obs_order_ids.merge(reviews, on="order_id", how="left")
    rev_merged = rev_merged.merge(
        obs_merged[["order_id", "customer_unique_id"]].drop_duplicates(),
        on="order_id", how="left"
    )
    rev_agg = rev_merged.groupby("customer_unique_id").agg(
        avg_review_score=("review_score", "mean"),
        review_count=("review_score", "count"),
    ).reset_index()

    # Combine all features
    df = agg.merge(pay_agg, on="customer_unique_id", how="left")
    df = df.merge(rev_agg, on="customer_unique_id", how="left")

    # Fill missing reviews
    df["avg_review_score"] = df["avg_review_score"].fillna(3.0)
    df["review_count"] = df["review_count"].fillna(0)

    # ─── Derived features (from observation window only) ───
    df["last_obs_purchase"] = pd.to_datetime(df["last_obs_purchase"])
    df["first_purchase"] = pd.to_datetime(df["first_purchase"])

    # Tenure: span of customer activity in observation window
    df["tenure_days"] = (df["last_obs_purchase"] - df["first_purchase"]).dt.days

    # Average days between orders (temporal regularity signal — NOT leaking)
    df["avg_days_between_orders"] = df.apply(
        lambda r: r["tenure_days"] / (r["frequency"] - 1) if r["frequency"] > 1 else 365.0,
        axis=1
    )

    # ─── Churn label (from PREDICTION window) ───
    pred_merged = pred_orders.merge(customers, on="customer_id", how="left")
    active_in_pred = set(pred_merged["customer_unique_id"].unique())
    df["is_churned"] = (~df["customer_unique_id"].isin(active_in_pred)).astype(int)

    # Encode state
    df["state_encoded"] = df["customer_state"].astype("category").cat.codes

    # Final feature set — NO recency_days (that was the leakage source)
    feature_cols = [
        "frequency", "monetary", "avg_order_value", "avg_installments",
        "payment_type_count", "avg_review_score", "review_count",
        "tenure_days", "avg_days_between_orders", "state_encoded", "is_churned"
    ]
    result = df[feature_cols].copy()
    result = result.dropna()

    churn_rate = result["is_churned"].mean() * 100
    logger.info(
        "Features built: %d customers, churn rate=%.1f%% (target: 15-35%%)",
        len(result), churn_rate
    )
    if churn_rate < 10 or churn_rate > 50:
        logger.warning("⚠️ Churn rate %.1f%% is outside realistic range!", churn_rate)

    return result


if __name__ == "__main__":
    from config import DATA_DIR
    df = build_features_from_csv(str(DATA_DIR))
    print(df.head(10))
    print(f"\nShape: {df.shape}")
    print(f"Churn rate: {df['is_churned'].mean():.2%}")
    print(f"Features: {[c for c in df.columns if c != 'is_churned']}")
