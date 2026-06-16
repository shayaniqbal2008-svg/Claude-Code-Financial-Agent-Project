from newsapi import NewsApiClient
from agent.data import StockData


def fetch_macro_news(api_key: str) -> list[dict]:
    client = NewsApiClient(api_key=api_key)
    articles = []
    for category in ["business", "technology", "general"]:
        try:
            response = client.get_top_headlines(country="us", category=category, page_size=20)
            articles.extend(response.get("articles", []))
        except Exception:
            continue

    return [
        {
            "title": a["title"],
            "description": a.get("description", ""),
            "source": a["source"]["name"],
            "published_at": a["publishedAt"],
            "url": a.get("url", ""),
        }
        for a in articles
        if a.get("title") and "[Removed]" not in a.get("title", "")
    ]


def fetch_ticker_news(stocks: list[StockData]) -> dict[str, list[dict]]:
    return {stock.ticker: stock.news for stock in stocks}
