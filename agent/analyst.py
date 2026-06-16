import json
from anthropic import Anthropic
from agent.screener import ScreenResult


SYSTEM_PROMPT = (
    "You are a financial analysis agent. Your sole decision framework is the 15 criteria provided. "
    "Do not add, remove, or reinterpret them. News and political developments are primary signals — "
    "weigh them heavily and surface conflicts between fundamentals and current events explicitly. "
    "Return ONLY valid JSON matching the specified schema. No prose outside the JSON."
)

CRITERIA_BLOCK = """
## The 15 Investment Criteria

### Quantitative (criteria 1–8 pre-screened — all passed for candidates listed below)
1. Market cap > $1 billion
2. Profit margin positive
3. Total cash positive and in millions minimum
4. Forward P/E positive
5. One-year price return > 15%
6. Current price ≤ analyst mean price target
7. Current price ≥ 80% of 52-week high (momentum filter)
8. Employee count > 1,000

### Qualitative (your evaluation — criteria 9–15)
9. NOT an Israeli company and NOT primarily funded by Israel-based sources
10. No significant war, political, or geopolitical exposure materially affecting the stock right now or imminently
11. Strong, robust technology with genuine growth potential
12. Fits AI-infrastructure theme — memory, storage, power, cooling, networking, or chips supporting AI data centers
13. Financial highlights overall positive — healthy trends, no major red flags
14. Acts as supplier or enabler to AI hyperscalers (NVDA, Google, Microsoft, Amazon, Meta) — parts, cables, memory, storage, power, cooling
15. GOOGL and AAPL are always standing positions — flag if underweight, never recommend selling without a significant and specific cause

## Output Schema
Return exactly this JSON structure (no other text):
{
  "portfolio_review": [
    {"ticker": "string", "grade": "A|B|C|D|F", "criteria_9_15_pass": [bool x7],
     "summary": "string", "flags": ["string"]}
  ],
  "sell_alerts": [
    {"ticker": "string", "reason": "string", "urgency": "high|medium|low"}
  ],
  "buy_candidates": [
    {"ticker": "string", "rationale": "string", "criteria_9_15_pass": [bool x7]}
  ],
  "news_briefing": [
    {"headline": "string", "impact": "string", "tickers_affected": ["string"]}
  ],
  "market_political_alerts": [
    {"event": "string", "market_impact": "string", "urgency": "high|medium|low"}
  ],
  "new_watchlist_candidates": ["string"]
}
"""


def analyze(
    holdings: list[dict],
    candidates: list[ScreenResult],
    macro_news: list[dict],
    ticker_news: dict[str, list[dict]],
    api_key: str,
    model: str = "claude-sonnet-4-6",
) -> dict:
    client = Anthropic(api_key=api_key)

    dynamic_input = json.dumps(
        {
            "current_holdings": holdings,
            "screened_candidates": [
                {
                    "ticker": c.ticker,
                    "market_cap": c.data.market_cap,
                    "profit_margin": c.data.profit_margin,
                    "forward_pe": c.data.forward_pe,
                    "one_year_return": c.data.one_year_return,
                    "current_price": c.data.current_price,
                    "week_52_high": c.data.week_52_high,
                    "country": c.data.country,
                    "industry": c.data.industry,
                    "sector": c.data.sector,
                }
                for c in candidates
                if c.passed_quant
            ],
            "macro_news_today": macro_news[:30],
            "ticker_news": ticker_news,
        },
        indent=2,
    )

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": CRITERIA_BLOCK,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": f"Analyze the following data and return the JSON report:\n\n{dynamic_input}",
                    },
                ],
            }
        ],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )

    return json.loads(response.content[0].text)
