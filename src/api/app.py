"""
FastAPI service for E-commerce Growth Intelligence Platform.
All endpoints return real data from CSV files + ML artifacts.
"""
import os, sys, json, pickle, threading
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.ab_testing.experiment_engine import ABTestEngine
from src.utils.logger import get_logger
from config import MODEL_DIR, DATA_DIR, ARTIFACTS_DIR, DASHBOARD_DIR

logger = get_logger(__name__)

app = FastAPI(title="E-commerce Growth Intelligence API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# Serve dashboard
if os.path.isdir(DASHBOARD_DIR):
    app.mount("/static", StaticFiles(directory=DASHBOARD_DIR), name="static")
if os.path.isdir(ARTIFACTS_DIR):
    app.mount("/artifacts", StaticFiles(directory=ARTIFACTS_DIR), name="artifacts")

@app.get("/", include_in_schema=False)
def serve_dashboard():
    index_path = os.path.join(DASHBOARD_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(404, "Dashboard not found. Ensure dashboard/index.html exists.")
    return FileResponse(index_path)

# ─── Data Cache ─────────────────────────────────────────────────────────────
_cache = {}

def _load_data():
    global _cache
    if _cache: return _cache
    files = {"customers": "olist_customers_dataset.csv", "orders": "olist_orders_dataset.csv",
             "order_items": "olist_order_items_dataset.csv", "payments": "olist_order_payments_dataset.csv",
             "reviews": "olist_order_reviews_dataset.csv", "products": "olist_products_dataset.csv",
             "sellers": "olist_sellers_dataset.csv", "categories": "product_category_name_translation.csv"}
    for key, fn in files.items():
        p = os.path.join(str(DATA_DIR), fn)
        if os.path.exists(p):
            _cache[key] = pd.read_csv(p)
        else:
            logger.warning("Data file not found: %s", p)
            _cache[key] = pd.DataFrame()
    if not _cache["orders"].empty:
        _cache["orders"]["order_purchase_timestamp"] = pd.to_datetime(_cache["orders"]["order_purchase_timestamp"])
        _cache["orders"]["order_delivered_customer_date"] = pd.to_datetime(_cache["orders"]["order_delivered_customer_date"], errors="coerce")
        _cache["orders"]["order_estimated_delivery_date"] = pd.to_datetime(_cache["orders"]["order_estimated_delivery_date"], errors="coerce")
    return _cache

_model_cache = {}
def _load_model():
    if _model_cache: return _model_cache
    p = os.path.join(str(MODEL_DIR), "churn_model.pkl")
    if os.path.exists(p):
        with open(p, "rb") as f: _model_cache.update(pickle.load(f))
    return _model_cache

# ═══ ENDPOINTS ══════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": bool(_load_model())}

# ─── PAGE 1: Overview ───────────────────────────────────────────────────────

@app.get("/api/kpis")
def get_kpis():
    d = _load_data()
    orders, payments, customers, reviews = d["orders"], d["payments"], d["customers"], d["reviews"]
    if orders.empty: raise HTTPException(404, "No data — run python setup.py first")
    delivered = orders[orders["order_status"] == "delivered"]
    rev_pay = payments.merge(delivered[["order_id"]], on="order_id")
    total_rev = float(rev_pay["payment_value"].sum())
    total_orders = int(delivered["order_id"].nunique())
    unique_cust = int(delivered.merge(customers, on="customer_id")["customer_unique_id"].nunique())
    aov = total_rev / total_orders if total_orders else 0
    avg_review = float(reviews["review_score"].mean()) if not reviews.empty else 0
    has_dates = delivered.dropna(subset=["order_delivered_customer_date", "order_estimated_delivery_date"])
    late = has_dates[has_dates["order_delivered_customer_date"] > has_dates["order_estimated_delivery_date"]]
    late_pct = len(late) / len(has_dates) * 100 if len(has_dates) > 0 else 0
    return {"total_revenue": round(total_rev, 2), "total_orders": total_orders,
            "unique_customers": unique_cust, "avg_order_value": round(aov, 2),
            "avg_review_score": round(avg_review, 2), "late_delivery_pct": round(late_pct, 1)}

@app.get("/api/revenue_trend")
def get_revenue_trend():
    d = _load_data()
    if d["orders"].empty: return []
    delivered = d["orders"][d["orders"]["order_status"] == "delivered"]
    merged = delivered.merge(d["payments"], on="order_id")
    merged["month"] = merged["order_purchase_timestamp"].dt.to_period("M").astype(str)
    trend = merged.groupby("month").agg(revenue=("payment_value", "sum"), orders=("order_id", "nunique")).reset_index()
    trend["revenue"] = trend["revenue"].round(2)
    return trend.sort_values("month").to_dict(orient="records")

@app.get("/api/top_states")
def get_top_states():
    d = _load_data()
    if d["orders"].empty: return []
    delivered = d["orders"][d["orders"]["order_status"] == "delivered"]
    m = delivered.merge(d["customers"], on="customer_id").merge(d["payments"], on="order_id")
    sr = m.groupby("customer_state")["payment_value"].sum().nlargest(10).reset_index()
    sr.columns = ["state", "revenue"]
    sr["revenue"] = sr["revenue"].round(2)
    return sr.to_dict(orient="records")

@app.get("/api/categories")
def get_categories():
    d = _load_data()
    items, prods, cats = d["order_items"], d["products"], d["categories"]
    if prods.empty or items.empty: return []
    m = items.merge(prods, on="product_id")
    if not cats.empty:
        m = m.merge(cats, on="product_category_name", how="left")
        m["category"] = m["product_category_name_english"].fillna(m["product_category_name"])
    else:
        m["category"] = m["product_category_name"]
    cr = m.groupby("category")["price"].sum().nlargest(10).reset_index()
    cr.columns = ["category", "revenue"]
    cr["revenue"] = cr["revenue"].round(2)
    return cr.to_dict(orient="records")

@app.get("/api/payments")
def get_payments():
    d = _load_data()
    if d["orders"].empty: return []
    delivered = d["orders"][d["orders"]["order_status"] == "delivered"]
    pd2 = d["payments"].merge(delivered[["order_id"]], on="order_id")
    dist = pd2.groupby("payment_type")["payment_value"].sum().reset_index()
    dist.columns = ["type", "value"]
    dist["value"] = dist["value"].round(2)
    return dist.to_dict(orient="records")

@app.get("/api/orders_table")
def get_orders_table():
    d = _load_data()
    if d["orders"].empty: return []
    orders = d["orders"].sort_values("order_purchase_timestamp", ascending=False).head(20)
    merged = orders.merge(d["customers"], on="customer_id", how="left")
    merged = merged.merge(d["payments"], on="order_id", how="left")
    result = []
    for _, r in merged.iterrows():
        result.append({"order_id": r["order_id"][:12] + "...", "date": str(r["order_purchase_timestamp"])[:10],
                       "state": r.get("customer_state", "N/A"), "status": r["order_status"],
                       "value": round(float(r.get("payment_value", 0)), 2)})
    return result

# ─── PAGE 2: SQL Analytics ──────────────────────────────────────────────────

@app.get("/api/cohort")
def get_cohort():
    d = _load_data()
    if d["orders"].empty: return []
    orders = d["orders"][d["orders"]["order_status"] == "delivered"]
    merged = orders.merge(d["customers"], on="customer_id")
    merged["order_month"] = merged["order_purchase_timestamp"].dt.to_period("M")
    first = merged.groupby("customer_unique_id")["order_month"].min().reset_index()
    first.columns = ["customer_unique_id", "cohort_month"]
    merged = merged.merge(first, on="customer_unique_id")
    merged["month_offset"] = (merged["order_month"] - merged["cohort_month"]).apply(lambda x: x.n if hasattr(x, 'n') else 0)
    cohort = merged.groupby(["cohort_month", "month_offset"])["customer_unique_id"].nunique().reset_index()
    cohort.columns = ["cohort_month", "month_offset", "customers"]
    cohort["cohort_month"] = cohort["cohort_month"].astype(str)
    cohort = cohort[cohort["month_offset"] <= 5]
    top_cohorts = sorted(cohort["cohort_month"].unique())[-8:]
    cohort = cohort[cohort["cohort_month"].isin(top_cohorts)]
    return cohort.to_dict(orient="records")

@app.get("/api/sellers")
def get_sellers():
    d = _load_data()
    if d["order_items"].empty: return []
    items = d["order_items"]
    reviews = d["reviews"]
    orders = d["orders"][d["orders"]["order_status"] == "delivered"]
    m = items.merge(orders[["order_id"]], on="order_id")
    m = m.merge(reviews, on="order_id", how="left")
    s = m.groupby("seller_id").agg(revenue=("price", "sum"), orders=("order_id", "nunique"),
                                    avg_review=("review_score", "mean")).reset_index()
    s = s[s["orders"] >= 5]
    order_items_orders = items.merge(orders[["order_id", "order_delivered_customer_date", "order_estimated_delivery_date"]], on="order_id")
    has_dates = order_items_orders.dropna(subset=["order_delivered_customer_date", "order_estimated_delivery_date"])
    has_dates = has_dates.copy()
    has_dates["is_late"] = has_dates["order_delivered_customer_date"] > has_dates["order_estimated_delivery_date"]
    late_rate = has_dates.groupby("seller_id")["is_late"].mean().reset_index()
    late_rate.columns = ["seller_id", "late_rate"]
    s = s.merge(late_rate, on="seller_id", how="left").fillna(0)
    s["revenue"] = s["revenue"].round(2)
    s["avg_review"] = s["avg_review"].round(2)
    s["late_rate"] = s["late_rate"].round(3)
    return s.head(50).to_dict(orient="records")

@app.get("/api/rfm")
def get_rfm():
    d = _load_data()
    if d["orders"].empty: return []
    orders = d["orders"][d["orders"]["order_status"] == "delivered"]
    merged = orders.merge(d["customers"], on="customer_id").merge(d["payments"], on="order_id")
    ref = merged["order_purchase_timestamp"].max()
    rfm = merged.groupby("customer_unique_id").agg(
        recency=("order_purchase_timestamp", lambda x: (ref - x.max()).days),
        frequency=("order_id", "nunique"),
        monetary=("payment_value", "sum")).reset_index()
    rfm["r_score"] = pd.qcut(rfm["recency"], 5, labels=[5,4,3,2,1]).astype(int)
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
    def segment(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 4 and f >= 4: return "Champions"
        if r >= 3 and f >= 3: return "Loyal"
        if r >= 4 and f <= 2: return "New Customers"
        if r <= 2 and f >= 3: return "At Risk"
        if r <= 2 and f <= 2: return "Lost"
        return "Needs Attention"
    rfm["segment"] = rfm.apply(segment, axis=1)
    seg_counts = rfm["segment"].value_counts().reset_index()
    seg_counts.columns = ["segment", "count"]
    return seg_counts.to_dict(orient="records")

@app.get("/api/cumulative_revenue")
def get_cumulative():
    d = _load_data()
    if d["orders"].empty: return []
    delivered = d["orders"][d["orders"]["order_status"] == "delivered"]
    merged = delivered.merge(d["payments"], on="order_id")
    merged["month"] = merged["order_purchase_timestamp"].dt.to_period("M").astype(str)
    monthly = merged.groupby("month")["payment_value"].sum().reset_index().sort_values("month")
    monthly["cumulative"] = monthly["payment_value"].cumsum().round(2)
    monthly["payment_value"] = monthly["payment_value"].round(2)
    return monthly.to_dict(orient="records")

# ─── PAGE 3: A/B Testing ───────────────────────────────────────────────────

@app.get("/api/ab_results")
def get_ab_results():
    engine = ABTestEngine()
    engine.run_all_experiments()
    df = engine.results_to_dataframe()
    records = []
    for _, row in df.iterrows():
        records.append({k: (round(float(v), 6) if isinstance(v, (float, np.floating)) else
                           int(v) if isinstance(v, (int, np.integer)) else
                           bool(v) if isinstance(v, (bool, np.bool_)) else str(v))
                       for k, v in row.items()})
    return records

# ─── PAGE 4: Churn ──────────────────────────────────────────────────────────

@app.get("/api/churn/model_info")
def get_churn_model_info():
    md = _load_model()
    if not md: raise HTTPException(503, "No model found. Run setup.py first.")
    model = md["model"]
    importance = dict(zip(md["feature_names"], [round(float(x), 4) for x in model.feature_importances_]))
    return {"metrics": md["metrics"], "feature_names": md["feature_names"],
            "feature_importance": importance, "params": md.get("params", {})}

@app.get("/api/churn/customers")
def get_churn_customers():
    md = _load_model()
    if not md: raise HTTPException(503, "No model found")
    from src.churn_model.feature_engineering import build_features_from_csv
    df = build_features_from_csv(str(DATA_DIR))
    features = [c for c in df.columns if c != "is_churned"]
    X = df[features]
    probas = md["model"].predict_proba(X)[:, 1]
    df = df.copy()
    df["churn_probability"] = probas
    df["risk_level"] = pd.cut(probas, bins=[0, 0.4, 0.7, 1.0], labels=["LOW", "MEDIUM", "HIGH"])
    high_risk = df.nlargest(20, "churn_probability")
    result = []
    for i, (_, r) in enumerate(high_risk.iterrows()):
        result.append({"customer_rank": i + 1, "churn_probability": round(float(r["churn_probability"]), 4),
                       "risk_level": str(r["risk_level"]), "frequency": int(r["frequency"]),
                       "monetary": round(float(r["monetary"]), 2),
                       "avg_days_between_orders": round(float(r["avg_days_between_orders"]), 1)})
    return result

@app.get("/api/churn/distribution")
def get_churn_distribution():
    md = _load_model()
    if not md: raise HTTPException(503, "No model found")
    from src.churn_model.feature_engineering import build_features_from_csv
    df = build_features_from_csv(str(DATA_DIR))
    features = [c for c in df.columns if c != "is_churned"]
    probas = md["model"].predict_proba(df[features])[:, 1]
    bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    hist, _ = np.histogram(probas, bins=bins)
    result = []
    for i in range(len(bins) - 1):
        label = f"{bins[i]:.1f}-{bins[i+1]:.1f}"
        tier = "LOW" if bins[i+1] <= 0.4 else "MEDIUM" if bins[i+1] <= 0.7 else "HIGH"
        result.append({"range": label, "count": int(hist[i]), "tier": tier})
    return result

class CustomerFeatures(BaseModel):
    frequency: int = Field(..., ge=1)
    monetary: float = Field(..., ge=0)
    avg_order_value: float = Field(..., ge=0)
    avg_installments: float = Field(..., ge=1)
    payment_type_count: int = Field(..., ge=1)
    avg_review_score: float = Field(3.0, ge=1, le=5)
    review_count: int = Field(0, ge=0)
    tenure_days: int = Field(0, ge=0)
    avg_days_between_orders: float = Field(90.0, ge=0)
    state_encoded: int = Field(0, ge=0)

@app.post("/api/churn/predict")
def predict_churn(customer: CustomerFeatures):
    md = _load_model()
    if not md: raise HTTPException(503, "Model not loaded. Run setup.py first.")
    features = customer.model_dump()
    try:
        df = pd.DataFrame([features])[md["feature_names"]]
    except KeyError as e:
        raise HTTPException(422, f"Feature mismatch: {e}. Model expects: {md['feature_names']}")
    proba = float(md["model"].predict_proba(df)[0][1])
    return {"churn_probability": round(proba, 4), "is_churned": proba >= 0.5,
            "risk_level": "HIGH" if proba >= 0.7 else "MEDIUM" if proba >= 0.4 else "LOW"}

# ─── PAGE 5: ML Experiments ────────────────────────────────────────────────

@app.get("/api/optuna_trials")
def get_optuna_trials():
    path = os.path.join(ARTIFACTS_DIR, "optuna_trials.json")
    if not os.path.exists(path): raise HTTPException(404, "No trial history found. Run setup.py first.")
    with open(path) as f: return json.load(f)

@app.post("/api/retrain")
def retrain_model():
    def _retrain():
        try:
            from src.churn_model.train_pipeline import run_full_pipeline
            global _model_cache
            _model_cache.clear()
            run_full_pipeline()
        except Exception as e:
            logger.error("Retrain failed: %s", e)
    t = threading.Thread(target=_retrain, daemon=True)
    t.start()
    return {"status": "started", "message": "Model retraining started in background"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
