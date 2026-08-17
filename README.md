# AI Flash Sale Assistant

> A B-end AI operations efficiency tool for e-commerce Flash Sale management — built from real TikTok Shop internship experience.

[![CI](https://github.com/Chenyuxin66/ai-flash-sale-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/Chenyuxin66/ai-flash-sale-assistant/actions)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-10%20passed-brightgreen.svg)](tests/)

> 🟢 **CI status:** every push to `main` automatically runs the full test suite (Python 3.10/3.11/3.12) plus an end-to-end demo smoke test on GitHub Actions.

## Overview

AI Flash Sale Assistant is a Python tool that automates three core Flash Sale operations workflows:
1. **Product Scoring** — Weighted scoring model for objective product selection
2. **Insight Generation** — Automated weekly performance analysis and recommendations
3. **Registration Check** — Seller submission completeness validation

This project originated from a real pain point identified during Flash Sale operations at TikTok Shop (Malaysia): operators spent ~2 hours/week on repetitive data analysis that could be automated.

## Features

### 1. Product Scoring Model (`scoring.py`)

Scores products using a 4-dimension weighted model:

```
Flash Sale Score = 40% × Historical GMV
                 + 30% × Conversion Rate
                 + 20% × Discount Competitiveness
                 + 10% × Seller Performance
```

Each dimension is normalized to 0-100, then weighted. Products are classified into strategy labels:

| Score | Label | Action |
|-------|-------|--------|
| ≥75 | Top Performer | Allocate quota immediately |
| 55-74 | High Potential | Monitor and test |
| 35-54 | Test | Small quota for testing |
| <35 | Low Priority | Deprioritize |

### 2. Insight Generator (`insight_generator.py`)

Generates a structured weekly report with 5 sections:
- **Overview** — Total products, GMV, avg conversion, avg discount
- **Top Performers** — Top 5 products with success factor analysis
- **Underperformers** — Bottom 5 products with issue diagnosis
- **Category Analysis** — Performance breakdown by category
- **Action Recommendations** — Data-driven optimization suggestions

### 3. Registration Checker (`registration_checker.py`)

Validates seller submissions for Flash Sale registration:
- Checks 4 required fields: Product link, SKU, Discount, Stock
- Quality checks: minimum stock (100), minimum discount (20%)
- Auto-generates follow-up messages for incomplete submissions

## Quick Start

### One-Click Demo (see it working in 10 seconds)

```bash
python demo.py
```

This runs the **entire workflow end-to-end** on the sample dataset — product scoring, weekly insight report generation, and seller registration check — and prints everything to the console. It is the fastest way to verify the tool works without reading any code.

### Installation

```bash
git clone https://github.com/Chenyuxin66/ai-flash-sale-assistant.git
cd ai-flash-sale-assistant
pip install -r requirements.txt
```

### Usage

```bash
# Score products and show top 10
python -m src.cli score -i data/sample_products.csv

# Generate weekly insight report
python -m src.cli insight -i data/sample_products.csv

# Check registration completeness
python -m src.cli check -i data/sample_products.csv --seller "ABC Store"

# Generate comprehensive report (all three combined)
python -m src.cli report -i data/sample_products.csv -o report.txt
```

### Example Output (Scoring)

```
============================================================
  Flash Sale Product Scoring Results
============================================================
  Total Products: 30
  Score Range: 12.5 - 89.3
  Average Score: 52.1

  Strategy Distribution:
    top_performer         5 products
    high_potential        8 products
    test                 10 products
    low_priority          7 products

  Top 5 Products:
  #   ID       Product                                  Score   Label
  --------------------------------------------------------------------------------
  1   FS013    Air Fryer 5L Digital                       89.3 top_performer
  2   FS018    Baby Formula Stage 2 900g                 85.7 top_performer
  3   FS003    Skincare Set Vitamin C                    83.2 top_performer
  ...
```

## Data Format

Input CSV should contain the following columns:

| Column | Type | Description |
|--------|------|-------------|
| product_id | string | Unique product identifier |
| product_name | string | Product display name |
| category | string | Product category |
| historical_gmv | float | Historical gross merchandise value |
| conversion_rate | float | View-to-order conversion rate (0-1) |
| discount_pct | float | Flash sale discount percentage |
| original_price | float | Original price |
| flash_price | float | Flash sale price |
| seller_rating | float | Seller rating (1-5) |
| seller_response_rate | float | Seller response rate (0-1) |
| stock_units | int | Available stock units |
| product_link | string | Product page URL |
| sku | string | Stock keeping unit |
| has_discount | string | "Yes" / "No" |
| has_stock | string | "Yes" / "No" |

See `data/sample_products.csv` for a complete example with 30 products.

## Project Structure

```
ai-flash-sale-assistant/
├── src/
│   ├── __init__.py
│   ├── scoring.py              # Product scoring model
│   ├── insight_generator.py    # Performance analysis engine
│   ├── registration_checker.py # Registration validation
│   └── cli.py                  # CLI interface
├── data/
│   └── sample_products.csv     # Sample dataset (30 products)
├── tests/
│   └── test_scoring.py         # Unit tests
├── docs/
│   └── PRD.md                  # Product requirements document
├── requirements.txt
├── .gitignore
└── README.md
```

## Testing

```bash
pip install pytest
pytest tests/ -v
```

## Customization

### Custom Scoring Weights

```python
from src.scoring import FlashSaleScorer

custom_weights = {
    "historical_gmv": 0.50,
    "conversion_rate": 0.25,
    "discount_competitiveness": 0.15,
    "seller_performance": 0.10,
}
scorer = FlashSaleScorer(weights=custom_weights)
```

### Custom Strategy Labels

Modify `STRATEGY_LABELS` in `src/scoring.py`:

```python
STRATEGY_LABELS = {
    "must_have": {"min_score": 80, "description": "Must include in flash sale"},
    "recommended": {"min_score": 60, "description": "Strongly recommended"},
    ...
}
```

## Tech Stack

- **Python 3.10+**
- **pandas** — Data processing and analysis
- **click** — CLI framework
- **pytest** — Testing

## Background & Origin Story

### The pain point (from real internship experience)

During my internship at **TikTok Shop (Malaysia) — Lifestyle Category Operations**, I noticed Flash Sale selection was done mostly **manually in Excel**:

- Operators scored products **by gut feeling** instead of a consistent formula — the same product could get different scores from different people.
- Weekly performance analysis took **~2 hours** of copy-pasting and pivot tables.
- Seller registrations arrived with **missing fields** (no SKU, no discount, no stock), and follow-ups were typed out one by one.

None of this was a "product" yet — it was my observation of how the team actually worked, and the inefficiencies I could quantify.

### From observation to tool

I turned that observation into a **product idea** (full PRD in `docs/PRD.md`): an AI assistant that automates the three most repetitive workflows — *scoring, insight, registration check*.

Then I went one step further and **implemented it as a runnable Python tool**:

- Designed a **weighted scoring model** (GMV 40% / Conversion 30% / Discount 20% / Seller 10%) that encodes the selection logic we used in operations — making decisions **objective and reproducible**.
- Built a **rule-based insight engine** that mimics the "AI generates → human verifies" workflow used in production, producing the same structured weekly report.
- Built a **registration checker** that auto-generates seller follow-up messages — the exact outreach flow I used to write by hand.

### Why this project matters

| Before (manual) | After (this tool) |
|---|---|
| Subjective, inconsistent product scoring | Consistent, explainable weighted score |
| ~2h/week manual analysis | Seconds, reproducible weekly report |
| Missed seller fields caught after the fact | Instant validation + auto follow-up |
| No audit trail of decisions | Every score is traceable to its inputs |

This project demonstrates: **product sense** (finding a real ops pain point and quantifying it), **execution** (turning an idea into working code with tests and docs), and **business impact thinking** (every feature maps to a time-saving workflow).

## License

MIT License — see [LICENSE](LICENSE) for details.
