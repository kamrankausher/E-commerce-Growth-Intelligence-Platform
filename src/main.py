"""Pipeline runner for local execution."""
from src.ab_testing.engine import run_all_experiments
from src.churn_model.train import train_model
from src.utils.logger import get_logger

logger = get_logger(__name__)


if __name__ == "__main__":
    logger.info("Running A/B experiments")
    run_all_experiments()
    logger.info("Training churn model")
    train_model()
