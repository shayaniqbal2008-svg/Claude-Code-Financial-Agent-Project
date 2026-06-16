from unittest.mock import MagicMock, patch
import pytest
from agent.data import StockData, fetch_stock_data


def make_mock_ticker(info: dict, hist_prices: list[float], news: list[dict]):
    mock = MagicMock()
    mock.info = info
    import pandas as pd
    mock.history.return_value = pd.DataFrame(
        {"Close": hist_prices},
        index=pd.date_range("2025-06-15", periods=len(hist_prices), freq="D")
    )
    mock.news = news
    return mock


@patch("agent.data.yf.Ticker")
def test_fetch_stock_data_returns_stock_data(mock_ticker_cls):
    mock_ticker_cls.return_value = make_mock_ticker(
        info={
            "marketCap": 3_000_000_000_000,
            "profitMargins": 0.25,
            "totalCash": 50_000_000_000,
            "forwardPE": 28.5,
            "targetMeanPrice": 220.0,
            "currentPrice": 195.0,
            "fiftyTwoWeekHigh": 200.0,
            "fullTimeEmployees": 150_000,
            "country": "United States",
            "industry": "Consumer Electronics",
            "sector": "Technology",
        },
        hist_prices=[100.0, 195.0],
        news=[{"title": "Apple hits record", "publisher": "Reuters", "link": "http://x", "providerPublishTime": 1234567890}]
    )
    result = fetch_stock_data("AAPL")
    assert isinstance(result, StockData)
    assert result.ticker == "AAPL"
    assert result.market_cap == 3_000_000_000_000
    assert result.profit_margin == 0.25
    assert result.total_cash == 50_000_000_000
    assert result.forward_pe == 28.5
    assert result.analyst_mean_target == 220.0
    assert result.current_price == 195.0
    assert result.week_52_high == 200.0
    assert result.employees == 150_000
    assert result.country == "United States"
    assert abs(result.one_year_return - 0.95) < 0.01  # (195-100)/100
    assert len(result.news) == 1


@patch("agent.data.yf.Ticker")
def test_fetch_stock_data_handles_missing_fields(mock_ticker_cls):
    mock_ticker_cls.return_value = make_mock_ticker(
        info={},
        hist_prices=[],
        news=[]
    )
    result = fetch_stock_data("FAKE")
    assert result.ticker == "FAKE"
    assert result.market_cap is None
    assert result.one_year_return is None
    assert result.news == []


@patch("agent.data.yf.Ticker")
def test_fetch_stock_data_news_capped_at_five(mock_ticker_cls):
    news_items = [{"title": f"News {i}", "publisher": "X", "link": "", "providerPublishTime": i} for i in range(10)]
    mock_ticker_cls.return_value = make_mock_ticker(info={}, hist_prices=[], news=news_items)
    result = fetch_stock_data("TEST")
    assert len(result.news) == 5
