"""
Realistic synthetic data generator for the Brazilian E-commerce dataset.
Generates 8000+ customers, 15000+ orders, 200+ sellers with:
  - All 27 Brazilian state codes with population-weighted distribution
  - Log-normal price distributions
  - Customer segments (active/occasional/dormant) for realistic churn
  - Weekend peaks and year-end seasonality
  - 2-year date range for proper cohort analysis
"""
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ─── Brazilian States with REALISTIC e-commerce distribution ────────────────
# SP ~35%, RJ ~15%, MG ~12% — matches real Brazilian e-commerce data
STATES = {
    "SP": 0.350, "RJ": 0.150, "MG": 0.120, "BA": 0.055, "RS": 0.050,
    "PR": 0.048, "PE": 0.035, "CE": 0.032, "PA": 0.024, "SC": 0.028,
    "MA": 0.018, "GO": 0.022, "AM": 0.012, "PB": 0.010, "ES": 0.014,
    "RN": 0.009, "AL": 0.008, "PI": 0.006, "MT": 0.010, "DF": 0.012,
    "MS": 0.008, "SE": 0.005, "RO": 0.004, "TO": 0.003, "AC": 0.002,
    "AP": 0.002, "RR": 0.001,
}

STATE_CODES = list(STATES.keys())
_raw = list(STATES.values())
STATE_WEIGHTS = [w / sum(_raw) for w in _raw]

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
DEFAULT_CITIES = ["Capital", "Interior City A", "Interior City B"]

# ─── Product Categories ─────────────────────────────────────────────────────
CATEGORIES = [
    ("beleza_saude", "health_beauty"), ("esporte_lazer", "sports_leisure"),
    ("informatica_acessorios", "computers_accessories"), ("moveis_decoracao", "furniture_decor"),
    ("utilidades_domesticas", "housewares"), ("cama_mesa_banho", "bed_bath_table"),
    ("telefonia", "telephony"), ("relogios_presentes", "watches_gifts"),
    ("automotivo", "auto"), ("brinquedos", "toys"), ("cool_stuff", "cool_stuff"),
    ("ferramentas_jardim", "garden_tools"), ("perfumaria", "perfumery"),
    ("bebes", "baby"), ("eletronicos", "electronics"), ("papelaria", "stationery"),
    ("fashion_bolsas_e_acessorios", "fashion_bags_accessories"),
    ("pet_shop", "pet_shop"), ("alimentos_bebidas", "food_drink"),
    ("moveis_escritorio", "office_furniture"),
]
_craw = [0.12,0.10,0.09,0.08,0.07,0.07,0.06,0.05,0.05,0.04,
         0.04,0.04,0.03,0.03,0.03,0.02,0.02,0.02,0.02,0.02]
CATEGORY_WEIGHTS = [w / sum(_craw) for w in _craw]


def _generate_seasonal_dates(rng, n, start_date, end_date):
    """Generate order dates with weekend peaks and year-end seasonality."""
    total_days = (end_date - start_date).days
    day_weights = np.ones(total_days + 1)
    for d in range(total_days + 1):
        dt = start_date + timedelta(days=d)
        if dt.weekday() >= 5:          # Weekend boost
            day_weights[d] *= 1.35
        if dt.month in (11, 12):       # Year-end / Black Friday / Christmas
            day_weights[d] *= 1.45
        elif dt.month == 1:            # January dip
            day_weights[d] *= 0.75
        elif dt.month in (5, 6):       # Mid-year promotion
            day_weights[d] *= 1.15
    day_weights /= day_weights.sum()
    day_offsets = rng.choice(total_days + 1, n, p=day_weights)

    hour_probs = [
        0.01,0.005,0.005,0.005,0.005,0.01,0.02,0.04,
        0.06,0.07,0.08,0.08,0.07,0.06,0.06,0.05,
        0.05,0.05,0.05,0.06,0.06,0.05,0.03,0.02,
    ]
    dates = []
    for d in day_offsets:
        hour = rng.choice(24, p=hour_probs)
        minute = rng.randint(0, 60)
        dates.append(start_date + timedelta(days=int(d), hours=int(hour), minutes=int(minute)))
    return dates


def generate_fake_data():
    """Generate all datasets and save as CSV files."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)

    np.random.seed(42)
    rng = np.random.RandomState(42)

    N_CUSTOMERS = 8500
    N_SELLERS = 220
    N_PRODUCTS = 5000

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)

    logger.info("Generating %d customers, %d sellers, %d products...",
                N_CUSTOMERS, N_SELLERS, N_PRODUCTS)

    # ═══════════════════════════════════════════════════════════════════════
    # 1. CUSTOMERS
    # ═══════════════════════════════════════════════════════════════════════
    customer_unique_ids = [f"cust_{i:06d}" for i in range(N_CUSTOMERS)]
    customer_states = rng.choice(STATE_CODES, N_CUSTOMERS, p=STATE_WEIGHTS)
    customer_cities = []
    for st in customer_states:
        cities = CITIES.get(st, DEFAULT_CITIES)
        customer_cities.append(rng.choice(cities))

    cuid_to_cids = {}
    cid_counter = 0
    for cuid in customer_unique_ids:
        n_sessions = rng.choice([1, 2, 3], p=[0.85, 0.12, 0.03])
        session_ids = []
        for _ in range(n_sessions):
            session_ids.append(f"csess_{cid_counter:07d}")
            cid_counter += 1
        cuid_to_cids[cuid] = session_ids

    cust_rows = []
    for i, cuid in enumerate(customer_unique_ids):
        for cid in cuid_to_cids[cuid]:
            cust_rows.append({
                "customer_id": cid, "customer_unique_id": cuid,
                "customer_zip_code_prefix": f"{rng.randint(10000, 99999)}",
                "customer_city": customer_cities[i], "customer_state": customer_states[i],
            })
    df_customers = pd.DataFrame(cust_rows)
    all_customer_ids = df_customers["customer_id"].tolist()

    # ═══════════════════════════════════════════════════════════════════════
    # 2. CUSTOMER SEGMENTS — controls realistic churn distribution
    # ═══════════════════════════════════════════════════════════════════════
    # Active (73%): buy often AND guaranteed ≥1 order in last 90 days
    # Occasional (15%): scattered orders — some recent activity
    # Dormant (12%): buy 1-2 times, only in first 15 months → always churned
    segments = rng.choice(
        ["active", "occasional", "dormant"], N_CUSTOMERS,
        p=[0.73, 0.15, 0.12]
    )

    # Build customer→segment lookup using customer_id
    cid_to_segment = {}
    for i, cuid in enumerate(customer_unique_ids):
        for cid in cuid_to_cids[cuid]:
            cid_to_segment[cid] = segments[i]

    # Generate orders PER CUSTOMER based on segment
    order_rows = []
    order_counter = 0
    dormant_end = datetime(2025, 6, 30)  # Dormant customers stop buying here
    recent_start = datetime(2025, 10, 1)  # Last 90 days of the dataset

    for i, cuid in enumerate(customer_unique_ids):
        cids = cuid_to_cids[cuid]
        seg = segments[i]

        if seg == "active":
            n_orders = max(2, min(10, int(rng.exponential(2.0) + 2)))
            dates = _generate_seasonal_dates(rng, n_orders, start_date, end_date)
            # GUARANTEE at least one order in last 90 days
            has_recent = any(d >= recent_start for d in dates)
            if not has_recent:
                extra = _generate_seasonal_dates(rng, 1, recent_start, end_date)
                dates.extend(extra)
        elif seg == "occasional":
            n_orders = rng.choice([1, 2, 3], p=[0.40, 0.40, 0.20])
            dates = _generate_seasonal_dates(rng, n_orders, start_date, end_date)
        else:  # dormant
            n_orders = rng.choice([1, 2], p=[0.60, 0.40])
            dates = _generate_seasonal_dates(rng, n_orders, start_date, dormant_end)

        for dt in dates:
            cid = rng.choice(cids)
            order_rows.append({
                "order_id": f"order_{order_counter:06d}",
                "customer_id": cid,
                "order_purchase_timestamp": dt,
            })
            order_counter += 1

    N_ORDERS = len(order_rows)
    logger.info("Generated %d orders from customer segments", N_ORDERS)

    # Assign statuses
    statuses = rng.choice(
        ["delivered", "shipped", "canceled", "unavailable", "processing"],
        N_ORDERS, p=[0.85, 0.05, 0.05, 0.03, 0.02],
    )

    # Delivery dates
    delivered_dates = []
    estimated_dates = []
    for i in range(N_ORDERS):
        purchase = order_rows[i]["order_purchase_timestamp"]
        est_days = rng.randint(7, 30)
        estimated_dates.append(purchase + timedelta(days=int(est_days)))
        if statuses[i] in ("delivered", "shipped"):
            actual_days = max(2, int(est_days + rng.normal(-2, 4)))
            delivered_dates.append(purchase + timedelta(days=actual_days))
        else:
            delivered_dates.append(None)

    for i in range(N_ORDERS):
        order_rows[i]["order_status"] = statuses[i]
        order_rows[i]["order_delivered_customer_date"] = delivered_dates[i]
        order_rows[i]["order_estimated_delivery_date"] = estimated_dates[i]

    df_orders = pd.DataFrame(order_rows)
    order_ids = df_orders["order_id"].tolist()

    # ═══════════════════════════════════════════════════════════════════════
    # 3. SELLERS
    # ═══════════════════════════════════════════════════════════════════════
    seller_states = rng.choice(STATE_CODES, N_SELLERS, p=STATE_WEIGHTS)
    seller_rows = []
    for i in range(N_SELLERS):
        st = seller_states[i]
        seller_rows.append({
            "seller_id": f"seller_{i:04d}",
            "seller_zip_code_prefix": f"{rng.randint(10000, 99999)}",
            "seller_city": rng.choice(CITIES.get(st, DEFAULT_CITIES)),
            "seller_state": st,
        })
    df_sellers = pd.DataFrame(seller_rows)

    # ═══════════════════════════════════════════════════════════════════════
    # 4. PRODUCTS
    # ═══════════════════════════════════════════════════════════════════════
    cat_names = [c[0] for c in CATEGORIES]
    df_products = pd.DataFrame({
        "product_id": [f"prod_{i:05d}" for i in range(N_PRODUCTS)],
        "product_category_name": rng.choice(cat_names, N_PRODUCTS, p=CATEGORY_WEIGHTS),
    })
    df_cat_translation = pd.DataFrame({
        "product_category_name": [c[0] for c in CATEGORIES],
        "product_category_name_english": [c[1] for c in CATEGORIES],
    })

    # ═══════════════════════════════════════════════════════════════════════
    # 5. ORDER ITEMS
    # ═══════════════════════════════════════════════════════════════════════
    product_ids = df_products["product_id"].tolist()
    seller_ids = df_sellers["seller_id"].tolist()
    top_sellers = seller_ids[:int(N_SELLERS * 0.2)]
    rest_sellers = seller_ids[int(N_SELLERS * 0.2):]

    item_rows = []
    for oid in order_ids:
        n_items = rng.choice([1, 2, 3], p=[0.75, 0.20, 0.05])
        for item_id in range(1, n_items + 1):
            price = float(np.exp(rng.normal(4.0, 0.9)))
            price = round(max(9.90, min(price, 2999.99)), 2)
            freight = round(float(rng.uniform(8.0, 65.0)), 2)
            seller = rng.choice(top_sellers) if rng.random() < 0.80 else rng.choice(rest_sellers)
            item_rows.append({
                "order_id": oid, "order_item_id": item_id,
                "product_id": rng.choice(product_ids), "seller_id": seller,
                "price": price, "freight_value": freight,
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
        installments = 1
        if payment_type == "credit_card":
            installments = int(rng.choice(
                [1, 2, 3, 4, 5, 6, 8, 10, 12],
                p=[0.35, 0.15, 0.12, 0.10, 0.08, 0.07, 0.06, 0.04, 0.03]))
        pay_rows.append({
            "order_id": oid, "payment_sequential": 1, "payment_type": payment_type,
            "payment_installments": installments, "payment_value": round(float(total), 2),
        })
    df_payments = pd.DataFrame(pay_rows)

    # ═══════════════════════════════════════════════════════════════════════
    # 7. REVIEWS — J-shaped distribution (mostly 4s and 5s)
    # ═══════════════════════════════════════════════════════════════════════
    delivered_orders = df_orders[df_orders["order_status"] == "delivered"]["order_id"].tolist()
    reviewed_orders = rng.choice(delivered_orders, size=int(len(delivered_orders) * 0.90), replace=False)
    review_rows = []
    for i, oid in enumerate(reviewed_orders):
        score = int(rng.choice([1, 2, 3, 4, 5], p=[0.11, 0.06, 0.09, 0.20, 0.54]))
        review_rows.append({"review_id": f"rev_{i:06d}", "order_id": oid, "review_score": score})
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
        df.to_csv(os.path.join(data_dir, filename), index=False)
        logger.info("  → %s (%d rows)", filename, len(df))

    delivered = df_orders[df_orders["order_status"] == "delivered"]
    total_rev = df_payments[df_payments["order_id"].isin(delivered["order_id"])]["payment_value"].sum()
    logger.info("✓ Generated %d customers, %d orders, %d sellers", N_CUSTOMERS, N_ORDERS, N_SELLERS)
    logger.info("  Revenue from delivered orders: R$ {:,.2f}".format(total_rev))
    logger.info("  Unique states: %d", df_customers["customer_state"].nunique())
    logger.info("  SP share: %.1f%%", (df_customers["customer_state"] == "SP").mean() * 100)
    return datasets


if __name__ == "__main__":
    generate_fake_data()
