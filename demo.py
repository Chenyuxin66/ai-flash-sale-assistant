#!/usr/bin/env python3
"""
AI Flash Sale Assistant - One-Click Demo
=========================================
Runs the complete end-to-end workflow with the sample dataset:

    1. Product Scoring      -> FlashSaleScorer (weighted selection model)
    2. Insight Generation   -> InsightGenerator (weekly performance report)
    3. Registration Check   -> RegistrationChecker (seller submission validation)

Usage:
    python demo.py

This script is the fastest way to see what the tool does without reading code.
No external API calls - everything runs locally on the sample dataset.
"""

import os
import sys

# Ensure the package root is importable regardless of CWD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from src.scoring import FlashSaleScorer
from src.insight_generator import InsightGenerator
from src.registration_checker import RegistrationChecker

DEMO_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_products.csv")


def section(title: str) -> None:
    """Print a section banner."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main() -> int:
    # ---------------------------------------------------------------
    # 0. Load data
    # ---------------------------------------------------------------
    print("AI Flash Sale Assistant - End-to-End Demo")
    print(f"Loading sample dataset: {DEMO_DATA}")
    df = pd.read_csv(DEMO_DATA)
    print(f"Loaded {len(df)} products across {df['category'].nunique()} categories.\n")

    # ---------------------------------------------------------------
    # 1. Product Scoring
    # ---------------------------------------------------------------
    section("STEP 1 | Product Scoring (Flash Sale Score)")
    scorer = FlashSaleScorer()
    results = scorer.score_products(df)
    summary = scorer.get_summary(results)

    print(f"Total Products     : {summary['total_products']}")
    print(f"Score Range        : {summary['min_score']} - {summary['max_score']}")
    print(f"Average Score      : {summary['avg_score']}")
    print("\nStrategy Distribution:")
    for label, count in sorted(summary["label_distribution"].items(),
                               key=lambda kv: -kv[1]):
        print(f"  {label:<20} {count} products")

    print("\nTop 5 Products:")
    print(f"  {'#':<3} {'ID':<8} {'Product':<32} {'Score':>6}  {'Label'}")
    print("  " + "-" * 66)
    for i, r in enumerate(results[:5], 1):
        print(f"  {i:<3} {r.product_id:<8} {r.product_name[:30]:<32} {r.flash_sale_score:>6.1f}  {r.strategy_label}")

    # ---------------------------------------------------------------
    # 2. Insight Generation
    # ---------------------------------------------------------------
    section("STEP 2 | Insight Generation (Weekly Report)")
    generator = InsightGenerator()
    report = generator.generate(df)
    print(generator.format_report(report))

    # ---------------------------------------------------------------
    # 3. Registration Check
    # ---------------------------------------------------------------
    section("STEP 3 | Registration Check (Seller Submission)")
    checker = RegistrationChecker()
    check_results = checker.check_all(df)
    completion_rate = checker.get_completion_rate(check_results)

    print(checker.format_summary(check_results))

    incomplete = checker.get_incomplete(check_results)
    if incomplete:
        print("\n[Sample Follow-up Message - auto-generated for seller outreach]")
        print("-" * 70)
        sample_message = checker.generate_followup_message(
            check_results[:8], seller_name="ABC Store"
        )
        print(sample_message)

    # ---------------------------------------------------------------
    # Wrap up
    # ---------------------------------------------------------------
    section("DEMO COMPLETE")
    print("All 3 core workflows executed successfully on the sample dataset.")
    print("Try the CLI for more control:")
    print("  python -m src.cli score  -i data/sample_products.csv")
    print("  python -m src.cli insight -i data/sample_products.csv")
    print("  python -m src.cli check  -i data/sample_products.csv --seller \"ABC Store\"")

    return 0


if __name__ == "__main__":
    sys.exit(main())
