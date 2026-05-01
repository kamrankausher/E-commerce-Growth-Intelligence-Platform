"""
Realistic synthetic data generator for the Brazilian E-commerce dataset.
Generates 8000+ customers, 15000+ orders, 200+ sellers with:
  - All 27 Brazilian state codes with population-weighted distribution
  - Log-normal price distributions
  - Multiple order statuses
  - 2-year date range for proper cohort analysis
  - Multiple items per order for some orders
"""
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ─── Brazilian States (all 27) with realistic population weights ────────────
STATES = {
    "SP": 0.220, "RJ": 0.083, "MG": 0.102, "BA": 0.073, "RS": 0.056,
    "PR": 0.057, "PE": 0.047, "CE": 0.045, "PA": 0.042, "SC": 0.036,
    "MA": 0.035, "GO": 0.035, "AM": 0.021, "PB": 0.020, "ES": 0.020,
    "RN": 0.018, "AL": 0.016, "PI": 0.016, "MT": 0.017, "DF": 0.015,
    "MS": 0.014, "SE": 0.012, "RO": 0.009, "TO": 0.008, "AC": 0.005,
    "AP": 0.004, "RR": 0.003,
}

STATE_CODES = list(STATES.keys())
_raw = list(STATES.values())
STATE_WEIGHTS = [w / sum(_raw) for w in _raw]  # normalize to sum=1.0

# ─── Brazilian Cities by State ──────────────────────────────────────────────
CITIES = {
    "SP": ["São Paulo", "Campinas", "Santos", "Ribeirão Preto", "Guarulhos", "São Bernardo do Campo"],
    "RJ": ["Rio de Janeiro", "Niterói", "Petrópolis", "Nova Iguaçu", "Campos dos Goytacazes"],
    "MG": ["Belo Horizonte", "Uberlândia", "Juiz de Fora", "Contagem", "Betim"],
    "BA": ["Salvador", "Feira de Santana", "Vitória da Conquista", "Camaçari"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Santa Maria"],
    "PR": ["Curitiba", "Londrina", "Maringá", "Ponta Grossa", "Cascavel"],
    "PE": ["Recife", "Jaboatão dos Guararapes", "Olinda", "Caruaru"],
    "CE": ["Fortaleza", "Caucaia", "Juazeiro do Norte", "Maracanaú"],
    "PA": ["Belém", "Ananindeua", "Santarém", "Marabá"],
    "SC": ["Florianópolis", "Joinville", "Blumenau", "Chapecó"],
}
# Default city for states not in the dict
DEFAULT_CITIES = ["Capital", "Interior City A", "Interior City B"]

# ─── Product Categories ─────────────────────────────────────────────────────
CATEGORIES = [
    ("beleza_saude", "health_beauty"),
    ("esporte_lazer", "sports_leisure"),
    ("informatica_acessorios", "computers_accessories"),
    ("moveis_decoracao", "furniture_decor"),
    ("utilidades_domesticas", "housewares"),
    ("cama_mesa_banho", "bed_bath_table"),
    ("telefonia", "telephony"),
    ("relogios_presentes", "watches_gifts"),
    ("automotivo", "auto"),
    ("brinquedos", "toys"),
    ("cool_stuff", "cool_stuff"),
    ("ferramentas_jardim", "garden_tools"),
    ("perfumaria", "perfumery"),
    ("bebes", "baby"),
    ("eletronicos", "electronics"),
    ("papelaria", "stationery"),
    ("fashion_bolsas_e_acessorios", "fashion_bags_accessories"),
    ("pet_shop", "pet_shop"),
    ("alimentos_bebidas", "food_drink"),
    ("moveis_escritorio", "office_furniture"),
]

_craw = [
    0.12, 0.10, 0.09, 0.08, 0.07, 0.07, 0.06, 0.05, 0.05, 0.04,
    0.04, 0.04, 0.03, 0.03, 0.03, 0.02, 0.02, 0.02, 0.02, 0.02,
]
CATEGORY_WEIGHTS = [w / sum(_craw) for w in _craw]


def generate_fake_data():
    """Generate all datasets and save as CSV files."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)

    np.random.seed(42)
    rng = np.random.RandomState(42)

    N_CUSTOMERS = 8500
    N_ORDERS = 15500
    N_SELLERS = 220
    N_PRODUCTS = 5000

    logger.info("Generating %d customers, %d orders, %d sellers, %d products...",
                N_CUSTOMERS, N_ORDERS, N_SELLERS, N_PRODUCTS)

    # ═══════════════════════════════════════════════════════════════════════
    # 1. CUSTOMERS
    # ═══════════════════════════════════════════════════════════════════════
    customer_unique_ids = [f"cust_{i:06d}" for i in range(N_CUSTOMERS)]
    customer_states = rng.choice(STATE_CODES, N_CUSTOMERS, p=STATE_WEIGHTS)
    customer_cities = []
    for st in customer_states:
        cities = CITIES.get(st, DEFAULT_CITIES)
        customer_cities.append(rng.choice(cities))

    # Each customer_unique_id maps to one or more customer_ids (sessions)
    # ~85% have 1 session, ~12% have 2, ~3% have 3+
    customer_ids = []
    cuid_to_cids = {}
    cid_counter = 0
    for i, cuid in enumerate(customer_unique_ids):
        n_sessions = rng.choice([1, 2, 3], p=[0.85, 0.12, 0.03])
        session_ids = []
        for _ in range(n_sessions):
            cid = f"csess_{cid_counter:07d}"
            cid_counter += 1
            session_ids.append(cid)
        cuid_to_cids[cuid] = session_ids

    # Build customers table (one row per customer_id/session)
    cust_rows = []
    for i, cuid in enumerate(customer_unique_ids):
        for cid in cuid_to_cids[cuid]:
            cust_rows.append({
                "customer_id": cid,
                "customer_unique_id": cuid,
                "customer_zip_code_prefix": f"{rng.randint(10000, 99999)}",
                "customer_city": customer_cities[i],
                "customer_state": customer_states[i],
            })

    df_customers = pd.DataFrame(cust_rows)
    all_customer_ids = df_customers["customer_id"].tolist()

    # ═══════════════════════════════════════════════════════════════════════
    # 2. SELLERS
    # ═══════════════════════════════════════════════════════════════════════
    seller_states = rng.choice(STATE_CODES, N_SELLERS, p=STATE_WEIGHTS)
    seller_rows = []
    for i in range(N_SELLERS):
        st = seller_states[i]
        cities = CITIES.get(st, DEFAULT_CITIES)
        seller_rows.append({
            "seller_id": f"seller_{i:04d}",
            "seller_zip_code_prefix": f"{rng.randint(10000, 99999)}",
            "seller_city": rng.choice(cities),
            "seller_state": st,
        })
    df_sellers = pd.DataFrame(seller_rows)

    # ═══════════════════════════════════════════════════════════════════════
    # 3. PRODUCTS
    # ═══════════════════════════════════════════════════════════════════════
    cat_names = [c[0] for c in CATEGORIES]
    product_categories = rng.choice(cat_names, N_PRODUCTS, p=CATEGORY_WEIGHTS)
    df_products = pd.DataFrame({
        "product_id": [f"prod_{i:05d}" for i in range(N_PRODUCTS)],
        "product_category_name": product_categories,
    })

    # Category translation table
    df_cat_translation = pd.DataFrame({
        "product_category_name": [c[0] for c in CATEGORIES],
        "product_category_name_english": [c[1] for c in CATEGORIES],
    })

    # ═══════════════════════════════════════════════════════════════════════
    # 4. ORDERS
    # ═══════════════════════════════════════════════════════════════════════
    # Date range: 2 years for proper cohort analysis
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_range_days = (end_date - start_date).days

    # Assign orders to customer sessions
    order_customer_ids = rng.choice(all_customer_ids, N_ORDERS)

    # Generate purchase timestamps with realistic weekly patterns
    purchase_dates = []
    for _ in range(N_ORDERS):
        days_offset = rng.randint(0, date_range_days)
        hour = rng.choice(range(24), p=[
            0.01, 0.005, 0.005, 0.005, 0.005, 0.01, 0.02, 0.04,
            0.06, 0.07, 0.08, 0.08, 0.07, 0.06, 0.06, 0.05,
            0.05, 0.05, 0.05, 0.06, 0.06, 0.05, 0.03, 0.02,
        ])
        minute = rng.randint(0, 60)
        dt = start_date + timedelta(days=int(days_offset), hours=int(hour), minutes=int(minute))
        purchase_dates.append(dt)

    # Order statuses with realistic distribution
    statuses = rng.choice(
        ["delivered", "shipped", "canceled", "unavailable", "processing"],
        N_ORDERS,
        p=[0.85, 0.05, 0.05, 0.03, 0.02],
    )

    # Delivery dates (only for delivered/shipped)
    delivered_dates = []
    estimated_dates = []
    for i in range(N_ORDERS):
        est_days = rng.randint(7, 30)
        estimated_dates.append(purchase_dates[i] + timedelta(days=int(est_days)))

        if statuses[i] in ("delivered", "shipped"):
            # Actual delivery: sometimes early, sometimes late
            actual_days = int(est_days + rng.normal(-2, 4))
            actual_days = max(2, actual_days)
            delivered_dates.append(purchase_dates[i] + timedelta(days=actual_days))
        else:
            delivered_dates.append(None)

    order_ids = [f"order_{i:06d}" for i in range(N_ORDERS)]
    df_orders = pd.DataFrame({
        "order_id": order_ids,
        "customer_id": order_customer_ids,
        "order_status": statuses,
        "order_purchase_timestamp": purchase_dates,
        "order_delivered_customer_date": delivered_dates,
        "order_estimated_delivery_date": estimated_dates,
    })

    # ═══════════════════════════════════════════════════════════════════════
    # 5. ORDER ITEMS (some orders have multiple items)
    # ═══════════════════════════════════════════════════════════════════════
    item_rows = []
    product_ids = df_products["product_id"].tolist()
    seller_ids = df_sellers["seller_id"].tolist()

    # Top 20% of sellers get 80% of orders (Pareto distribution)
    top_sellers = seller_ids[:int(N_SELLERS * 0.2)]
    rest_sellers = seller_ids[int(N_SELLERS * 0.2):]

    for oid in order_ids:
        # 75% single item, 20% two items, 5% three items
        n_items = rng.choice([1, 2, 3], p=[0.75, 0.20, 0.05])
        for item_id in range(1, n_items + 1):
            # Log-normal price distribution (realistic)
            price = float(np.exp(rng.normal(4.0, 0.9)))  # median ~55, range 5-1000+
            price = round(max(9.90, min(price, 2999.99)), 2)

            freight = round(float(rng.uniform(8.0, 65.0)), 2)

            # Pareto seller distribution
            if rng.random() < 0.80:
                seller = rng.choice(top_sellers)
            else:
                seller = rng.choice(rest_sellers)

            item_rows.append({
                "order_id": oid,
                "order_item_id": item_id,
                "product_id": rng.choice(product_ids),
                "seller_id": seller,
                "price": price,
                "freight_value": freight,
            })

    df_items = pd.DataFrame(item_rows)

    # ═══════════════════════════════════════════════════════════════════════
    # 6. PAYMENTS
    # ═══════════════════════════════════════════════════════════════════════
    pay_rows = []
    for oid in order_ids:
        order_items = df_items[df_items["order_id"] == oid]
        total = order_items["price"].sum() + order_items["freight_value"].sum()

        payment_type = rng.choice(
            ["credit_card", "boleto", "voucher", "debit_card"],
            p=[0.73, 0.19, 0.04, 0.04],
        )

        if payment_type == "credit_card":
            installments = int(rng.choice([1, 2, 3, 4, 5, 6, 8, 10, 12],
                                          p=[0.35, 0.15, 0.12, 0.10, 0.08, 0.07, 0.06, 0.04, 0.03]))
        else:
            installments = 1

        pay_rows.append({
            "order_id": oid,
            "payment_sequential": 1,
            "payment_type": payment_type,
            "payment_installments": installments,
            "payment_value": round(float(total), 2),
        })

    df_payments = pd.DataFrame(pay_rows)

    # ═══════════════════════════════════════════════════════════════════════
    # 7. REVIEWS (not all orders have reviews)
    # ═══════════════════════════════════════════════════════════════════════
    delivered_orders = df_orders[df_orders["order_status"] == "delivered"]["order_id"].tolist()
    # 90% of delivered orders have reviews
    reviewed_orders = rng.choice(delivered_orders,
                                  size=int(len(delivered_orders) * 0.90),
                                  replace=False)

    review_rows = []
    for i, oid in enumerate(reviewed_orders):
        # Realistic score distribution: skewed positive
        score = int(rng.choice([1, 2, 3, 4, 5], p=[0.11, 0.06, 0.09, 0.20, 0.54]))
        review_rows.append({
            "review_id": f"rev_{i:06d}",
            "order_id": oid,
            "review_score": score,
        })

    df_reviews = pd.DataFrame(review_rows)

    # ═══════════════════════════════════════════════════════════════════════
    # SAVE ALL CSVs
    # ═══════════════════════════════════════════════════════════════════════
    datasets = {
        "olist_customers_dataset.csv": df_customers,
        "olist_orders_dataset.csv": df_orders,
        "olist_order_items_dataset.csv": df_items,
        "olist_order_payments_dataset.csv": df_payments,
        "olist_order_reviews_dataset.csv": df_reviews,
        "olist_products_dataset.csv": df_products,
        "olist_sellers_dataset.csv": df_sellers,
        "product_category_name_translation.csv": df_cat_translation,
    }

    for filename, df in datasets.items():
        path = os.path.join(data_dir, filename)
        df.to_csv(path, index=False)
        logger.info("  → %s (%d rows)", filename, len(df))

    logger.info("✓ Generated %d customers, %d orders, %d sellers in %s",
                N_CUSTOMERS, N_ORDERS, N_SELLERS, data_dir)

    # Print summary stats
    delivered = df_orders[df_orders["order_status"] == "delivered"]
    total_rev = df_payments[df_payments["order_id"].isin(delivered["order_id"])]["payment_value"].sum()
    logger.info("  Revenue from delivered orders: R$ {:,.2f}".format(total_rev))
    logger.info("  Unique states: %d", df_customers["customer_state"].nunique())
    logger.info("  Unique cities: %d", df_customers["customer_city"].nunique())
    logger.info("  Unique sellers: %d", df_sellers["seller_id"].nunique())

    return datasets


if __name__ == "__main__":
    generate_fake_data()
