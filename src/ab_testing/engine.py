"""A/B testing simulation engine with statistical tests."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats
from src.utils.db import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)
RNG = np.random.default_rng(42)


@dataclass
class ExperimentResult:
    experiment_name: str
    metric_name: str
    test_name: str
    control_value: float
    treatment_value: float
    p_value: float
    ci_lower: float
    ci_upper: float
    mde: float
    is_significant: bool


def mde_binary(p_baseline: float, alpha: float = 0.05, power: float = 0.8, n_per_group: int = 5000) -> float:
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    return (z_alpha + z_beta) * np.sqrt(2 * p_baseline * (1 - p_baseline) / n_per_group)


def run_checkout_experiment(n: int = 8000) -> ExperimentResult:
    control = RNG.binomial(1, 0.45, size=n)
    treatment = RNG.binomial(1, 0.48, size=n)
    table = np.array([[control.sum(), n - control.sum()], [treatment.sum(), n - treatment.sum()]])
    chi2, p_value, _, _ = stats.chi2_contingency(table)
    uplift = treatment.mean() - control.mean()
    se = np.sqrt(control.mean() * (1 - control.mean()) / n + treatment.mean() * (1 - treatment.mean()) / n)
    ci = (uplift - 1.96 * se, uplift + 1.96 * se)
    return ExperimentResult(
        experiment_name="checkout_flow_change",
        metric_name="conversion_rate",
        test_name="chi_square",
        control_value=float(control.mean()),
        treatment_value=float(treatment.mean()),
        p_value=float(p_value),
        ci_lower=float(ci[0]),
        ci_upper=float(ci[1]),
        mde=float(mde_binary(control.mean(), n_per_group=n)),
        is_significant=bool(p_value < 0.05),
    )


def run_email_subject_experiment(n: int = 6000) -> ExperimentResult:
    control = RNG.binomial(1, 0.22, size=n)
    treatment = RNG.binomial(1, 0.245, size=n)
    table = np.array([[control.sum(), n - control.sum()], [treatment.sum(), n - treatment.sum()]])
    _, p_value, _, _ = stats.chi2_contingency(table)
    uplift = treatment.mean() - control.mean()
    se = np.sqrt(control.mean() * (1 - control.mean()) / n + treatment.mean() * (1 - treatment.mean()) / n)
    return ExperimentResult(
        experiment_name="email_subject_line",
        metric_name="open_rate",
        test_name="chi_square",
        control_value=float(control.mean()),
        treatment_value=float(treatment.mean()),
        p_value=float(p_value),
        ci_lower=float(uplift - 1.96 * se),
        ci_upper=float(uplift + 1.96 * se),
        mde=float(mde_binary(control.mean(), n_per_group=n)),
        is_significant=bool(p_value < 0.05),
    )


def run_discount_experiment(n: int = 5000) -> ExperimentResult:
    control = RNG.normal(loc=125, scale=35, size=n)
    treatment = RNG.normal(loc=132, scale=36, size=n)
    t_stat, p_value = stats.ttest_ind(treatment, control, equal_var=False)
    diff = treatment.mean() - control.mean()
    se = np.sqrt(treatment.var(ddof=1) / n + control.var(ddof=1) / n)
    dof = n * 2 - 2
    critical = stats.t.ppf(0.975, dof)
    return ExperimentResult(
        experiment_name="discount_strategy",
        metric_name="avg_order_value",
        test_name="t_test",
        control_value=float(control.mean()),
        treatment_value=float(treatment.mean()),
        p_value=float(p_value),
        ci_lower=float(diff - critical * se),
        ci_upper=float(diff + critical * se),
        mde=float(0.2 * control.std(ddof=1)),
        is_significant=bool(p_value < 0.05),
    )


def run_all_experiments() -> pd.DataFrame:
    results = [run_checkout_experiment(), run_email_subject_experiment(), run_discount_experiment()]
    df = pd.DataFrame([r.__dict__ for r in results])
    logger.info("Experiment summary:\n%s", df)

    engine = get_engine()
    df.to_sql("ab_test_results", engine, if_exists="append", index=False)
    logger.info("Stored %s experiment rows", len(df))
    return df


if __name__ == "__main__":
    run_all_experiments()
