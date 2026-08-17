"""
AI Flash Sale Assistant - CLI Interface
========================================
Command-line tool for Flash Sale operations.

Commands:
    score    - Score products and generate strategy labels
    insight  - Generate weekly performance insight report
    check    - Validate seller registration completeness
    report   - Generate a comprehensive report (all three combined)

Usage:
    python -m src.cli score --input data/sample_products.csv
    python -m src.cli insight --input data/sample_products.csv
    python -m src.cli check --input data/sample_products.csv
    python -m src.cli report --input data/sample_products.csv --output report.txt
"""

import sys
import os
import click
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scoring import FlashSaleScorer
from src.insight_generator import InsightGenerator
from src.registration_checker import RegistrationChecker


def load_data(file_path: str) -> pd.DataFrame:
    """Load product data from CSV file."""
    if not os.path.exists(file_path):
        click.echo(f"Error: File not found: {file_path}", err=True)
        sys.exit(1)
    return pd.read_csv(file_path)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """AI Flash Sale Assistant - E-commerce Flash Sale Operations Tool"""
    pass


@cli.command()
@click.option("--input", "-i", "input_path", required=True, help="Path to product CSV file")
@click.option("--output", "-o", "output_path", default=None, help="Output CSV path for scores")
@click.option("--top", "-t", default=10, help="Show top N products")
def score(input_path, output_path, top):
    """Score products and generate strategy labels."""
    df = load_data(input_path)
    scorer = FlashSaleScorer()
    results = scorer.score_products(df)

    # Summary
    summary = scorer.get_summary(results)
    click.echo("\n" + "=" * 60)
    click.echo("  Flash Sale Product Scoring Results")
    click.echo("=" * 60)
    click.echo(f"  Total Products: {summary['total_products']}")
    click.echo(f"  Score Range: {summary['min_score']} - {summary['max_score']}")
    click.echo(f"  Average Score: {summary['avg_score']}")
    click.echo(f"\n  Strategy Distribution:")
    for label, count in summary["label_distribution"].items():
        click.echo(f"    {label:<20} {count:>3} products")

    # Top products
    click.echo(f"\n  Top {min(top, len(results))} Products:")
    click.echo(f"  {'#':<3} {'ID':<8} {'Product':<40} {'Score':>7} {'Label':<18}")
    click.echo(f"  {'-'*80}")
    for i, r in enumerate(results[:top], 1):
        name = r.product_name[:38] if len(r.product_name) > 38 else r.product_name
        click.echo(f"  {i:<3} {r.product_id:<8} {name:<40} {r.flash_sale_score:>7.1f} {r.strategy_label:<18}")

    # Dimension breakdown for top 3
    click.echo(f"\n  Dimension Breakdown (Top 3):")
    for r in results[:3]:
        click.echo(f"\n  {r.product_name}:")
        click.echo(f"    Historical GMV:          {r.dimension_scores['historical_gmv']:>6.1f} (weight: 40%)")
        click.echo(f"    Conversion Rate:         {r.dimension_scores['conversion_rate']:>6.1f} (weight: 30%)")
        click.echo(f"    Discount Competitiveness:{r.dimension_scores['discount_competitiveness']:>6.1f} (weight: 20%)")
        click.echo(f"    Seller Performance:      {r.dimension_scores['seller_performance']:>6.1f} (weight: 10%)")
        click.echo(f"    -> {r.recommendation}")

    # Export
    if output_path:
        scorer.export_results(results, output_path)
        click.echo(f"\n  Results exported to: {output_path}")

    click.echo("")


@cli.command()
@click.option("--input", "-i", "input_path", required=True, help="Path to product CSV file")
@click.option("--output", "-o", "output_path", default=None, help="Output file path for report")
def insight(input_path, output_path):
    """Generate weekly performance insight report."""
    df = load_data(input_path)
    generator = InsightGenerator()
    report = generator.generate(df)

    formatted = generator.format_report(report)
    click.echo(formatted)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted)
        click.echo(f"\n  Report saved to: {output_path}")


@cli.command()
@click.option("--input", "-i", "input_path", required=True, help="Path to product CSV file")
@click.option("--seller", "-s", default="Seller", help="Seller name for follow-up message")
@click.option("--output", "-o", "output_path", default=None, help="Output file path")
def check(input_path, seller, output_path):
    """Validate seller registration completeness."""
    df = load_data(input_path)
    checker = RegistrationChecker()
    results = checker.check_all(df)

    summary = checker.format_summary(results)
    click.echo(summary)

    # Show follow-up message for incomplete
    incomplete = checker.get_incomplete(results)
    if incomplete:
        click.echo("\n" + "-" * 60)
        click.echo("  Follow-up Message for Seller:")
        click.echo("-" * 60)
        msg = checker.generate_followup_message(results, seller)
        click.echo(msg)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
            if incomplete:
                f.write("\n\n")
                f.write(checker.generate_followup_message(results, seller))
        click.echo(f"\n  Report saved to: {output_path}")


@cli.command()
@click.option("--input", "-i", "input_path", required=True, help="Path to product CSV file")
@click.option("--output", "-o", "output_path", default=None, help="Output file path")
def report(input_path, output_path):
    """Generate a comprehensive report (scoring + insight + registration check)."""
    df = load_data(input_path)

    sections = []

    # Section 1: Scoring
    scorer = FlashSaleScorer()
    results = scorer.score_products(df)
    summary = scorer.get_summary(results)

    sections.append("=" * 70)
    sections.append("  AI Flash Sale Assistant - Comprehensive Report")
    sections.append("=" * 70)

    sections.append(f"\n{'='*70}")
    sections.append("  Part 1: Product Scoring")
    sections.append(f"{'='*70}")
    sections.append(f"  Total Products: {summary['total_products']}")
    sections.append(f"  Score Range: {summary['min_score']} - {summary['max_score']}")
    sections.append(f"  Average Score: {summary['avg_score']}")
    sections.append(f"\n  Strategy Distribution:")
    for label, count in summary["label_distribution"].items():
        sections.append(f"    {label:<20} {count:>3} products")
    sections.append(f"\n  Top 5 Products:")
    for i, r in enumerate(results[:5], 1):
        sections.append(f"    {i}. {r.product_name} - Score: {r.flash_sale_score} ({r.strategy_label})")

    # Section 2: Insight
    generator = InsightGenerator()
    insight_report = generator.generate(df)
    sections.append(f"\n{'='*70}")
    sections.append("  Part 2: Performance Insights")
    sections.append(f"{'='*70}")
    sections.append(generator.format_report(insight_report))

    # Section 3: Registration Check
    checker = RegistrationChecker()
    reg_results = checker.check_all(df)
    sections.append(f"\n{'='*70}")
    sections.append("  Part 3: Registration Status")
    sections.append(f"{'='*70}")
    sections.append(checker.format_summary(reg_results))

    output_text = "\n".join(sections)
    click.echo(output_text)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        click.echo(f"\n  Report saved to: {output_path}")


if __name__ == "__main__":
    cli()
