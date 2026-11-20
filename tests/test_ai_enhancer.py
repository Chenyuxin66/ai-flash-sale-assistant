"""
Tests for the AI integration layer.

All tests run offline: they use either the mock mode (AI_MOCK=1)
or verify the graceful fallback path when no API key is configured.
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai_client import AIClient
from src.ai_insight_enhancer import AIInsightEnhancer
from src.insight_generator import InsightGenerator
from src.registration_checker import RegistrationChecker


@pytest.fixture
def sample_df():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "sample_products.csv")
    return pd.read_csv(path)


@pytest.fixture
def mock_client(monkeypatch):
    monkeypatch.setenv("AI_MOCK", "1")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    return AIClient()


@pytest.fixture
def rule_report(sample_df):
    return InsightGenerator().generate(sample_df)


# --- AIClient ---

class TestAIClient:
    def test_mock_mode_returns_canned_response(self, mock_client):
        assert mock_client.mock is True
        assert mock_client.available is True  # mock mode can produce output
        out = mock_client.chat("system", "user")
        assert "本周核心结论" in out

    def test_no_key_is_unavailable(self, monkeypatch):
        monkeypatch.delenv("AI_API_KEY", raising=False)
        monkeypatch.delenv("AI_MOCK", raising=False)
        client = AIClient()
        assert client.available is False
        assert client.describe().startswith("AI: disabled")

    def test_chat_without_key_raises(self, monkeypatch):
        monkeypatch.delenv("AI_API_KEY", raising=False)
        monkeypatch.delenv("AI_MOCK", raising=False)
        client = AIClient()
        with pytest.raises(RuntimeError):
            client.chat("system", "user")

    def test_env_overrides(self, monkeypatch):
        monkeypatch.setenv("AI_API_KEY", "sk-test")
        monkeypatch.setenv("AI_MODEL", "test-model")
        client = AIClient()
        assert client.api_key == "sk-test"
        assert client.model == "test-model"


# --- AIInsightEnhancer ---

class TestEnhancer:
    def test_facts_block_contains_all_facts(self, sample_df, rule_report):
        enhancer = AIInsightEnhancer(AIClient())
        facts = enhancer._facts_block(sample_df, rule_report)
        assert "overview" in facts
        assert "top_performers" in facts
        assert "category_analysis" in facts
        assert sample_df.iloc[0]["product_id"] in facts

    def test_briefing_fallback_without_key(self, sample_df, rule_report, monkeypatch):
        monkeypatch.delenv("AI_API_KEY", raising=False)
        monkeypatch.delenv("AI_MOCK", raising=False)
        enhancer = AIInsightEnhancer(AIClient())
        out = enhancer.enhance_weekly_briefing(
            sample_df, rule_report, fallback="RULE REPORT")
        assert "RULE REPORT" in out
        assert "AI features not configured" in out

    def test_briefing_mock_mode(self, sample_df, rule_report, mock_client):
        enhancer = AIInsightEnhancer(mock_client)
        out = enhancer.enhance_weekly_briefing(sample_df, rule_report)
        assert "本周核心结论" in out
        assert "下期行动清单" in out

    def test_followup_fallback_without_key(self, sample_df, monkeypatch):
        monkeypatch.delenv("AI_API_KEY", raising=False)
        monkeypatch.delenv("AI_MOCK", raising=False)
        checker = RegistrationChecker()
        results = checker.check_all(sample_df)
        incomplete = checker.get_incomplete(results)
        enhancer = AIInsightEnhancer(AIClient())
        out = enhancer.enhance_followup_message(
            incomplete, "Seller A", fallback="TEMPLATE MSG")
        if incomplete:
            assert "TEMPLATE MSG" in out

    def test_followup_mock_mode(self, sample_df, mock_client):
        checker = RegistrationChecker()
        results = checker.check_all(sample_df)
        incomplete = checker.get_incomplete(results)
        enhancer = AIInsightEnhancer(mock_client)
        out = enhancer.enhance_followup_message(incomplete, "Seller A")
        assert "Deadline" in out or "deadline" in out.lower()
