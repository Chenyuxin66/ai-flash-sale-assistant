# AI Flash Sale Assistant - Product Requirements Document (PRD)

## 1. Product Overview

**Product Name**: AI Flash Sale Assistant  
**Version**: 1.0  
**Type**: B-end AI Operations Efficiency Tool  
**Target Users**: E-commerce Flash Sale Operations Teams (Flash Sale Owners, Category Operation Managers, Operation Interns)

## 2. Problem Statement

During Flash Sale operations, three major pain points were identified:

### Pain Point 1: Data Analysis is Time-Consuming
- Operators spend ~2 hours/week on: Dashboard export -> Data cleaning -> Analysis -> Summary writing
- The process is highly repetitive but currently manual

### Pain Point 2: Insight Generation Depends on Experience
- New operators seeing a GMV drop cannot quickly diagnose whether it's a pricing, traffic, or conversion issue
- Analysis quality varies significantly between team members

### Pain Point 3: Decision-Making Lacks Standardization
- Different operators use different analysis methods and frameworks
- No unified scoring criteria for product selection

## 3. Solution: Three Core Features

### Feature 1: AI Performance Insight Generator
**Priority**: P0 (MVP)

Automatically analyzes Flash Sale data and generates structured insights:
- **Top Performer Analysis**: Identifies top 5 products, analyzes success factors (high conversion, strong discount, seller quality)
- **Underperforming Analysis**: Identifies bottom 5 products, diagnoses root causes (low conversion, weak discount, poor seller metrics)
- **Action Recommendations**: Data-driven suggestions (GMV concentration risk, category allocation, stock alerts)

**Input**: Product CSV with historical_gmv, conversion_rate, discount_pct, seller metrics  
**Output**: Formatted insight report with 5 sections (Overview, Top Performers, Underperformers, Category Analysis, Recommendations)  
**Validation**: Before ~2h/week -> After ~30min/week

### Feature 2: AI Flash Sale Product Scoring
**Priority**: P1

Weighted scoring model for objective product selection:

```
Flash Sale Score = 40% * Historical GMV
                 + 30% * Conversion Rate
                 + 20% * Discount Competitiveness
                 + 10% * Seller Performance
```

Each dimension is min-max normalized to 0-100 before weighting.

**Strategy Labels**:
| Score Range | Label | Action |
|---|---|---|
| >= 75 | Top Performer | Allocate quota immediately |
| 55-74 | High Potential | Monitor and test in next flash sale |
| 35-54 | Test | Small quota for testing |
| < 35 | Low Priority | Deprioritize or exclude |

### Feature 3: AI Registration Assistant
**Priority**: P2

Validates seller submission completeness:
- **Required fields check**: Product link, SKU, Discount info, Stock info
- **Quality checks**: Minimum stock (100 units), minimum discount (20%)
- **Follow-up generation**: Auto-generates personalized messages for sellers with incomplete submissions

## 4. MVP Scope

**MVP includes**: Feature 1 (Insight Generator) only

**Rationale**:
- Simplest to implement (rule-based, no ML model training needed)
- Strongest user demand (weekly time savings is immediately measurable)
- Easiest to validate (clear before/after comparison)

**MVP excludes** (future iterations):
- Automated product selection (requires historical data integration)
- GMV prediction (requires ML model training)
- Real-time monitoring (requires API integration)

## 5. Technical Architecture

```
ai-flash-sale-assistant/
+-- src/
|   +-- scoring.py              # Feature 2: Product scoring model
|   +-- insight_generator.py    # Feature 1: Insight generation engine
|   +-- registration_checker.py # Feature 3: Registration validation
|   +-- cli.py                  # Command-line interface
+-- data/
|   +-- sample_products.csv     # Sample dataset (30 products)
+-- tests/
|   +-- test_scoring.py         # Unit tests
+-- docs/
|   +-- PRD.md                  # This document
```

**Tech Stack**:
- Python 3.10+
- pandas (data processing)
- click (CLI framework)
- pytest (testing)

## 6. Success Metrics

| Metric | Before | Target | Measurement |
|---|---|---|---|
| Weekly analysis time | ~2 hours | ~30 minutes | Time tracking |
| Product selection consistency | Varies by operator | Standardized scoring | Inter-operator variance |
| Registration follow-up time | ~1 hour/week | ~15 minutes/week | AM self-report |
| Selection accuracy | ~60% hit rate | ~75% hit rate | Post-sale analysis |

## 7. Future Roadmap

- **v1.1**: Integrate with Aeolus (TikTok data platform) API for automated data pulling
- **v1.2**: Add LLM-powered natural language insight generation (replace rule-based engine)
- **v1.3**: GMV prediction model using historical trend data
- **v2.0**: Web dashboard with real-time monitoring and alerts
