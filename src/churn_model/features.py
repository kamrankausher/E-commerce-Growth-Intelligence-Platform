"""Feature engineering for churn modeling."""
import pandas as pd
from sqlalchemy import text
from src.utils.db import get_engine


FEATURE_SQL = """
WITH order_base AS (
    SELECT c.customer_unique_id,
           o.order_id,
           o.order_purchase_timestamp,
           SUM(op.payment_value) AS order_value
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_payments op ON o.order_id = op.order_id
    GROUP BY c.customer_unique_id, o.order_id, o.order_purchase_timestamp
), customer_agg AS (
    SELECT customer_unique_id,
           MAX(order_purchase_timestamp) AS last_purchase_date,
           MIN(order_purchase_timestamp) AS first_purchase_date,
           COUNT(order_id) AS purchase_frequency,
           AVG(order_value) AS avg_order_value,
           SUM(order_value) AS lifetime_value
    FROM order_base
    GROUP BY customer_unique_id
)
SELECT customer_unique_id,
       EXTRACT(DAY FROM (CURRENT_DATE - DATE(last_purchase_date))) AS recency_days,
       EXTRACT(DAY FROM (DATE(last_purchase_date) - DATE(first_purchase_date))) AS customer_age_days,
       purchase_frequency,
       avg_order_value,
       lifetime_value,
       CASE
         WHEN EXTRACT(DAY FROM (CURRENT_DATE - DATE(last_purchase_date))) > 120 THEN 1
         ELSE 0
       END AS churn_label
FROM customer_agg
WHERE purchase_frequency >= 1
"""


def build_features() -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(FEATURE_SQL), conn)
