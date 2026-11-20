"""
AI Insight Enhancer
====================
The bridge between the rule engine and the LLM.

Architecture (the "two-stage" design):
    Stage 1 - Rule engine (scoring / insight_generator / registration_checker)
              computes all FACTS: numbers, rankings, anomalies. Deterministic,
              verifiable, zero hallucination.
    Stage 2 - LLM receives ONLY those computed facts and produces what rules
              cannot: attribution analysis, risk narrative, prioritized
              action list, seller follow-up copy.

Because the model never invents numbers (it must cite the provided facts),
outputs stay grounded in data - this is the key design decision that makes
LLM integration safe for operations work.

Usage:
    from src.ai_client import AIClient
    from src.ai_insight_enhancer import AIInsightEnhancer

    client = AIClient()
    enhancer = AIInsightEnhancer(client)
    briefing = enhancer.enhance_weekly_briefing(df, insight_report)
    # or, on failure / no key:
    fallback = enhancer.enhance_weekly_briefing(df, insight_report, fallback=rule_report_text)
"""

import json
from typing import Optional

import pandas as pd

from src.ai_client import AIClient
from src.insight_generator import InsightReport

# Compact row template so prompts stay small even with hundreds of products
_ROW_FIELDS = [
    "product_id", "product_name", "category", "historical_gmv",
    "conversion_rate", "discount_pct", "seller_rating",
    "seller_response_rate", "stock_units",
]

BRIEFING_SYSTEM_PROMPT = """You are a senior e-commerce operations analyst for TikTok Shop Flash Sale campaigns (Southeast Asia market).

Rules you MUST follow:
1. Use ONLY the facts provided in the data block. NEVER invent or alter any number.
2. Every claim that involves a number must cite the number from the data block.
3. Be concise and operational: an operations intern should be able to act on your output immediately, without re-analysis.
4. Output in Markdown, in Chinese, with exactly these four sections:

## 本周核心结论
(2-4 bullets, each one sentence: the single most important takeaway)
## 重点商品解读
(attributions for the top and underperforming products listed in the data - explain WHY they perform well/badly, grouping similar products when patterns repeat)
## 风险与异常预警
(stock risk, GMV concentration, low conversion, seller quality - only risks actually supported by the data)
## 下期行动清单
(numbered, 3-6 items, each prefixed with 【高】/【中】/【低】 priority, each action specific to a product, category or seller group - not generic advice)"""

MOCK_FOLLOWUP = """Hi Seller Team,

During our Flash Sale registration check, we found the following items that need your attention:

1. Missing product link: FS003, FS017
2. Missing SKU info: FS008
3. Stock concern (below threshold): FS012, FS021
4. Discount below activity requirement: FS005

Please review and update the registration sheet by [Deadline: date].
If any item cannot be resolved in time, let us know so we can arrange replacement products.

Thanks for your support!"""

FOLLOWUP_SYSTEM_PROMPT = """You are an operations intern at TikTok Shop Malaysia writing follow-up messages to Account Managers (AMs) about Flash Sale registration issues.

Rules:
1. Use ONLY the product/issue facts provided. Do not invent product details.
2. Write in English (AMs are based in Malaysia), professional but brief.
3. Group products by issue type so the AM can resolve them in batches.
4. End with a clear deadline placeholder [Deadline: date] and a one-line escalation note.
5. Keep the whole message under 250 words."""


class AIInsightEnhancer:
    """Turns rule-engine facts into LLM-generated operational briefings."""

    def __init__(self, client: Optional[AIClient] = None):
        self.client = client or AIClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enhance_weekly_briefing(
        self,
        df: pd.DataFrame,
        report: InsightReport,
        fallback: str = "",
    ) -> str:
        """
        Generate the AI weekly briefing from rule-engine facts.

        Args:
            df: product dataframe (source of the report)
            report: rule-based InsightReport (the facts)
            fallback: rule-based report text to return if AI is unavailable

        Returns:
            Markdown briefing string (AI-generated, or fallback text).
        """
        if not self.client.available:
            return self._decorate_fallback(fallback, "AI features not configured - rule-based report shown.")

        facts = self._facts_block(df, report)
        user_prompt = (
            "Below are the computed facts from this week's Flash Sale candidate pool "
            "(produced by the rule engine - treat them as ground truth).\n\n"
            f"{facts}\n\n"
            "Generate the weekly briefing following the required four-section structure."
        )
        try:
            return self.client.chat(BRIEFING_SYSTEM_PROMPT, user_prompt,
                                    temperature=0.3, max_tokens=2000)
        except RuntimeError as exc:
            return self._decorate_fallback(
                fallback, f"AI call failed ({exc}) - rule-based report shown.")

    def enhance_followup_message(
        self,
        incomplete_results: list,
        seller_name: str = "Seller",
        fallback: str = "",
    ) -> str:
        """
        Generate an English AM follow-up message from registration anomalies.

        Args:
            incomplete_results: list of RegistrationCheckResult with issues
            seller_name: seller or AM name to address
            fallback: template-based message to return if AI is unavailable
        """
        if not self.client.available:
            return self._decorate_fallback(fallback, "AI features not configured - template message shown.")

        items = []
        for r in incomplete_results[:50]:  # cap prompt size
            items.append({
                "product_id": r.product_id,
                "product": r.product_name,
                "missing_fields": r.missing_fields,
                "issues": r.issues,
                "actions": r.follow_up_actions,
            })

        user_prompt = (
            f"Registration check found {len(incomplete_results)} products with problems "
            f"for seller/AM: {seller_name}. Facts:\n\n"
            f"{json.dumps(items, ensure_ascii=False, indent=1)}\n\n"
            "Write the follow-up message to the AM per the rules."
        )
        try:
            return self.client.chat(FOLLOWUP_SYSTEM_PROMPT, user_prompt,
                                    temperature=0.4, max_tokens=800,
                                    mock_response=MOCK_FOLLOWUP)
        except RuntimeError as exc:
            return self._decorate_fallback(
                fallback, f"AI call failed ({exc}) - template message shown.")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _facts_block(self, df: pd.DataFrame, report: InsightReport) -> str:
        """Serialize the rule-engine report into a compact, token-efficient block."""
        cols = [c for c in _ROW_FIELDS if c in df.columns]
        products = df[cols].to_dict(orient="records")

        facts = {
            "overview": report.overview,
            "key_metrics": report.metrics,
            "top_performers": report.top_performers,
            "underperformers": report.underperformers,
            "category_analysis": report.category_analysis,
            "rule_based_recommendations": report.recommendations,
            "all_products": products,
        }
        return json.dumps(facts, ensure_ascii=False, indent=1, default=str)

    @staticmethod
    def _decorate_fallback(text: str, reason: str) -> str:
        header = (
            f"> ℹ️ {reason}\n"
            f"> Configure `.env` (AI_API_KEY / AI_BASE_URL / AI_MODEL) to enable AI output.\n"
        )
        return f"{header}\n{text}" if text else header
