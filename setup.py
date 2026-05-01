"""
setup.py - One-command setup for the E-commerce Growth Intelligence Platform.

Usage:
    python setup.py
"""
import os
import sys
import time
import io

# Fix Windows console encoding for emoji
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def main():
    start = time.time()
    print("=" * 70)
    print("  E-commerce Growth Intelligence Platform - Setup")
    print("=" * 70)
    print()

    # Step 1: Generate Data
    print("[1/4] Generating realistic e-commerce data...")
    print("-" * 50)
    from generate_fake_data import generate_fake_data
    generate_fake_data()
    print()

    # Step 2: Load into SQLite
    print("[2/4] Loading data into SQLite...")
    print("-" * 50)
    from data.load_data import load_all_data
    load_all_data()
    print()

    # Step 3: ML Pipeline
    print("[3/4] Running ML pipeline (Optuna + XGBoost + SHAP)...")
    print("-" * 50)
    from src.churn_model.train_pipeline import run_full_pipeline
    run_full_pipeline()
    print()

    # Step 4: A/B Testing
    print("[4/4] Running A/B test experiments...")
    print("-" * 50)
    from src.ab_testing.experiment_engine import ABTestEngine
    engine = ABTestEngine()
    results = engine.run_all_experiments()
    for r in results:
        sig = "SIGNIFICANT" if r.is_significant else "NOT SIGNIFICANT"
        print(f"  {r.experiment_name}: p={r.p_value:.4f} - {sig}")
    print()

    elapsed = time.time() - start
    print("=" * 70)
    print(f"  Setup complete in {elapsed:.1f} seconds!")
    print("=" * 70)
    print()
    print("  To start the dashboard:")
    print()
    print("    python -m uvicorn src.api.app:app --reload --port 8000")
    print()
    print("  Then open: http://localhost:8000")
    print()


if __name__ == "__main__":
    main()
