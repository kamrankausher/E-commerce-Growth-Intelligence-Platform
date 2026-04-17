"""Central config loader for local environments."""
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/ecommerce_growth"
    )
    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    model_path: str = os.getenv("MODEL_PATH", "artifacts/churn_model.joblib")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
