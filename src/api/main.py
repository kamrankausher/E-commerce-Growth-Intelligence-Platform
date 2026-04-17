"""FastAPI service for churn prediction."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import joblib
import numpy as np
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
app = FastAPI(title="E-commerce Growth Intelligence API", version="1.0.0")


class ChurnRequest(BaseModel):
    recency_days: float = Field(..., ge=0)
    customer_age_days: float = Field(..., ge=0)
    purchase_frequency: int = Field(..., ge=0)
    avg_order_value: float = Field(..., ge=0)
    lifetime_value: float = Field(..., ge=0)


class ChurnResponse(BaseModel):
    churn_probability: float
    churn_prediction: int


def _load_model():
    try:
        return joblib.load(settings.model_path)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Model not found at {settings.model_path}. Train model first.") from exc


model = None


@app.on_event("startup")
def startup_event():
    global model
    try:
        model = _load_model()
        logger.info("Model loaded from %s", settings.model_path)
    except RuntimeError as exc:
        model = None
        logger.warning("Startup without model: %s", exc)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict_churn", response_model=ChurnResponse)
def predict_churn(request: ChurnRequest):
    try:
        if model is None:
            raise ValueError("Model is not loaded. Train the churn model first.")
        features = np.array(
            [[
                request.recency_days,
                request.customer_age_days,
                request.purchase_frequency,
                request.avg_order_value,
                request.lifetime_value,
            ]]
        )
        probability = float(model.predict_proba(features)[0][1])
        prediction = int(probability >= 0.5)
        return ChurnResponse(churn_probability=probability, churn_prediction=prediction)
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc
