"""
AI API Client (OpenAI-compatible)
==================================
Lightweight client that talks to any OpenAI-compatible chat API:
DeepSeek, Zhipu GLM, Moonshot, Qwen, OpenAI, etc.

Configuration (env vars or a `.env` file in the project root):
    AI_API_KEY   - your API key (required to enable AI features)
    AI_BASE_URL  - API base URL (default: https://api.deepseek.com/v1)
    AI_MODEL     - model name        (default: deepseek-chat)
    AI_MOCK      - set to "1" to return a canned response (for tests/CI, no network)

Design principle:
    The rule engine computes the facts; the LLM only interprets them.
    If no API key is configured, every AI feature degrades gracefully
    to the rule-based output instead of crashing.
"""

import os
import json
from pathlib import Path

import requests


# Defaults point to DeepSeek: OpenAI-compatible, low cost, accessible
# from mainland China without a VPN, and strong at Chinese business writing.
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"
REQUEST_TIMEOUT = 60  # seconds


def _load_dotenv(project_root: Path) -> dict:
    """Minimal .env loader (KEY=VALUE lines, # comments). No extra dependency."""
    values = {}
    env_file = project_root / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"').strip("'")
    return values


MOCK_RESPONSE = """## 本周核心结论
1. 候选池整体表现健康，但 GMV 集中度偏高：前 20% 商品贡献过半 GMV，选品名单对头部商品依赖较大。
2. 折扣深度与转化率正相关，高折扣商品转化明显更好，部分低转化商品价格吸引力不足。
3. 存在库存偏低的头部商品，活动期间有售罄风险，需要提前补货或准备替补商品。

## 重点商品解读
- 头部商品的历史 GMV 与转化率均高于中位数，属于「有销售基础 + 有成交能力」的稳推型商品，建议优先锁定名额。
- 尾部商品主要卡在转化率与折扣深度两处：转化低说明承接（主图/详情/评价）有问题，折扣浅说明活动价格吸引力不够，两类问题要分开处理。

## 风险与异常预警
- 低库存商品在闪购流量放大后可能提前售罄，既浪费坑位也可能带来超卖投诉。
- GMV 集中在少数商品上，一旦头部商品异常（下架/库存不足），整场活动产出会明显波动。

## 下期行动清单
1. 【高】对低库存高分商品逐个确认补货时间，补不上的立即启用替补名单。
2. 【高】对高 GMV 未覆盖类目定向补选品，把名额向这类类目倾斜。
3. 【中】对低转化商品先改 Listing 承接，再考虑加折扣，避免纯靠让价拉转化。
4. 【中】持续追踪本期入选商品的实际活动 GMV，积累数据用于校准评分权重。"""


class AIClient:
    """OpenAI-compatible chat client with graceful degradation and mock mode."""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        project_root = Path(__file__).resolve().parent.parent
        env = _load_dotenv(project_root)

        self.api_key = api_key or os.environ.get("AI_API_KEY") or env.get("AI_API_KEY", "")
        self.base_url = (base_url or os.environ.get("AI_BASE_URL")
                         or env.get("AI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.model = model or os.environ.get("AI_MODEL") or env.get("AI_MODEL") or DEFAULT_MODEL

        self.mock = (os.environ.get("AI_MOCK") or env.get("AI_MOCK") or "").strip() == "1"
        self.last_error: str = ""

    @property
    def available(self) -> bool:
        """True when a chat() call can produce output (mock mode or key set)."""
        return bool(self.api_key) or self.mock

    def chat(self, system_prompt: str, user_prompt: str,
             temperature: float = 0.3, max_tokens: int = 2000,
             mock_response: str = None) -> str:
        """
        Send a chat completion request and return the assistant message text.

        Args:
            mock_response: canned text returned in mock mode (falls back to
                the default MOCK_RESPONSE when not provided).

        Raises a RuntimeError with a readable message on failure;
        callers should catch it and fall back to rule-based output.
        """
        if self.mock:
            return mock_response if mock_response is not None else MOCK_RESPONSE

        if not self.api_key:
            raise RuntimeError("AI_API_KEY is not configured.")

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(url, headers=headers,
                                 data=json.dumps(payload), timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            self.last_error = f"Network error: {exc}"
            raise RuntimeError(self.last_error) from exc

        if resp.status_code != 200:
            self.last_error = f"API returned HTTP {resp.status_code}: {resp.text[:300]}"
            raise RuntimeError(self.last_error)

        try:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, ValueError) as exc:
            self.last_error = f"Unexpected API response format: {resp.text[:300]}"
            raise RuntimeError(self.last_error) from exc

    def describe(self) -> str:
        """Human-readable description of the current AI configuration."""
        if self.mock:
            return "AI: MOCK mode (AI_MOCK=1) - canned response, no network calls"
        if not self.api_key:
            return ("AI: disabled (no API key) - falling back to rule-based output. "
                    "Set AI_API_KEY in .env to enable.")
        return f"AI: enabled - model={self.model} @ {self.base_url}"
