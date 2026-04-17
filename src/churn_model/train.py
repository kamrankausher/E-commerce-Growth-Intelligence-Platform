"""Train churn model with Optuna + MLflow + SHAP."""
from pathlib import Path
import joblib
import mlflow
import numpy as np
import optuna
import pandas as pd
import shap
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from src.churn_model.features import build_features
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _prepare_data(df: pd.DataFrame):
    x = df[["recency_days", "customer_age_days", "purchase_frequency", "avg_order_value", "lifetime_value"]]
    y = df["churn_label"]
    return train_test_split(x, y, test_size=0.2, random_state=42, stratify=y)


def _objective(trial: optuna.Trial, x_train, y_train, x_val, y_val) -> float:
    params = {
        "max_depth": trial.suggest_int("max_depth", 3, 8),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "n_estimators": trial.suggest_int("n_estimators", 100, 400),
        "subsample": trial.suggest_float("subsample", 0.7, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
        "random_state": 42,
        "objective": "binary:logistic",
        "eval_metric": "auc",
    }
    model = XGBClassifier(**params)
    model.fit(x_train, y_train)
    preds = model.predict_proba(x_val)[:, 1]
    return roc_auc_score(y_val, preds)


def train_model() -> str:
    df = build_features()
    x_train, x_test, y_train, y_test = _prepare_data(df)
    x_train2, x_val, y_train2, y_val = train_test_split(
        x_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment("ecommerce_churn")

    study = optuna.create_study(direction="maximize")
    study.optimize(lambda trial: _objective(trial, x_train2, y_train2, x_val, y_val), n_trials=15)
    best_params = study.best_params

    with mlflow.start_run(run_name="xgboost_optuna"):
        model = XGBClassifier(
            **best_params,
            random_state=42,
            objective="binary:logistic",
            eval_metric="auc",
        )
        model.fit(x_train, y_train)
        probs = model.predict_proba(x_test)[:, 1]
        preds = (probs >= 0.5).astype(int)

        auc = roc_auc_score(y_test, probs)
        f1 = f1_score(y_test, preds)

        mlflow.log_params(best_params)
        mlflow.log_metric("roc_auc", auc)
        mlflow.log_metric("f1", f1)
        mlflow.xgboost.log_model(model, artifact_path="model", registered_model_name="churn_model")

        Path("artifacts").mkdir(exist_ok=True)
        joblib.dump(model, settings.model_path)

        sample = x_test.sample(n=min(500, len(x_test)), random_state=42)
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(sample)
        shap.summary_plot(shap_values, sample, show=False)
        import matplotlib.pyplot as plt

        shap_path = Path("artifacts/shap_summary.png")
        plt.tight_layout()
        plt.savefig(shap_path)
        mlflow.log_artifact(str(shap_path))
        plt.close()

        logger.info("Training done | AUC=%.4f | F1=%.4f", auc, f1)

    return settings.model_path


if __name__ == "__main__":
    train_model()
