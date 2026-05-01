"""
Unit tests for the churn prediction pipeline.
Tests feature engineering output, model training, and prediction.
"""
import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.churn_model.train_pipeline import ChurnPredictor


class TestChurnPredictor:
    """Tests for the ChurnPredictor class."""

    @staticmethod
    def _make_synthetic_data(n=1000):
        """Generate synthetic feature data for testing without DB/CSV."""
        np.random.seed(42)
        df = pd.DataFrame({
            "frequency": np.random.randint(1, 15, n),
            "monetary": np.random.uniform(20, 3000, n).round(2),
            "avg_order_value": np.random.uniform(20, 500, n).round(2),
            "avg_installments": np.random.uniform(1, 10, n).round(1),
            "payment_type_count": np.random.randint(1, 4, n),
            "avg_review_score": np.random.uniform(1, 5, n).round(2),
            "review_count": np.random.randint(0, 10, n),
            "recency_days": np.random.randint(0, 365, n),
            "tenure_days": np.random.randint(0, 730, n),
            "state_encoded": np.random.randint(0, 27, n),
            "is_churned": np.random.binomial(1, 0.3, n),
        })
        return df

    def test_prepare_data(self):
        """Data preparation should create train/test splits."""
        predictor = ChurnPredictor()
        df = self._make_synthetic_data()
        predictor.prepare_data(df)

        assert predictor.X_train is not None
        assert predictor.X_test is not None
        assert len(predictor.X_train) > len(predictor.X_test)
        assert "is_churned" not in predictor.feature_names

    def test_train_model(self):
        """Training should produce a model with metrics."""
        predictor = ChurnPredictor()
        df = self._make_synthetic_data()
        predictor.prepare_data(df)
        predictor.train()

        assert predictor.model is not None
        assert "accuracy" in predictor.metrics
        assert "roc_auc" in predictor.metrics
        assert 0 <= predictor.metrics["accuracy"] <= 1
        assert 0 <= predictor.metrics["roc_auc"] <= 1

    def test_predict_returns_valid_output(self):
        """Prediction should return probability, flag, and risk level."""
        predictor = ChurnPredictor()
        df = self._make_synthetic_data()
        predictor.prepare_data(df)
        predictor.train()

        sample_features = {
            "frequency": 3,
            "monetary": 450.0,
            "avg_order_value": 150.0,
            "avg_installments": 2.5,
            "payment_type_count": 2,
            "avg_review_score": 4.0,
            "review_count": 3,
            "recency_days": 45,
            "tenure_days": 180,
            "state_encoded": 12,
        }
        result = predictor.predict(sample_features)

        assert "churn_probability" in result
        assert "is_churned" in result
        assert "risk_level" in result
        assert 0 <= result["churn_probability"] <= 1
        assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH"]

    def test_save_and_load_model(self, tmp_path):
        """Model should save to disk and load back correctly."""
        predictor = ChurnPredictor()
        df = self._make_synthetic_data()
        predictor.prepare_data(df)
        predictor.train()

        model_path = str(tmp_path / "test_model.pkl")
        predictor.save_model(model_path)
        assert os.path.exists(model_path)

        loaded = ChurnPredictor.load_model(model_path)
        assert loaded.model is not None
        assert loaded.feature_names == predictor.feature_names
        assert loaded.metrics == predictor.metrics

    def test_feature_names_consistent(self):
        """Feature names should match expected set."""
        predictor = ChurnPredictor()
        df = self._make_synthetic_data()
        predictor.prepare_data(df)

        expected = [
            "frequency", "monetary", "avg_order_value", "avg_installments",
            "payment_type_count", "avg_review_score", "review_count",
            "recency_days", "tenure_days", "state_encoded"
        ]
        assert set(predictor.feature_names) == set(expected)
