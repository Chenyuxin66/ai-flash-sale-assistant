"""
AI Performance Insight Generator
=================================
Automated analysis engine for Flash Sale product performance.

Generates three types of insights:
    1. Top Performer Analysis - Best performing products and why
    2. Underperforming Analysis - Products that failed to meet expectations
    3. Action Recommendations - Data-driven suggestions for optimization

This module uses a rule-based engine (no external AI API required) that mimics
the "AI Prompt -> Human Verification" workflow used in actual operations.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class InsightReport:
    """Container for a complete insight report."""
    overview: dict = field(default_factory=dict)
    top_performers: list[dict] = field(default_factory=list)
    underperformers: list[dict] = field(default_factory=list)
    category_analysis: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


class InsightGenerator:
    """
    Generates performance insights from Flash Sale product data.

    This implements the "AI Insight Generator" feature from the product spec.
    In production, this would call an LLM API; here we use a rule-based engine
    that produces the same structured output.

    Usage:
        generator = InsightGenerator()
        report = generator.generate(df)
        print(generator.format_report(report))
    """

    # Thresholds for performance classification
    TOP_PERFORMER_PERCENTILE = 75
    UNDERPERFORMER_PERCENTILE = 25
    LOW_CONVERSION_THRESHOLD = 0.04
    HIGH_DISCOUNT_THRESHOLD = 40

    def generate(self, df: pd.DataFrame) -> InsightReport:
        """
        Generate a complete insight report from product data.

        Expected columns:
            product_id, product_name, category, historical_gmv,
            conversion_rate, discount_pct, original_price, flash_price,
            seller_rating, stock_units
        """
        report = InsightReport()

        # Overview
        report.overview = self._generate_overview(df)

        # Top performers
        report.top_performers = self._analyze_top_performers(df)

        # Underperformers
        report.underperformers = self._analyze_underperformers(df)

        # Category analysis
        report.category_analysis = self._analyze_by_category(df)

        # Recommendations
        report.recommendations = self._generate_recommendations(df, report)

        # Metrics
        report.metrics = self._calculate_metrics(df)

        return report

    def _generate_overview(self, df: pd.DataFrame) -> dict:
        """Generate overview statistics."""
        return {
            "total_products": len(df),
            "total_historical_gmv": round(df["historical_gmv"].sum(), 2),
            "avg_conversion_rate": round(df["conversion_rate"].mean(), 4),
            "avg_discount": round(df["discount_pct"].mean(), 1),
            "total_stock": int(df["stock_units"].sum()),
            "categories": df["category"].nunique(),
        }

    def _analyze_top_performers(self, df: pd.DataFrame) -> list[dict]:
        """Identify and analyze top performing products."""
        gmv_threshold = np.percentile(df["historical_gmv"], self.TOP_PERFORMER_PERCENTILE)
        conv_median = df["conversion_rate"].median()

        top_df = df[df["historical_gmv"] >= gmv_threshold].nlargest(5, "historical_gmv")

        results = []
        for _, row in top_df.iterrows():
            reasons = []
            if row["conversion_rate"] > conv_median:
                reasons.append(f"High conversion rate ({row['conversion_rate']:.1%} above median)")
            if row["discount_pct"] >= 35:
                reasons.append(f"Strong discount appeal ({row['discount_pct']:.0f}% off)")
            if row["seller_rating"] >= 4.5:
                reasons.append(f"Excellent seller rating ({row['seller_rating']:.1f})")

            results.append({
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "category": row["category"],
                "historical_gmv": row["historical_gmv"],
                "conversion_rate": row["conversion_rate"],
                "discount_pct": row["discount_pct"],
                "success_factors": reasons if reasons else ["Consistent solid performance across metrics"],
            })
        return results

    def _analyze_underperformers(self, df: pd.DataFrame) -> list[dict]:
        """Identify and analyze underperforming products."""
        gmv_threshold = np.percentile(df["historical_gmv"], self.UNDERPERFORMER_PERCENTILE)

        bottom_df = df[df["historical_gmv"] <= gmv_threshold].nsmallest(5, "historical_gmv")

        results = []
        for _, row in bottom_df.iterrows():
            issues = []
            if row["conversion_rate"] < self.LOW_CONVERSION_THRESHOLD:
                issues.append(
                    f"Low conversion rate ({row['conversion_rate']:.1%}) - "
                    f"consider improving product images/descriptions"
                )
            if row["discount_pct"] < 25:
                issues.append(
                    f"Weak discount ({row['discount_pct']:.0f}%) - "
                    f"insufficient price incentive for flash sale"
                )
            if row["seller_rating"] < 4.3:
                issues.append(
                    f"Below-average seller rating ({row['seller_rating']:.1f}) - "
                    f"may affect buyer trust"
                )
            if row["seller_response_rate"] < 0.80:
                issues.append(
                    f"Low seller response rate ({row['seller_response_rate']:.0%}) - "
                    f"customer service risk"
                )

            results.append({
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "category": row["category"],
                "historical_gmv": row["historical_gmv"],
                "conversion_rate": row["conversion_rate"],
                "discount_pct": row["discount_pct"],
                "issues": issues if issues else ["Below-median GMV performance"],
            })
        return results

    def _analyze_by_category(self, df: pd.DataFrame) -> list[dict]:
        """Analyze performance by product category."""
        results = []
        for category, group in df.groupby("category"):
            results.append({
                "category": category,
                "product_count": len(group),
                "total_gmv": round(group["historical_gmv"].sum(), 2),
                "avg_gmv": round(group["historical_gmv"].mean(), 2),
                "avg_conversion": round(group["conversion_rate"].mean(), 4),
                "avg_discount": round(group["discount_pct"].mean(), 1),
                "performance": self._rate_category_performance(group),
            })

        results.sort(key=lambda x: x["total_gmv"], reverse=True)
        return results

    def _rate_category_performance(self, group: pd.DataFrame) -> str:
        """Rate a category's overall performance."""
        avg_gmv = group["historical_gmv"].mean()
        avg_conv = group["conversion_rate"].mean()

        if avg_gmv > 15000 and avg_conv > 0.07:
            return "Excellent"
        elif avg_gmv > 8000 and avg_conv > 0.05:
            return "Good"
        elif avg_gmv > 4000:
            return "Average"
        else:
            return "Below Average"

    def _generate_recommendations(self, df: pd.DataFrame, report: InsightReport) -> list[str]:
        """Generate actionable recommendations based on analysis."""
        recs = []

        # GMV concentration analysis
        top_20_pct_gmv = df.nlargest(int(len(df) * 0.2), "historical_gmv")["historical_gmv"].sum()
        total_gmv = df["historical_gmv"].sum()
        concentration = top_20_pct_gmv / total_gmv if total_gmv > 0 else 0

        if concentration > 0.5:
            recs.append(
                f"GMV is highly concentrated: top 20% products account for "
                f"{concentration:.0%} of total GMV. "
                f"Consider diversifying product selection to reduce dependency risk."
            )

        # Conversion rate analysis
        low_conv_count = (df["conversion_rate"] < self.LOW_CONVERSION_THRESHOLD).sum()
        if low_conv_count > len(df) * 0.3:
            recs.append(
                f"{low_conv_count} products ({low_conv_count/len(df):.0%}) have conversion rate "
                f"below {self.LOW_CONVERSION_THRESHOLD:.0%}. "
                f"Review product images, titles, and pricing strategy for these items."
            )

        # Discount analysis
        high_discount = df[df["discount_pct"] >= self.HIGH_DISCOUNT_THRESHOLD]
        if len(high_discount) > 0:
            avg_conv_high = high_discount["conversion_rate"].mean()
            avg_conv_rest = df[df["discount_pct"] < self.HIGH_DISCOUNT_THRESHOLD]["conversion_rate"].mean()
            if avg_conv_high > avg_conv_rest:
                recs.append(
                    f"Products with >= {self.HIGH_DISCOUNT_THRESHOLD}% discount show "
                    f"{((avg_conv_high/avg_conv_rest)-1):.0%} higher conversion rate. "
                    f"Consider increasing discount depth for underperforming categories."
                )

        # Category insights
        if report.category_analysis:
            best_cat = report.category_analysis[0]
            worst_cat = report.category_analysis[-1]
            recs.append(
                f"Best performing category: {best_cat['category']} "
                f"(avg GMV: {best_cat['avg_gmv']:.0f}, conversion: {best_cat['avg_conversion']:.1%}). "
                f"Allocate more quota slots here."
            )
            if worst_cat["performance"] == "Below Average":
                recs.append(
                    f"Underperforming category: {worst_cat['category']} "
                    f"(avg GMV: {worst_cat['avg_gmv']:.0f}). "
                    f"Reduce quota allocation or improve product selection quality."
                )

        # Stock risk
        low_stock = df[df["stock_units"] < 200]
        if len(low_stock) > 0:
            recs.append(
                f"{len(low_stock)} products have stock below 200 units. "
                f"High sell-through risk during flash sale - coordinate with sellers to replenish."
            )

        if not recs:
            recs.append("Overall performance is balanced. Continue current strategy and monitor trends.")

        return recs

    def _calculate_metrics(self, df: pd.DataFrame) -> dict:
        """Calculate key performance metrics."""
        return {
            "gmv_concentration_top20": round(
                df.nlargest(int(len(df) * 0.2), "historical_gmv")["historical_gmv"].sum()
                / df["historical_gmv"].sum(), 4
            ),
            "avg_discount_depth": round(df["discount_pct"].mean(), 1),
            "stock_coverage_ratio": round(
                df["stock_units"].sum() / max(len(df) * 500, 1), 2
            ),
            "seller_quality_avg": round(df["seller_rating"].mean(), 2),
        }

    def format_report(self, report: InsightReport) -> str:
        """Format the insight report as a readable string."""
        lines = []
        lines.append("=" * 70)
        lines.append("  Flash Sale Weekly Insight Report")
        lines.append("=" * 70)

        # Overview
        ov = report.overview
        lines.append(f"\n[Overview]")
        lines.append(f"  Total Products: {ov['total_products']}")
        lines.append(f"  Total Historical GMV: {ov['total_historical_gmv']:,.0f}")
        lines.append(f"  Avg Conversion Rate: {ov['avg_conversion_rate']:.2%}")
        lines.append(f"  Avg Discount: {ov['avg_discount']:.1f}%")
        lines.append(f"  Categories: {ov['categories']}")

        # Top Performers
        lines.append(f"\n[Top Performers]")
        if report.top_performers:
            for i, p in enumerate(report.top_performers, 1):
                lines.append(f"  {i}. {p['product_name']} ({p['category']})")
                lines.append(f"     GMV: {p['historical_gmv']:,.0f} | Conv: {p['conversion_rate']:.2%} | Discount: {p['discount_pct']:.0f}%")
                for factor in p["success_factors"]:
                    lines.append(f"     -> {factor}")
        else:
            lines.append("  No top performers identified.")

        # Underperformers
        lines.append(f"\n[Underperforming Products]")
        if report.underperformers:
            for i, p in enumerate(report.underperformers, 1):
                lines.append(f"  {i}. {p['product_name']} ({p['category']})")
                lines.append(f"     GMV: {p['historical_gmv']:,.0f} | Conv: {p['conversion_rate']:.2%} | Discount: {p['discount_pct']:.0f}%")
                for issue in p["issues"]:
                    lines.append(f"     -> {issue}")
        else:
            lines.append("  No underperforming products identified.")

        # Category Analysis
        lines.append(f"\n[Category Analysis]")
        lines.append(f"  {'Category':<15} {'Count':>5} {'Total GMV':>12} {'Avg Conv':>10} {'Rating':>15}")
        lines.append(f"  {'-'*60}")
        for cat in report.category_analysis:
            lines.append(
                f"  {cat['category']:<15} {cat['product_count']:>5} "
                f"{cat['total_gmv']:>12,.0f} {cat['avg_conversion']:>10.2%} {cat['performance']:>15}"
            )

        # Recommendations
        lines.append(f"\n[Action Recommendations]")
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"  {i}. {rec}")

        # Metrics
        lines.append(f"\n[Key Metrics]")
        m = report.metrics
        lines.append(f"  GMV Concentration (Top 20%): {m['gmv_concentration_top20']:.1%}")
        lines.append(f"  Avg Discount Depth: {m['avg_discount_depth']:.1f}%")
        lines.append(f"  Stock Coverage Ratio: {m['stock_coverage_ratio']:.2f}x")
        lines.append(f"  Seller Quality (Avg Rating): {m['seller_quality_avg']:.2f}/5.0")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)
