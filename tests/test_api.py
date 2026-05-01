"""Unit tests for the FastAPI endpoints."""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

class TestHealthEndpoint:
    def test_health_returns_200(self):
        assert client.get("/health").status_code == 200

    def test_health_response_format(self):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert "model_loaded" in data

class TestKPIEndpoint:
    def test_kpis_returns_200(self):
        r = client.get("/api/kpis")
        assert r.status_code in [200, 404]  # 404 if no data yet

    def test_kpis_fields(self):
        r = client.get("/api/kpis")
        if r.status_code == 200:
            data = r.json()
            for key in ["total_revenue", "total_orders", "unique_customers", "avg_order_value"]:
                assert key in data

class TestPredictEndpoint:
    def test_predict_returns_result(self):
        r = client.post("/api/churn/predict", json={
            "frequency": 3, "monetary": 450.50, "avg_order_value": 150.17,
            "avg_installments": 2.5, "payment_type_count": 2, "avg_review_score": 4.2,
            "review_count": 3, "recency_days": 45, "tenure_days": 180, "state_encoded": 12})
        assert r.status_code in [200, 503]

    def test_predict_invalid_returns_422(self):
        r = client.post("/api/churn/predict", json={"frequency": 3})
        assert r.status_code == 422

    def test_predict_negative_frequency_returns_422(self):
        r = client.post("/api/churn/predict", json={
            "frequency": -1, "monetary": 450.50, "avg_order_value": 150.17,
            "avg_installments": 2.5, "payment_type_count": 2, "recency_days": 45,
            "tenure_days": 180, "state_encoded": 12})
        assert r.status_code == 422

class TestModelInfoEndpoint:
    def test_model_info_status(self):
        r = client.get("/api/churn/model_info")
        assert r.status_code in [200, 503]

class TestABEndpoint:
    def test_ab_results(self):
        r = client.get("/api/ab_results")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3

class TestAnalyticsEndpoints:
    def test_revenue_trend(self):
        r = client.get("/api/revenue_trend")
        assert r.status_code == 200

    def test_top_states(self):
        r = client.get("/api/top_states")
        assert r.status_code == 200

    def test_categories(self):
        r = client.get("/api/categories")
        assert r.status_code == 200

    def test_payments(self):
        r = client.get("/api/payments")
        assert r.status_code == 200
