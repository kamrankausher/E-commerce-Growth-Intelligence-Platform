# E-commerce Growth Intelligence Platform

A production-ready, local-first analytics + ML platform built on the Brazilian Olist dataset to help e-commerce teams improve growth decisions.

## Business Problem
E-commerce operators usually track revenue, but struggle to connect customer behavior, experiments, and churn risk in one place. This project solves that by combining:
- SQL-driven analytics for KPIs and cohorts
- A/B experiment simulation + statistical testing
- Churn prediction pipeline with explainability
- API + dashboard for business users

## Architecture (Text Diagram)

```
        Olist CSV Files (data/)
                 |
                 v
      Data Loader (Pandas + SQLAlchemy)
                 |
                 v
           PostgreSQL (Normalized Tables)
         /               |                \
        v                v                 v
 SQL Analytics     A/B Testing Engine   Churn Pipeline
 (CTEs, windows)   (t-test, chi2, CIs)  (XGBoost+Optuna+SHAP)
        |                |                 |
        +---------> Streamlit Dashboard <--+
                          |
                          v
                    FastAPI /predict_churn
                          |
                          v
                 Docker + GitHub Actions CI
```

## Project Structure

```
project/
├── data/
├── sql/
│   ├── schema.sql
│   └── analytics_queries.sql
├── notebooks/
├── src/
│   ├── ab_testing/
│   │   └── engine.py
│   ├── churn_model/
│   │   ├── features.py
│   │   └── train.py
│   ├── api/
│   │   └── main.py
│   ├── utils/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── load_data.py
│   │   └── logger.py
│   └── main.py
├── dashboard/
│   └── app.py
├── mlruns/
├── tests/
├── .github/workflows/ci.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Setup (Local Machine)

### 1) Clone and create environment
```bash
git clone <repo-url>
cd E-commerce-Growth-Intelligence-Platform
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Start PostgreSQL locally
You can use local install or Docker:
```bash
docker run --name ecommerce-pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=ecommerce_growth -p 5432:5432 -d postgres:15
```

### 3) Configure environment
```bash
cp .env.example .env
```

### 4) Download Olist CSV files
Place Kaggle Olist CSV files into `data/`.

### 5) Load schema + data
```bash
python -m src.utils.load_data
```

### 6) Run A/B experiments
```bash
python -m src.ab_testing.engine
```

### 7) Start MLflow
```bash
mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --host 0.0.0.0 --port 5000
```

### 8) Train churn model
```bash
python -m src.churn_model.train
```

### 9) Run API
```bash
uvicorn src.api.main:app --reload --port 8000
```

### 10) Run dashboard
```bash
streamlit run dashboard/app.py
```

## API Example

`POST /predict_churn`

Request:
```json
{
  "recency_days": 180,
  "customer_age_days": 420,
  "purchase_frequency": 3,
  "avg_order_value": 145.5,
  "lifetime_value": 436.5
}
```

Response:
```json
{
  "churn_probability": 0.79,
  "churn_prediction": 1
}
```

## SQL Analytics Included
`sql/analytics_queries.sql` contains 11 interview-ready queries:
- Revenue by state
- Monthly revenue trend
- Monthly retention
- Repeat purchase rate
- Top sellers
- Cohort analysis
- RFM ranking
- Category review/sales performance
- Delivery delay by state
- Payment mix
- Best weekday by revenue

## Sample Insights You Can Discuss in Interview
- Which states contribute highest GMV and where logistics delays hurt retention.
- Which cohorts decay fastest after month 1.
- Whether checkout or campaign experiments are statistically significant.
- Which customers are at high churn risk and why (SHAP feature importance).

## Testing
```bash
pytest -q
```

## Docker
```bash
docker build -t ecommerce-growth-intelligence .
docker run -p 8000:8000 --env-file .env ecommerce-growth-intelligence
```

## Why this project is resume-strong
- Real SQL + experimentation + ML + MLOps in one practical system.
- Fully local and reproducible (no paid infrastructure).
- Clean modular structure suitable for a fresher explaining trade-offs.
