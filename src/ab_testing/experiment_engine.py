"""
A/B Testing Engine — Statistical experiment framework.

Simulates three realistic e-commerce experiments:
  1. Checkout flow redesign (conversion rate)
  2. Email subject line test (open rate)
  3. Discount strategy test (average order value)

Uses two-proportion z-test, Welch's t-test, confidence intervals, and power analysis.
"""
import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)
np.random.seed(42)


@dataclass
class ExperimentResult:
    """Container for A/B test results."""
    experiment_name: str
    metric_name: str
    control_size: int
    treatment_size: int
    control_mean: float
    treatment_mean: float
    absolute_lift: float
    relative_lift_pct: float
    test_statistic: float
    p_value: float
    ci_lower: float
    ci_upper: float
    is_significant: bool
    mde: float
    statistical_power: float
    test_type: str


class ABTestEngine:
    """Runs and analyzes A/B test experiments."""

    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
        self.results = []

    def simulate_checkout_experiment(self, n_control=5000, n_treatment=5000):
        control = np.random.binomial(1, 0.032, n_control)
        treatment = np.random.binomial(1, 0.038, n_treatment)
        return self._run_proportion_test(control, treatment, "Checkout Flow Redesign", "conversion_rate")

    def simulate_email_experiment(self, n_control=10000, n_treatment=10000):
        control = np.random.binomial(1, 0.21, n_control)
        treatment = np.random.binomial(1, 0.23, n_treatment)
        return self._run_proportion_test(control, treatment, "Email Subject Line Test", "open_rate")

    def simulate_discount_experiment(self, n_control=3000, n_treatment=3000):
        control = np.clip(np.random.normal(85.0, 25.0, n_control), 5.0, None)
        treatment = np.clip(np.random.normal(92.0, 28.0, n_treatment), 5.0, None)
        return self._run_continuous_test(control, treatment, "Discount Strategy (10% vs 15%)", "avg_order_value")

    def _run_proportion_test(self, control, treatment, name, metric):
        c_s, t_s = control.sum(), treatment.sum()
        c_n, t_n = len(control), len(treatment)
        c_r, t_r = c_s / c_n, t_s / t_n
        observed = np.array([[c_s, c_n - c_s], [t_s, t_n - t_s]])
        chi2, p_value, _, _ = stats.chi2_contingency(observed)
        se = np.sqrt(c_r * (1 - c_r) / c_n + t_r * (1 - t_r) / t_n)
        z = stats.norm.ppf(1 - self.alpha / 2)
        diff = t_r - c_r
        mde = self._calc_mde(c_n, t_n, c_r)
        power = self._calc_power_prop(c_r, t_r, c_n, t_n)
        result = ExperimentResult(name, metric, c_n, t_n, round(c_r, 5), round(t_r, 5),
            round(diff, 5), round(diff / c_r * 100, 2) if c_r > 0 else 0,
            round(chi2, 4), round(p_value, 6), round(diff - z * se, 5), round(diff + z * se, 5),
            p_value < self.alpha, round(mde, 5), round(power, 4), "chi_square")
        self.results.append(result)
        return result

    def _run_continuous_test(self, control, treatment, name, metric):
        c_m, t_m = control.mean(), treatment.mean()
        diff = t_m - c_m
        t_stat, p_value = stats.ttest_ind(control, treatment, equal_var=False)
        se = np.sqrt(control.var(ddof=1) / len(control) + treatment.var(ddof=1) / len(treatment))
        t_crit = stats.t.ppf(1 - self.alpha / 2, df=min(len(control), len(treatment)) - 1)
        pooled = np.sqrt((control.var(ddof=1) + treatment.var(ddof=1)) / 2)
        mde = self._calc_mde_cont(len(control), len(treatment), pooled)
        power = self._calc_power_cont(c_m, t_m, control.std(ddof=1), treatment.std(ddof=1), len(control), len(treatment))
        result = ExperimentResult(name, metric, len(control), len(treatment),
            round(c_m, 2), round(t_m, 2), round(diff, 2),
            round(diff / c_m * 100, 2) if c_m > 0 else 0,
            round(t_stat, 4), round(p_value, 6),
            round(diff - t_crit * se, 4), round(diff + t_crit * se, 4),
            p_value < self.alpha, round(mde, 4), round(power, 4), "t_test")
        self.results.append(result)
        return result

    def _calc_mde(self, n1, n2, br):
        za, zb = stats.norm.ppf(1 - self.alpha / 2), stats.norm.ppf(0.8)
        return (za + zb) * np.sqrt(2 * br * (1 - br) / min(n1, n2))

    def _calc_mde_cont(self, n1, n2, ps):
        za, zb = stats.norm.ppf(1 - self.alpha / 2), stats.norm.ppf(0.8)
        return (za + zb) * ps * np.sqrt(1 / n1 + 1 / n2)

    def _calc_power_prop(self, p1, p2, n1, n2):
        pp = (p1 * n1 + p2 * n2) / (n1 + n2)
        se0 = np.sqrt(2 * pp * (1 - pp) / min(n1, n2))
        se1 = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
        za = stats.norm.ppf(1 - self.alpha / 2)
        return float(stats.norm.cdf((abs(p2 - p1) - za * se0) / se1))

    def _calc_power_cont(self, m1, m2, s1, s2, n1, n2):
        se = np.sqrt(s1**2 / n1 + s2**2 / n2)
        za = stats.norm.ppf(1 - self.alpha / 2)
        return float(stats.norm.cdf((abs(m2 - m1) - za * se) / se))

    def run_all_experiments(self):
        self.results = []
        self.simulate_checkout_experiment()
        self.simulate_email_experiment()
        self.simulate_discount_experiment()
        return self.results

    def results_to_dataframe(self):
        if not self.results: self.run_all_experiments()
        return pd.DataFrame([vars(r) for r in self.results])


if __name__ == "__main__":
    engine = ABTestEngine()
    engine.run_all_experiments()
    print(engine.results_to_dataframe().to_string(index=False))
