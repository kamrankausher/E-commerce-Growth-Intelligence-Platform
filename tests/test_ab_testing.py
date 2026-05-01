"""
Unit tests for the A/B Testing Engine.
Tests all three experiments, statistical calculations, and output format.
"""
import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.ab_testing.experiment_engine import ABTestEngine, ExperimentResult


class TestABTestEngine:
    """Tests for the ABTestEngine class."""

    def setup_method(self):
        """Create a fresh engine for each test."""
        self.engine = ABTestEngine(confidence_level=0.95)

    def test_engine_initialization(self):
        """Engine should initialize with correct alpha."""
        assert self.engine.alpha == pytest.approx(0.05)
        assert self.engine.confidence_level == pytest.approx(0.95)
        assert len(self.engine.results) == 0

    def test_checkout_experiment_returns_result(self):
        """Checkout experiment should return an ExperimentResult."""
        result = self.engine.simulate_checkout_experiment()
        assert isinstance(result, ExperimentResult)
        assert result.experiment_name == "Checkout Flow Redesign"
        assert result.metric_name == "conversion_rate"
        assert result.test_type == "chi_square"

    def test_email_experiment_returns_result(self):
        """Email experiment should return an ExperimentResult."""
        result = self.engine.simulate_email_experiment()
        assert isinstance(result, ExperimentResult)
        assert result.experiment_name == "Email Subject Line Test"
        assert result.metric_name == "open_rate"

    def test_discount_experiment_returns_result(self):
        """Discount experiment should return an ExperimentResult."""
        result = self.engine.simulate_discount_experiment()
        assert isinstance(result, ExperimentResult)
        assert result.experiment_name == "Discount Strategy (10% vs 15%)"
        assert result.metric_name == "avg_order_value"
        assert result.test_type == "t_test"

    def test_run_all_experiments(self):
        """Running all experiments should produce 3 results."""
        results = self.engine.run_all_experiments()
        assert len(results) == 3
        names = [r.experiment_name for r in results]
        assert "Checkout Flow Redesign" in names
        assert "Email Subject Line Test" in names
        assert "Discount Strategy (10% vs 15%)" in names

    def test_results_to_dataframe(self):
        """Results should convert to a valid DataFrame."""
        self.engine.run_all_experiments()
        df = self.engine.results_to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        required_cols = [
            "experiment_name", "p_value", "is_significant",
            "ci_lower", "ci_upper", "mde", "statistical_power"
        ]
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_p_value_range(self):
        """p-values should be between 0 and 1."""
        self.engine.run_all_experiments()
        for result in self.engine.results:
            assert 0 <= result.p_value <= 1, (
                f"{result.experiment_name}: p={result.p_value} out of range"
            )

    def test_confidence_interval_contains_effect(self):
        """The point estimate should be within the confidence interval."""
        self.engine.run_all_experiments()
        for result in self.engine.results:
            assert result.ci_lower <= result.absolute_lift <= result.ci_upper, (
                f"{result.experiment_name}: lift={result.absolute_lift} "
                f"not in [{result.ci_lower}, {result.ci_upper}]"
            )

    def test_power_range(self):
        """Statistical power should be between 0 and 1."""
        self.engine.run_all_experiments()
        for result in self.engine.results:
            assert 0 <= result.statistical_power <= 1, (
                f"{result.experiment_name}: power={result.statistical_power}"
            )

    def test_mde_is_positive(self):
        """MDE should always be positive."""
        self.engine.run_all_experiments()
        for result in self.engine.results:
            assert result.mde > 0, f"{result.experiment_name}: MDE={result.mde}"

    def test_discount_positive_lift(self):
        """15% discount should generally have higher AOV than 10%."""
        result = self.engine.simulate_discount_experiment(n_control=5000, n_treatment=5000)
        # With large sample and $7 difference, this should almost always be true
        assert result.treatment_mean > result.control_mean
        assert result.absolute_lift > 0
