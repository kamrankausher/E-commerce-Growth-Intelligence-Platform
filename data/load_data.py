"""
Data loader — loads CSV files into SQLite database.
Creates tables and indexes for fast query performance.
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DATA_DIR
from src.utils.database import get_connection, load_df_to_table
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ─── CSV filename → table name mapping ──────────────────────────────────────
CSV_TABLE_MAP = {
    "olist_customers_dataset.csv": "customers",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}

# ─── SQLite Indexes for performance ─────────────────────────────────────────
INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status)",
    "CREATE INDEX IF NOT EXISTS idx_orders_purchase_ts ON orders(order_purchase_timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(order_id)",
    "CREATE INDEX IF NOT EXISTS idx_items_product ON order_items(product_id)",
    "CREATE INDEX IF NOT EXISTS idx_items_seller ON order_items(seller_id)",
    "CREATE INDEX IF NOT EXISTS idx_payments_order ON order_payments(order_id)",
    "CREATE INDEX IF NOT EXISTS idx_reviews_order ON order_reviews(order_id)",
    "CREATE INDEX IF NOT EXISTS idx_customers_state ON customers(customer_state)",
    "CREATE INDEX IF NOT EXISTS idx_customers_unique ON customers(customer_unique_id)",
]


def load_all_data():
    """Load all CSV files into SQLite and create indexes."""
    logger.info("Loading CSV data into SQLite...")

    for csv_file, table_name in CSV_TABLE_MAP.items():
        csv_path = os.path.join(DATA_DIR, csv_file)
        if not os.path.exists(csv_path):
            logger.warning("File not found: %s — skipping", csv_path)
            continue

        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip().str.lower()
        load_df_to_table(df, table_name)

    # Create indexes
    logger.info("Creating performance indexes...")
    conn = get_connection()
    try:
        for sql in INDEX_SQL:
            conn.execute(sql)
        conn.commit()
        logger.info("✓ All indexes created")
    finally:
        conn.close()

    logger.info("✓ All data loaded into SQLite successfully!")


if __name__ == "__main__":
    load_all_data()
