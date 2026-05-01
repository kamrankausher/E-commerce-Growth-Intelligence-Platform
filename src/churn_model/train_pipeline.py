"""
Churn prediction pipeline — XGBoost + Optuna + SHAP + MLflow.
"""
import os, sys, json, pickle, warnings
import numpy as np
import pandas as pd
import xgboost as xgb
import optuna, shap, mlflow, mlflow.xgboost
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, classification_report)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import (RANDOM_SEED, TEST_SIZE, OPTUNA_N_TRIALS,
                    MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT_NAME, MODEL_DIR, DATA_DIR, ARTIFACTS_DIR)
from src.churn_model.feature_engineering import build_features_from_csv
from src.utils.logger import get_logger

logger = get_logger(__name__)
warnings.filterwarnings("ignore", category=UserWarning)
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


class ChurnPredictor:
    def __init__(self):
        self.model = None
        self.best_params = None
        self.feature_names = None
        self.metrics = {}
        self.study = None

    def prepare_data(self, df=None):
        if df is None:
            df = build_features_from_csv(str(DATA_DIR))
        target = "is_churned"
        self.feature_names = [c for c in df.columns if c != target]
        X, y = df[self.feature_names], df[target]
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y)
        logger.info("Data split — Train: %d, Test: %d, Churn rate: %.1f%%",
                    len(self.X_train), len(self.X_test), y.mean() * 100)
        return self

    def tune_hyperparameters(self, n_trials=None):
        if n_trials is None:
            n_trials = OPTUNA_N_TRIALS
        logger.info("Starting Optuna tuning (%d trials)...", n_trials)
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        def objective(trial):
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
                "gamma": trial.suggest_float("gamma", 0.0, 5.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 10.0),
                "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 10.0),
                "scale_pos_weight": trial.suggest_float("scale_pos_weight", 1.0, 10.0),
            }
            skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
            scores = []
            for ti, vi in skf.split(self.X_train, self.y_train):
                m = xgb.XGBClassifier(**params, random_state=RANDOM_SEED, eval_metric="logloss", verbosity=0)
                m.fit(self.X_train.iloc[ti], self.y_train.iloc[ti])
                scores.append(roc_auc_score(self.y_train.iloc[vi], m.predict_proba(self.X_train.iloc[vi])[:, 1]))
            return np.mean(scores)

        self.study = optuna.create_study(direction="maximize")
        self.study.optimize(objective, n_trials=n_trials)
        self.best_params = self.study.best_params
        logger.info("Best ROC-AUC: %.4f", self.study.best_value)
        self._save_optuna_trials()
        return self

    def _save_optuna_trials(self):
        if not self.study: return
        trials = []
        for t in self.study.trials:
            trials.append({"number": t.number, "value": round(t.value, 6) if t.value else None,
                           "params": {k: round(v, 6) if isinstance(v, float) else v for k, v in t.params.items()},
                           "state": t.state.name})
        with open(os.path.join(ARTIFACTS_DIR, "optuna_trials.json"), "w") as f:
            json.dump(trials, f, indent=2)

    def train(self, params=None):
        if params is None: params = self.best_params or {}
        logger.info("Training final model...")
        self.model = xgb.XGBClassifier(**params, random_state=RANDOM_SEED, eval_metric="logloss", verbosity=0)
        self.model.fit(self.X_train, self.y_train, eval_set=[(self.X_test, self.y_test)], verbose=False)
        y_pred = self.model.predict(self.X_test)
        y_proba = self.model.predict_proba(self.X_test)[:, 1]
        self.metrics = {"accuracy": round(accuracy_score(self.y_test, y_pred), 4),
                        "precision": round(precision_score(self.y_test, y_pred), 4),
                        "recall": round(recall_score(self.y_test, y_pred), 4),
                        "f1": round(f1_score(self.y_test, y_pred), 4),
                        "roc_auc": round(roc_auc_score(self.y_test, y_proba), 4)}
        logger.info("Model metrics: %s", json.dumps(self.metrics))
        logger.info("\n%s", classification_report(self.y_test, y_pred, target_names=["Active", "Churned"]))
        return self

    def explain(self, n_samples=500):
        logger.info("Computing SHAP values...")
        explainer = shap.TreeExplainer(self.model)
        sample = self.X_test.sample(n=min(n_samples, len(self.X_test)), random_state=RANDOM_SEED)
        shap_values = explainer(sample)
        try:
            plt.figure(figsize=(10, 6))
            shap.summary_plot(shap_values, sample, show=False, plot_size=(10, 6))
            plt.tight_layout()
            plt.savefig(os.path.join(ARTIFACTS_DIR, "shap_summary.png"), dpi=150, bbox_inches="tight")
            plt.close()
            logger.info("SHAP plot saved")
        except Exception as e:
            logger.warning("Could not save SHAP plot: %s", e)
        return shap_values

    def log_to_mlflow(self):
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        with mlflow.start_run(run_name="xgb-churn-model") as run:
            if self.best_params: mlflow.log_params(self.best_params)
            mlflow.log_metrics(self.metrics)
            mlflow.xgboost.log_model(self.model, artifact_path="churn_model", registered_model_name="churn-predictor")
            mlflow.log_dict({"features": self.feature_names}, "feature_names.json")
            logger.info("MLflow run logged: %s", run.info.run_id)
        return self

    def save_model(self, path=None):
        if path is None: path = os.path.join(MODEL_DIR, "churn_model.pkl")
        with open(path, "wb") as f:
            pickle.dump({"model": self.model, "feature_names": self.feature_names,
                         "metrics": self.metrics, "params": self.best_params}, f)
        logger.info("Model saved to %s", path)

    @classmethod
    def load_model(cls, path=None):
        if path is None: path = os.path.join(MODEL_DIR, "churn_model.pkl")
        with open(path, "rb") as f:
            data = pickle.load(f)
        p = cls()
        p.model, p.feature_names, p.metrics, p.best_params = data["model"], data["feature_names"], data["metrics"], data["params"]
        return p

    def predict(self, features: dict) -> dict:
        df = pd.DataFrame([features])[self.feature_names]
        proba = self.model.predict_proba(df)[0][1]
        return {"churn_probability": round(float(proba), 4), "is_churned": bool(proba >= 0.5),
                "risk_level": "HIGH" if proba >= 0.7 else "MEDIUM" if proba >= 0.4 else "LOW"}


def run_full_pipeline():
    p = ChurnPredictor()
    p.prepare_data()
    p.tune_hyperparameters(n_trials=OPTUNA_N_TRIALS)
    p.train()
    p.log_to_mlflow()
    p.save_model()
    p.explain()
    logger.info("Pipeline complete!")
    return p

if __name__ == "__main__":
    run_full_pipeline()
