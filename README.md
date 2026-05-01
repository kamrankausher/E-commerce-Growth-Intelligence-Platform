<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/XGBoost-2.0-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/Chart.js-4.4-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white" />
  <img src="https://img.shields.io/badge/MLflow-2.13-0194E2?style=for-the-badge&logo=mlflow&logoColor=white" />
</p>

# 📈 E-commerce Growth Intelligence Platform

> A production-grade data science platform that helps e-commerce businesses **analyze customer behavior**, **run statistically rigorous A/B tests**, **predict customer churn with ML**, and **track model experiments** — all from a single, beautiful dashboard.

---

## 🎯 The Problem

E-commerce companies bleed revenue from three blind spots:

| Problem | Impact | This Platform's Solution |
|---------|--------|--------------------------|
| **Silent Churn** | Customers leave without warning | XGBoost churn predictor with SHAP explainability |
| **Gut-feel Marketing** | No experiment framework | A/B testing engine with Chi-Square & Welch's t-test |
| **Scattered KPIs** | Metrics live in 5 different tools | Unified 5-page analytics dashboard |

---

## 🖥️ Dashboard Preview

The platform ships with a custom-built **Dark Deep Space** dashboard (pure HTML/CSS/JS — no heavy frameworks):

### Overview — Business KPIs
> 6 real-time KPIs, monthly revenue trends, geographic distribution, category performance, and payment analytics.

### SQL Analytics Engine
> Cohort retention matrix, RFM customer segmentation, seller performance scatter plot, and cumulative revenue growth.

### A/B Test Experiment Results
> 3 experiments with confidence interval visualization, significance badges, p-values, statistical power, and a sample size calculator.

### Churn Prediction Intelligence
> Model metrics, feature importance (XGBoost gain), risk distribution, top 20 high-risk customers, and an interactive prediction simulator.

### ML Experiment Tracking
> Optuna trial history (25 Bayesian optimization trials), best hyperparameters, and one-click model retraining.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                           │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Custom Dashboard │  │   FastAPI    │  │  Swagger /docs   │   │
│  │  HTML/CSS/JS      │  │   REST API   │  │  Auto-generated  │   │
│  │  (Chart.js)       │  │  15+ routes  │  │                  │   │
│  └────────┬─────────┘  └──────┬───────┘  └──────────────────┘   │
├───────────┼────────────────────┼──────────────────────────────────┤
│           │    INTELLIGENCE LAYER                                 │
│  ┌────────▼────────┐  ┌───────▼───────┐  ┌──────────────────┐   │
│  │   A/B Testing   │  │     Churn     │  │     MLflow       │   │
│  │   Engine        │  │   Predictor   │  │  Experiment Log  │   │
│  │  (SciPy stats)  │  │  (XGBoost)    │  │                  │   │
│  └────────┬────────┘  └───────┬───────┘  └────────┬─────────┘   │
│           │                   │                    │              │
│  ┌────────▼───────────────────▼────────────────────▼─────────┐   │
│  │          Feature Engineering (SQL + Pandas)                │   │
│  └────────────────────────────┬───────────────────────────────┘   │
├───────────────────────────────┼───────────────────────────────────┤
│           DATA LAYER          │                                    │
│  ┌────────────────────────────▼───────────────────────────────┐   │
│  │            SQLite (Portable, Zero-Config)                  │   │
│  │  customers │ orders │ items │ payments │ reviews │ sellers │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
ecommerce-growth-intelligence/
├── dashboard/                    # Frontend (served by FastAPI)
│   ├── index.html                # 5-page SPA with sidebar navigation
│   ├── styles.css                # Dark Deep Space design system
│   └── app.js                    # Chart.js rendering + API integration
├── data/
│   ├── load_data.py              # CSV → SQLite loader with indexes
│   └── download_olist.py         # Kaggle dataset downloader
├── src/
│   ├── ab_testing/
│   │   └── experiment_engine.py  # 3 experiments: Chi-square, Welch's t
│   ├── churn_model/
│   │   ├── feature_engineering.py  # RFM + 10 derived features
│   │   └── train_pipeline.py       # XGBoost + Optuna + SHAP + MLflow
│   ├── api/
│   │   └── app.py                # FastAPI backend (15+ endpoints)
│   └── utils/
│       ├── logger.py             # Centralized logging
│       └── database.py           # SQLite connection manager
├── tests/
│   ├── test_ab_testing.py        # 11 statistical test validations
│   ├── test_churn_model.py       # 5 model pipeline tests
│   └── test_api.py               # API endpoint coverage
├── sql/
│   └── analytics_queries.sql     # 12 advanced analytical SQL queries
├── .github/workflows/ci.yml     # GitHub Actions CI pipeline
├── Dockerfile                    # Container image for API
├── docker-compose.yml            # Full stack orchestration
├── setup.py                      # One-command setup script
├── generate_fake_data.py         # Synthetic data generator (8,500 customers)
├── config.py                     # Central configuration
├── requirements.txt              # Python dependencies
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- ~500MB disk space

### Setup (One Command)

```bash
# Clone the repository
git clone https://github.com/KamranKausher/E-commerce-Growth-Intelligence-Platform.git
cd E-commerce-Growth-Intelligence-Platform

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the full setup pipeline (~40 seconds)
python setup.py
```

`setup.py` automatically:
1. **Generates** 8,500 realistic customers, 15,500 orders, 220 sellers across 27 Brazilian states
2. **Loads** all data into SQLite with optimized indexes
3. **Trains** XGBoost churn model (25 Optuna trials + SHAP analysis)
4. **Runs** 3 A/B test experiments with statistical analysis

### Launch the Dashboard

```bash
python -m uvicorn src.api.app:app --reload --port 8000
```

Open **http://localhost:8000** — the full dashboard loads instantly.

---

## 📊 Key Components

### 1. SQL Analytics Engine (12 Queries)

| # | Query | SQL Techniques |
|---|-------|---------------|
| 1 | Revenue by State | JOIN, GROUP BY, ROUND |
| 2 | Monthly Revenue Trend | Window functions, LAG |
| 3 | Customer Cohort Analysis | CTEs, date arithmetic |
| 4 | Repeat Purchase Rate | Conditional aggregation |
| 5 | Top Sellers by Revenue | Aggregate ranking |
| 6 | Monthly Retention Rate | SELF JOIN, interval math |
| 7 | Category Performance | LEFT JOIN, COALESCE |
| 8 | Delivery Performance | CASE expressions, percentile |
| 9 | RFM Segmentation | NTILE window function |
| 10 | Payment Method Analysis | RANK window function |
| 11 | CLV Distribution | Statistical aggregates |
| 12 | Review Sentiment by Category | HAVING, conditional agg |

### 2. A/B Testing Engine

Three statistically rigorous experiments with automatic test selection:

| Experiment | Metric | Test Type | Result |
|-----------|--------|-----------|--------|
| Checkout Flow Redesign | Conversion Rate | Chi-Square | Not significant (p > 0.05) |
| Email Subject Line | Open Rate | Chi-Square | **Significant** (p = 0.021) |
| Discount Strategy (10% vs 15%) | Avg Order Value | Welch's t-test | **Significant** (p < 0.001) |

Each test outputs: **p-value, 95% CI, effect size, statistical power, MDE**

### 3. Churn Prediction Model

| Component | Detail |
|-----------|--------|
| **Algorithm** | XGBoost Classifier |
| **Tuning** | Optuna Bayesian Optimization (25 trials) |
| **Explainability** | SHAP TreeExplainer (visual artifacts) |
| **Tracking** | MLflow (params, metrics, model registry) |
| **Serving** | FastAPI endpoint with real-time prediction |
| **Churn Definition** | No purchase in trailing 90 days |

### Features Used (10 engineered features)

| Feature | Description |
|---------|-------------|
| `frequency` | Total orders placed |
| `monetary` | Lifetime spend (BRL) |
| `recency_days` | Days since last purchase |
| `avg_order_value` | Mean order value |
| `avg_review_score` | Mean review rating |
| `tenure_days` | Days between first and last order |
| `payment_type_count` | Payment method diversity |
| `avg_installments` | Mean installment count |
| `review_count` | Number of reviews written |
| `state_encoded` | Customer state (label encoded) |

---

## 🔌 API Reference

The FastAPI backend exposes 15+ endpoints:

```bash
# Health check
GET  /health

# KPIs & Overview
GET  /api/kpis
GET  /api/revenue_trend
GET  /api/top_states
GET  /api/categories
GET  /api/payments
GET  /api/orders_table

# SQL Analytics
GET  /api/cohort
GET  /api/rfm
GET  /api/sellers
GET  /api/cumulative_revenue

# A/B Testing
GET  /api/ab_results

# Churn Model
GET  /api/churn/model_info
GET  /api/churn/distribution
GET  /api/churn/customers
POST /api/churn/predict

# ML Experiments
GET  /api/optuna_trials
POST /api/retrain
```

### Example: Predict Churn

```bash
curl -X POST http://localhost:8000/api/churn/predict \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": 3,
    "monetary": 450.50,
    "avg_order_value": 150.17,
    "avg_installments": 2.5,
    "payment_type_count": 2,
    "avg_review_score": 4.2,
    "review_count": 3,
    "recency_days": 45,
    "tenure_days": 180,
    "state_encoded": 12
  }'
```

```json
{
  "churn_probability": 0.234,
  "is_churned": false,
  "risk_level": "LOW"
}
```

Full interactive docs: **http://localhost:8000/docs**

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific modules
python -m pytest tests/test_ab_testing.py -v   # 11 tests
python -m pytest tests/test_churn_model.py -v  # 5 tests
python -m pytest tests/test_api.py -v          # API endpoint tests
```

---

## 🐳 Docker

```bash
# Full stack
docker-compose up -d

# API only
docker build -t ecommerce-intelligence .
docker run -p 8000:8000 ecommerce-intelligence
```

---

## 🔍 Key Business Insights

1. **Sao Paulo (SP) dominates** — ~42% of total revenue, reflecting Brazil's economic concentration
2. **Recency is the #1 churn predictor** — SHAP analysis confirms time-based features dominate over monetary
3. **Credit card is king** — 74%+ of payments via credit card, with installment plans being common
4. **Delivery impacts satisfaction** — Late deliveries correlate with 1.5-star lower review scores
5. **Low organic retention** — Cohort analysis shows 90%+ of customers churn by Month 2, indicating massive retention opportunity
6. **Pareto seller distribution** — Top 20% of sellers generate ~80% of marketplace revenue

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.11+ |
| **Database** | SQLite 3 (portable, zero-config) |
| **ML** | XGBoost, Scikit-learn, Optuna, SHAP |
| **Experiment Tracking** | MLflow |
| **API** | FastAPI, Pydantic, Uvicorn |
| **Frontend** | HTML5, CSS3, JavaScript (Chart.js) |
| **Statistics** | SciPy, Statsmodels |
| **Data** | Pandas, NumPy |
| **Containerization** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |
| **Testing** | Pytest |

---

## 📄 License

MIT License — feel free to use for learning and portfolio purposes.

---

## 👤 Author

**Kamran Kausher**

Built as a data science portfolio project demonstrating end-to-end ML engineering — from SQL analytics and statistical testing to production model deployment with a custom dashboard.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/kamrankausher)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat-square&logo=github)](https://github.com/KamranKausher)
