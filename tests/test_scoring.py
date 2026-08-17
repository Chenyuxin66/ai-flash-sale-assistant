"""
Tests for Flash Sale Product Scoring Module
"""

import sys
import os
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scoring import FlashSaleScorer, ScoringResult, SCORE_WEIGHTS, STRATEGY_LABELS


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame([
        {
            "product_id": "P001", "product_name": "Premium Headphones", "category": "Electronics",
            "historical_gmv": 20000, "conversion_rate": 0.09, "discount_pct": 35,
            "seller_rating": 4.8, "seller_response_rate": 0.95,
        },
        {
            "product_id": "P002", "product_name": "Basic Cable", "category": "Electronics",
            "historical_gmv": 500, "conversion_rate": 0.01, "discount_pct": 50,
            "seller_rating": 3.5, "seller_response_rate": 0.60,
        },
        {
            "product_id": "P003", "product_name": "Skincare Set", "category": "Beauty",
            "historical_gmv": 15000, "conversion_rate": 0.08, "discount_pct": 30,
            "seller_rating": 4.6, "seller_response_rate": 0.90,
        },
    ])


class TestFlashSaleScorer:
    def test_score_products_returns_results(self, sample_df):
        scorer = FlashSaleScorer()
        results = scorer.score_products(sample_df)
        assert len(results) == 3
        assert all(isinstance(r, ScoringResult) for r in results)

    def test_results_sorted_descending(self, sample_df):
        scorer = FlashSaleScorer()
        results = scorer.score_products(sample_df)
        scores = [r.flash_sale_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_top_product_is_high_gmv(self, sample_df):
        scorer = FlashSaleScorer()
        results = scorer.score_products(sample_df)
        assert results[0].product_id == "P001"  # Highest GMV and conversion

    def test_strategy_labels_assigned(self, sample_df):
        scorer = FlashSaleScorer()
        results = scorer.score_products(sample_df)
        for r in results:
            assert r.strategy_label in STRATEGY_LABELS

    def test_dimension_scores_sum_to_total(self, sample_df):
        """Weighted sum of dimension scores should approximately equal total score."""
        scorer = FlashSaleScorer()
        results = scorer.score_products(sample_df)
        for r in results:
            weighted_sum = sum(
                r.dimension_scores[dim] * weight
                for dim, weight in SCORE_WEIGHTS.items()
            )
            assert abs(r.flash_sale_score - round(weighted_sum, 2)) < 1.0

    def test_get_summary(self, sample_df):
        scorer = FlashSaleScorer()
        results = scorer.score_products(sample_df)
        summary = scorer.get_summary(results)
        assert summary["total_products"] == 3
        assert "avg_score" in summary
        assert "label_distribution" in summary

    def test_export_results(self, sample_df, tmp_path):
        scorer = FlashSaleScorer()
        results = scorer.score_products(sample_df)
        output = tmp_path / "scores.csv"
        scorer.export_results(results, str(output))
        assert output.exists()
        exported = pd.read_csv(output)
        assert len(exported) == 3

    def test_custom_weights(self, sample_df):
        custom_weights = {
            "historical_gmv": 0.25,
            "conversion_rate": 0.25,
            "discount_competitiveness": 0.25,
            "seller_performance": 0.25,
        }
        scorer = FlashSaleScorer(weights=custom_weights)
        results = scorer.score_products(sample_df)
        assert len(results) == 3

    def test_missing_columns_raises_error(self):
        scorer = FlashSaleScorer()
        bad_df = pd.DataFrame([{"product_id": "P001"}])
        with pytest.raises(ValueError, match="Missing required columns"):
            scorer.score_products(bad_df)

    def test_low_gmv_product_gets_low_label(self, sample_df):
        scorer = FlashSaleScorer()
        results = scorer.score_products(sample_df)
        # P002 has lowest GMV, conversion, and seller rating
        p002 = [r for r in results if r.product_id == "P002"][0]
        assert p002.strategy_label in ("low_priority", "test")
