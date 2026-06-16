import json
from unittest.mock import MagicMock, patch
import pytest
from agent.data import StockData
from agent.screener import ScreenResult
from agent.analyst import analyze, CRITERIA_BLOCK


def make_screen_result(ticker: str, passed: bool = True) -> ScreenResult:
    data = StockData(
        ticker=ticker, market_cap=5_000_000_000, profit_margin=0.20,
        total_cash=500_000_000, forward_pe=25.0, one_year_return=0.30,
        analyst_mean_target=150.0, current_price=130.0, week_52_high=145.0,
        employees=5000, country="United States", industry="Semiconductors",
        sector="Technology", news=[]
    )
    return ScreenResult(ticker=ticker, passed_halal=True, passed_quant=passed,
                        failed_criteria=[], data=data)


VALID_REPORT = {
    "portfolio_review": [
        {"ticker": "AAPL", "grade": "A", "criteria_9_15_pass": [True]*7,
         "summary": "Strong position", "flags": []}
    ],
    "sell_alerts": [],
    "buy_candidates": [
        {"ticker": "NVDA", "rationale": "AI leader", "criteria_9_15_pass": [True]*7}
    ],
    "news_briefing": [
        {"headline": "Fed holds rates", "impact": "Positive for tech", "tickers_affected": ["AAPL"]}
    ],
    "market_political_alerts": [],
    "new_watchlist_candidates": ["AMD"]
}


@patch("agent.analyst.Anthropic")
def test_analyze_returns_dict(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(VALID_REPORT))]
    mock_client.messages.create.return_value = mock_message

    result = analyze(
        holdings=[{"ticker": "AAPL", "quantity": 10, "avg_cost": 180.0}],
        candidates=[make_screen_result("NVDA")],
        macro_news=[{"title": "Fed holds rates", "description": "", "source": "Reuters",
                     "published_at": "2026-06-15", "url": ""}],
        ticker_news={"AAPL": [], "NVDA": []},
        api_key="fake_key"
    )
    assert isinstance(result, dict)
    assert "portfolio_review" in result
    assert "sell_alerts" in result
    assert "buy_candidates" in result
    assert "news_briefing" in result
    assert "market_political_alerts" in result
    assert "new_watchlist_candidates" in result


@patch("agent.analyst.Anthropic")
def test_analyze_uses_prompt_caching(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(VALID_REPORT))]
    mock_client.messages.create.return_value = mock_message

    analyze(
        holdings=[], candidates=[], macro_news=[], ticker_news={}, api_key="fake_key"
    )
    call_kwargs = mock_client.messages.create.call_args
    # Extract messages from positional or keyword args
    if call_kwargs.kwargs.get("messages"):
        messages = call_kwargs.kwargs["messages"]
    else:
        messages = call_kwargs.args[0] if call_kwargs.args else []

    # Find content blocks with cache_control
    content_blocks = messages[0]["content"] if messages else []
    cache_blocks = [b for b in content_blocks if isinstance(b, dict) and b.get("cache_control")]
    assert len(cache_blocks) >= 1


def test_criteria_block_contains_all_15_criteria():
    for i in range(1, 16):
        assert str(i) in CRITERIA_BLOCK, f"Criterion {i} missing from CRITERIA_BLOCK"


@patch("agent.analyst.Anthropic")
def test_analyze_only_passes_candidates_that_passed_quant(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(VALID_REPORT))]
    mock_client.messages.create.return_value = mock_message

    passing = make_screen_result("NVDA", passed=True)
    failing = make_screen_result("JUNK", passed=False)

    analyze(
        holdings=[],
        candidates=[passing, failing],
        macro_news=[],
        ticker_news={},
        api_key="fake_key"
    )
    call_kwargs = mock_client.messages.create.call_args
    if call_kwargs.kwargs.get("messages"):
        messages = call_kwargs.kwargs["messages"]
    else:
        messages = call_kwargs.args[0]

    # The dynamic input text should contain NVDA but not JUNK
    dynamic_text = messages[0]["content"][-1]["text"]
    assert "NVDA" in dynamic_text
    assert "JUNK" not in dynamic_text
