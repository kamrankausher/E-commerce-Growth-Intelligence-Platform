"""Load Olist CSV files into normalized PostgreSQL tables."""
from pathlib import Path
import pandas as pd
from src.utils.db import get_engine, run_sql_file
from src.utils.logger import get_logger

logger = get_logger(__name__)

TABLES = {
    "olist_customers_dataset.csv": "customers",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "olist_geolocation_dataset.csv": "geolocation",
    "product_category_name_translation.csv": "product_category_translation",
}


def load_csvs(data_dir: str = "data") -> None:
    engine = get_engine()
    logger.info("Initializing schema and indexes")
    run_sql_file(engine, "sql/schema.sql")

    for file_name, table_name in TABLES.items():
        path = Path(data_dir) / file_name
        if not path.exists():
            logger.warning("Skipping missing file: %s", path)
            continue

        logger.info("Loading %s -> %s", file_name, table_name)
        df = pd.read_csv(path)
        df.to_sql(table_name, engine, if_exists="append", index=False, method="multi", chunksize=5000)

    logger.info("Data load completed")


if __name__ == "__main__":
    load_csvs()
