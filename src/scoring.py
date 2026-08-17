"""
Flash Sale Product Scoring Module
==================================
Implements a weighted scoring model for Flash Sale product selection.

Score = 40% Historical GMV + 30% Conversion Rate + 20% Discount Competitiveness + 10% Seller Performance

Each dimension is normalized to 0-100 before weighting.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


# --- Configuration ---

SCORE_WEIGHTS = {
    "historical_gmv": 0.40,
    "conversion_rate": 0.30,
    "discount_competitiveness": 0.20,
    "seller_performance": 0.10,
}

STRATEGY_LABELS = {
    "top_performer": {
        "min_score": 75,
        "description": "High priority - allocate quota immediately",
    },
    "high_potential": {
        "min_score": 55,
        "description": "Good candidate - monitor and test in next flash sale",
    },
    "test": {
        "min_score": 35,
        "description": "Marginal - small quota for testing",
    },
    "low_priority": {
        "min_score": 0,
        "description": "Low priority - deprioritize or exclude",
    },
}


@dataclass
class ScoringResult:
    """Container for a single product's scoring result."""
    product_id: str
    product_name: str
    category: str
    flash_sale_score: float
    strategy_label: str
    dimension_scores: dict = field(default_factory=dict)
    recommendation: str = ""


class FlashSaleScorer:
    """
    Scores Flash Sale products based on a 5-dimension weighted model.

    Dimensions:
        1. Historical GMV (40%) - Product's past revenue contribution
        2. Conversion Rate (30%) - How well the product converts views to orders
        3. Discount Competitiveness (20%) - How attractive the flash discount is
        4. Seller Performance (10%) - Seller's rating and responsiveness

    Usage:
        scorer = FlashSaleScorer()
        results = scorer.score_products(df)
        scorer.export_results(results, "output.csv")
    """

    def __init__(self, weights: Optional[dict] = None):
        self.weights = weights or SCORE_WEIGHTS

    def _normalize(self, series: pd.Series, invert: bool = False) -> pd.Series:
        """Min-max normalize a series to 0-100 scale."""
        min_val = series.min()
        max_val = series.max()
        if max_val == min_val:
            return pd.Series([50.0] * len(series), index=series.index)
        normalized = (series - min_val) / (max_val - min_val) * 100
        if invert:
            normalized = 100 - normalized
        return normalized

    def _calculate_discount_competitiveness(self, discount_pct: pd.Series) -> pd.Series:
        """
        Calculate discount competitiveness score.
        Higher discount = more competitive, but with diminishing returns.
        Uses a sigmoid-like curve to avoid rewarding extreme discounts too heavily.
        """
        # Cap at 60% discount for scoring purposes (diminishing returns)
        capped = discount_pct.clip(upper=60)
        return (capped / 60) * 100

    def _calculate_seller_performance(
        self, rating: pd.Series, response_rate: pd.Series
    ) -> pd.Series:
        """
        Calculate seller performance from rating (1-5) and response rate (0-1).
        Weighted: 60% rating + 40% response rate.
        """
        rating_score = (rating / 5.0) * 100
        response_score = response_rate * 100
        return rating_score * 0.6 + response_score * 0.4

    def _assign_label(self, score: float) -> tuple:
        """Assign strategy label based on total score."""
        for label, config in STRATEGY_LABELS.items():
            if score >= config["min_score"]:
                return label, config["description"]
        return "low_priority", STRATEGY_LABELS["low_priority"]["description"]

    def score_products(self, df: pd.DataFrame) -> list[ScoringResult]:
        """
        Score all products in the dataframe.

        Expected columns:
            product_id, product_name, category, historical_gmv,
            conversion_rate, discount_pct, seller_rating, seller_response_rate

        Args:
            df: DataFrame with product data

        Returns:
            List of ScoringResult objects, sorted by score descending
        """
        # Validate required columns
        required = [
            "product_id", "product_name", "historical_gmv",
            "conversion_rate", "discount_pct", "seller_rating", "seller_response_rate",
        ]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Calculate dimension scores
        gmv_score = self._normalize(df["historical_gmv"])
        conv_score = self._normalize(df["conversion_rate"])
        discount_score = self._calculate_discount_competitiveness(df["discount_pct"])
        seller_score = self._calculate_seller_performance(
            df["seller_rating"], df["seller_response_rate"]
        )

        # Calculate weighted total
        total_score = (
            gmv_score * self.weights["historical_gmv"]
            + conv_score * self.weights["conversion_rate"]
            + discount_score * self.weights["discount_competitiveness"]
            + seller_score * self.weights["seller_performance"]
        )

        # Build results
        results = []
        for i, idx in enumerate(df.index):
            score = round(total_score.iloc[i], 2)
            label, desc = self._assign_label(score)
            results.append(ScoringResult(
                product_id=str(df.at[idx, "product_id"]),
                product_name=str(df.at[idx, "product_name"]),
                category=str(df.at[idx, "category"]) if "category" in df.columns else "N/A",
                flash_sale_score=score,
                strategy_label=label,
                dimension_scores={
                    "historical_gmv": round(gmv_score.iloc[i], 2),
                    "conversion_rate": round(conv_score.iloc[i], 2),
                    "discount_competitiveness": round(discount_score.iloc[i], 2),
                    "seller_performance": round(seller_score.iloc[i], 2),
                },
                recommendation=desc,
            ))

        # Sort by score descending
        results.sort(key=lambda x: x.flash_sale_score, reverse=True)
        return results

    def export_results(self, results: list[ScoringResult], output_path: str) -> None:
        """Export scoring results to CSV."""
        rows = []
        for r in results:
            row = {
                "product_id": r.product_id,
                "product_name": r.product_name,
                "category": r.category,
                "flash_sale_score": r.flash_sale_score,
                "strategy_label": r.strategy_label,
                "recommendation": r.recommendation,
            }
            row.update({f"dim_{k}": v for k, v in r.dimension_scores.items()})
            rows.append(row)
        pd.DataFrame(rows).to_csv(output_path, index=False)

    def get_summary(self, results: list[ScoringResult]) -> dict:
        """Get summary statistics of scoring results."""
        scores = [r.flash_sale_score for r in results]
        label_counts = {}
        for r in results:
            label_counts[r.strategy_label] = label_counts.get(r.strategy_label, 0) + 1
        return {
            "total_products": len(results),
            "avg_score": round(np.mean(scores), 2) if scores else 0,
            "max_score": round(max(scores), 2) if scores else 0,
            "min_score": round(min(scores), 2) if scores else 0,
            "label_distribution": label_counts,
        }
