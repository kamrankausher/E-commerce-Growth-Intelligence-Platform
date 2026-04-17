from src.ab_testing.engine import run_checkout_experiment, run_discount_experiment


def test_checkout_experiment_output():
    result = run_checkout_experiment(n=1000)
    assert 0 <= result.control_value <= 1
    assert 0 <= result.treatment_value <= 1
    assert 0 <= result.p_value <= 1


def test_discount_experiment_ci_ordering():
    result = run_discount_experiment(n=1000)
    assert result.ci_lower < result.ci_upper
