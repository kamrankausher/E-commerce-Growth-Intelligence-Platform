"""
Central configuration for the E-commerce Growth Intelligence Platform.
All paths use os.path for cross-platform compatibility.
"""
import os

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SQL_DIR = os.path.join(BASE_DIR, "sql")
MODEL_DIR = os.path.join(BASE_DIR, "models")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
MLFLOW_DIR = os.path.join(BASE_DIR, "mlruns")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")

# ─── Database (SQLite) ──────────────────────────────────────────────────────
DATABASE_PATH = os.path.join(DATA_DIR, "ecommerce.db")

# ─── MLflow ──────────────────────────────────────────────────────────────────
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", f"file:///{MLFLOW_DIR}")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "churn-prediction")

# ─── API ─────────────────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

# ─── Model Defaults ─────────────────────────────────────────────────────────
RANDOM_SEED = 42
TEST_SIZE = 0.2
OPTUNA_N_TRIALS = 25

# ─── Logging ─────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
