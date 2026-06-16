from unittest.mock import MagicMock, patch
import pytest
from agent.data import StockData
from agent.news import fetch_macro_news, fetch_ticker_news


def make_stock(ticker: str, news: list[dict]) -> StockData:
    return StockData(
        ticker=ticker, market_cap=None, profit_margin=None, total_cash=None,
        forward_pe=None, one_year_return=None, analyst_mean_target=None,
        current_price=None, week_52_high=None, employees=None,
        country=None, industry=None, sector=None, news=news
    )


@patch("agent.news.NewsApiClient")
def test_fetch_macro_news_returns_articles(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.get_top_headlines.return_value = {
        "articles": [
            {"title": "Fed holds rates", "description": "Fed meeting summary",
             "source": {"name": "Reuters"}, "publishedAt": "2026-06-15T10:00:00Z",
             "url": "http://reuters.com/fed"}
        ]
    }
    result = fetch_macro_news("fake_key")
    assert len(result) >= 1
    assert result[0]["title"] == "Fed holds rates"
    assert result[0]["source"] == "Reuters"


@patch("agent.news.NewsApiClient")
def test_fetch_macro_news_filters_removed_articles(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.get_top_headlines.return_value = {
        "articles": [
            {"title": "[Removed]", "description": "", "source": {"name": "X"},
             "publishedAt": "2026-06-15T10:00:00Z", "url": "http://x.com"}
        ]
    }
    result = fetch_macro_news("fake_key")
    assert len(result) == 0


def test_fetch_ticker_news_indexes_by_ticker():
    stocks = [
        make_stock("AAPL", [{"title": "Apple news", "publisher": "Reuters",
                              "link": "http://r.com", "published_at": 123}]),
        make_stock("GOOGL", []),
    ]
    result = fetch_ticker_news(stocks)
    assert "AAPL" in result
    assert "GOOGL" in result
    assert result["AAPL"][0]["title"] == "Apple news"
    assert result["GOOGL"] == []


def test_fetch_ticker_news_empty_list():
    result = fetch_ticker_news([])
    assert result == {}
