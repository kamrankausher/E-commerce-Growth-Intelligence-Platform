"""
Feature engineering for churn prediction.

Builds customer-level features from the Olist CSV dataset using Pandas.
Features created:
  - Recency (days since last purchase)
  - Frequency (total orders)
  - Monetary (total spend)
  - Average order value
  - Average review score
  - Average delivery time
  - Payment diversity
  - State (geographic feature)
  - Churn label (1 if no purchase in last 90 days of dataset)
"""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_features_from_csv(data_dir: str) -> pd.DataFrame:
    """
    Build customer-level features from CSV files (no database required).

    Args:
        data_dir: Path to directory containing Olist CSV files.

    Returns:
        DataFrame with engineered features and churn label.
    """
    logger.info("Building features from CSV files in %s...", data_dir)

    customers = pd.read_csv(os.path.join(data_dir, "olist_customers_dataset.csv"))
    orders = pd.read_csv(os.path.join(data_dir, "olist_orders_dataset.csv"))
    payments = pd.read_csv(os.path.join(data_dir, "olist_order_payments_dataset.csv"))
    reviews = pd.read_csv(os.path.join(data_dir, "olist_order_reviews_dataset.csv"))

    # Parse timestamps
    orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])

    # Filter to delivered orders only
    delivered = orders[orders["order_status"] == "delivered"].copy()

    # Merge customer info
    merged = delivered.merge(customers, on="customer_id", how="left")

    # ─── Aggregated features per customer ───
    agg = merged.groupby("customer_unique_id").agg(
        customer_state=("customer_state", "first"),
        frequency=("order_id", "nunique"),
        last_purchase=("order_purchase_timestamp", "max"),
        first_purchase=("order_purchase_timestamp", "min"),
    ).reset_index()

    # Payment features
    pay_merged = delivered[["order_id"]].merge(payments, on="order_id", how="left")
    pay_merged = pay_merged.merge(
        merged[["order_id", "customer_unique_id"]].drop_duplicates(),
        on="order_id", how="left"
    )
    pay_agg = pay_merged.groupby("customer_unique_id").agg(
        monetary=("payment_value", "sum"),
        avg_order_value=("payment_value", "mean"),
        avg_installments=("payment_installments", "mean"),
        payment_type_count=("payment_type", "nunique"),
    ).reset_index()

    # Review features
    rev_merged = delivered[["order_id"]].merge(reviews, on="order_id", how="left")
    rev_merged = rev_merged.merge(
        merged[["order_id", "customer_unique_id"]].drop_duplicates(),
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

    return _compute_derived_features(df)


def _compute_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute recency, tenure, and churn label."""

    df["last_purchase"] = pd.to_datetime(df["last_purchase"])
    df["first_purchase"] = pd.to_datetime(df["first_purchase"])

    # Reference date = max date in dataset
    reference_date = df["last_purchase"].max()

    # Recency = days since last purchase
    df["recency_days"] = (reference_date - df["last_purchase"]).dt.days

    # Tenure = days between first and last purchase
    df["tenure_days"] = (df["last_purchase"] - df["first_purchase"]).dt.days

    # ─── Churn label ───
    # Customer is "churned" if they haven't purchased in the last 90 days
    churn_threshold = 90
    df["is_churned"] = (df["recency_days"] > churn_threshold).astype(int)

    # Encode state as numeric (label encoding)
    df["state_encoded"] = df["customer_state"].astype("category").cat.codes

    # Drop non-feature columns
    feature_cols = [
        "frequency", "monetary", "avg_order_value", "avg_installments",
        "payment_type_count", "avg_review_score", "review_count",
        "recency_days", "tenure_days", "state_encoded", "is_churned"
    ]
    result = df[feature_cols].copy()
    result = result.dropna()

    logger.info(
        "Features built: %d customers, churn rate=%.1f%%",
        len(result), result["is_churned"].mean() * 100
    )
    return result


if __name__ == "__main__":
    from config import DATA_DIR
    df = build_features_from_csv(str(DATA_DIR))
    print(df.head(10))
    print(f"\nShape: {df.shape}")
    print(f"Churn rate: {df['is_churned'].mean():.2%}")
