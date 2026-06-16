from dataclasses import dataclass, field
import yfinance as yf


@dataclass
class StockData:
    ticker: str
    market_cap: float | None
    profit_margin: float | None
    total_cash: float | None
    forward_pe: float | None
    one_year_return: float | None
    analyst_mean_target: float | None
    current_price: float | None
    week_52_high: float | None
    employees: int | None
    country: str | None
    industry: str | None
    sector: str | None
    news: list[dict] = field(default_factory=list)


def fetch_stock_data(ticker: str) -> StockData:
    t = yf.Ticker(ticker)
    info = t.info

    one_year_return = None
    try:
        hist = t.history(period="1y")
        if len(hist) >= 2:
            start = hist["Close"].iloc[0]
            end = hist["Close"].iloc[-1]
            if start > 0:
                one_year_return = (end - start) / start
    except Exception:
        pass

    raw_news = t.news or []
    news = [
        {
            "title": n.get("title", ""),
            "publisher": n.get("publisher", ""),
            "link": n.get("link", ""),
            "published_at": n.get("providerPublishTime", 0),
        }
        for n in raw_news[:5]
    ]

    return StockData(
        ticker=ticker,
        market_cap=info.get("marketCap"),
        profit_margin=info.get("profitMargins"),
        total_cash=info.get("totalCash"),
        forward_pe=info.get("forwardPE"),
        one_year_return=one_year_return,
        analyst_mean_target=info.get("targetMeanPrice"),
        current_price=info.get("currentPrice") or info.get("regularMarketPrice"),
        week_52_high=info.get("fiftyTwoWeekHigh"),
        employees=info.get("fullTimeEmployees"),
        country=info.get("country"),
        industry=info.get("industry"),
        sector=info.get("sector"),
        news=news,
    )
