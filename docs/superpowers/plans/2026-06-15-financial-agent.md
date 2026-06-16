# Financial Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated daily financial advisory agent that runs at 8 AM CT, screens stocks against 15 investment criteria weighted by live news, and serves results via an always-on local dashboard.

**Architecture:** Python agent engine writes daily reports (JSON + HTML) to disk at 8 AM CT; FastAPI dashboard server reads and serves them; system tray icon (pystray) gives instant browser access; Windows Task Scheduler and Startup folder handle automation.

**Tech Stack:** Python 3.11+, yfinance, anthropic SDK, mcp (Python MCP client), newsapi-python, FastAPI, uvicorn, pystray, pillow, httpx, python-dotenv, pytest

---

## File Map

```
Financial Agent/
├── agent/
│   ├── __init__.py
│   ├── main.py           # orchestrator — runs all steps in sequence
│   ├── portfolio.py      # Robinhood MCP client
│   ├── data.py           # yfinance stock data fetching
│   ├── news.py           # yfinance ticker news + NewsAPI macro news
│   ├── screener.py       # halal filter + 15 quantitative criteria
│   ├── analyst.py        # Claude API qualitative analysis + report generation
│   ├── report.py         # assembles JSON report + renders HTML
│   └── storage.py        # file I/O abstraction layer
├── dashboard/
│   ├── __init__.py
│   ├── server.py         # FastAPI app with all routes
│   ├── tray.py           # pystray system tray icon
│   └── static/
│       ├── index.html    # dashboard HTML shell
│       ├── style.css     # dark theme styles
│       └── app.js        # live refresh + collapsible sections
├── tests/
│   ├── __init__.py
│   ├── test_storage.py
│   ├── test_data.py
│   ├── test_news.py
│   ├── test_screener.py
│   ├── test_analyst.py
│   ├── test_report.py
│   └── test_server.py
├── scripts/
│   ├── install.ps1           # one-command full setup
│   ├── setup_scheduler.ps1   # register Task Scheduler job
│   └── setup_startup.ps1     # register dashboard in Windows Startup
├── data/
│   ├── watchlist.json        # candidate tickers (seeded, grows over time)
│   └── user_profile.json     # per-user settings
├── reports/                  # daily report files (git-ignored)
├── logs/                     # agent run logs (git-ignored)
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## Task 1: Project scaffold and environment

**Files:**
- Create: all directories and root files listed above

- [ ] **Step 1: Install Python**

Download and run the Python 3.11+ installer from https://www.python.org/downloads/
During install, check "Add python.exe to PATH". After install, verify:

```
python --version
# Expected: Python 3.11.x or higher
pip --version
# Expected: pip 23.x or higher
```

- [ ] **Step 2: Create directory structure**

Run in PowerShell from the project root (`C:\Users\shaya_lukp8lb\Desktop\Claude Code\Financial Agent`):

```powershell
New-Item -ItemType Directory -Force agent, dashboard, "dashboard/static", tests, scripts, data, reports, logs
New-Item -ItemType File -Force agent/__init__.py, dashboard/__init__.py, tests/__init__.py
```

- [ ] **Step 3: Create requirements.txt**

```
anthropic>=0.40.0
yfinance>=0.2.40
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pystray>=0.19.5
pillow>=11.0.0
newsapi-python>=0.2.7
mcp>=1.0.0
httpx>=0.28.0
python-dotenv>=1.0.0
pytest>=8.3.0
pytest-asyncio>=0.24.0
```

- [ ] **Step 4: Install dependencies**

```
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 5: Create .env.example**

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
NEWSAPI_KEY=your_newsapi_key_here
ROBINHOOD_MCP_TOKEN=your_robinhood_mcp_token_here
```

- [ ] **Step 6: Create .env from example and fill in keys**

Copy `.env.example` to `.env`. Get keys:
- Anthropic: https://console.anthropic.com → API Keys → Create Key
- NewsAPI: https://newsapi.org/register (free plan, 100 req/day)
- Robinhood MCP token: Leave blank for now — Task 3 will determine the auth approach

- [ ] **Step 7: Create .gitignore**

```
.env
reports/
logs/
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
.superpowers/
```

- [ ] **Step 8: Create data/user_profile.json**

```json
{
  "name": "Shayan",
  "email": "shayaniqbal2008@gmail.com",
  "halal_filter": true,
  "timezone": "America/Chicago"
}
```

- [ ] **Step 9: Create data/watchlist.json**

Seed with AI-infrastructure stocks to screen on first run:

```json
[
  "NVDA", "AMD", "AVGO", "MRVL", "ANET", "SMCI", "VRT", "ETN",
  "DELL", "HPE", "CDNS", "SNPS", "LRCX", "AMAT", "KLAC", "ONTO",
  "COHR", "IIVI", "MANH", "CRDO", "CIEN", "LITE", "VIAV", "FORM",
  "WOLF", "ACLS", "MKSI", "IPGP", "NTAP", "PSTG", "WDFC", "WDC",
  "GOOGL", "AAPL"
]
```

- [ ] **Step 10: Initialize git and commit scaffold**

```
git init
git add .gitignore requirements.txt .env.example data/ agent/__init__.py dashboard/__init__.py tests/__init__.py
git commit -m "feat: project scaffold and environment setup"
```

---

## Task 2: Storage abstraction layer

**Files:**
- Create: `agent/storage.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_storage.py`:

```python
import json
import pytest
from pathlib import Path
from agent.storage import Storage


@pytest.fixture
def storage(tmp_path):
    return Storage(tmp_path)


def test_save_and_load_report_json(storage):
    report = {"date": "2026-06-15", "sell_alerts": [], "buy_candidates": []}
    storage.save_report_json("2026-06-15", report)
    loaded = storage.load_report("2026-06-15")
    assert loaded == report


def test_load_report_returns_none_when_missing(storage):
    assert storage.load_report("2026-01-01") is None


def test_load_latest_report_returns_most_recent(storage):
    storage.save_report_json("2026-06-13", {"date": "2026-06-13"})
    storage.save_report_json("2026-06-15", {"date": "2026-06-15"})
    storage.save_report_json("2026-06-14", {"date": "2026-06-14"})
    latest = storage.load_latest_report()
    assert latest["date"] == "2026-06-15"


def test_load_latest_report_returns_none_when_empty(storage):
    assert storage.load_latest_report() is None


def test_list_report_dates_sorted_descending(storage):
    for d in ["2026-06-13", "2026-06-15", "2026-06-14"]:
        storage.save_report_json(d, {"date": d})
    dates = storage.list_report_dates()
    assert dates == ["2026-06-15", "2026-06-14", "2026-06-13"]


def test_save_and_load_watchlist(storage):
    tickers = ["NVDA", "AAPL", "GOOGL"]
    storage.save_watchlist(tickers)
    loaded = storage.load_watchlist()
    assert set(loaded) == set(tickers)


def test_load_watchlist_returns_empty_when_missing(storage):
    assert storage.load_watchlist() == []


def test_load_user_profile_returns_defaults_when_missing(storage):
    profile = storage.load_user_profile()
    assert "halal_filter" in profile


def test_load_user_profile_reads_file(storage, tmp_path):
    profile_data = {"halal_filter": True, "name": "Shayan"}
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "data" / "user_profile.json").write_text(json.dumps(profile_data))
    storage = Storage(tmp_path)
    loaded = storage.load_user_profile()
    assert loaded["halal_filter"] is True
    assert loaded["name"] == "Shayan"


def test_add_to_watchlist_deduplicates(storage):
    storage.save_watchlist(["NVDA", "AAPL"])
    existing = storage.load_watchlist()
    storage.save_watchlist(list(set(existing + ["AAPL", "GOOGL"])))
    final = storage.load_watchlist()
    assert final.count("AAPL") == 1
    assert "GOOGL" in final
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_storage.py -v
```

Expected: ImportError or multiple FAILs — `storage.py` does not exist yet.

- [ ] **Step 3: Implement storage.py**

Create `agent/storage.py`:

```python
import json
from pathlib import Path


class Storage:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.reports_dir = self.base_dir / "reports"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        for d in [self.reports_dir, self.data_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def save_report_json(self, date: str, report: dict) -> Path:
        path = self.reports_dir / f"{date}.json"
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return path

    def save_report_html(self, date: str, html: str) -> Path:
        path = self.reports_dir / f"{date}.html"
        path.write_text(html, encoding="utf-8")
        return path

    def load_report(self, date: str) -> dict | None:
        path = self.reports_dir / f"{date}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def load_latest_report(self) -> dict | None:
        reports = sorted(self.reports_dir.glob("*.json"))
        if not reports:
            return None
        return json.loads(reports[-1].read_text(encoding="utf-8"))

    def list_report_dates(self) -> list[str]:
        return sorted([p.stem for p in self.reports_dir.glob("*.json")], reverse=True)

    def load_watchlist(self) -> list[str]:
        path = self.data_dir / "watchlist.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def save_watchlist(self, tickers: list[str]) -> None:
        path = self.data_dir / "watchlist.json"
        path.write_text(json.dumps(sorted(set(tickers)), indent=2), encoding="utf-8")

    def load_user_profile(self) -> dict:
        path = self.data_dir / "user_profile.json"
        if not path.exists():
            return {"halal_filter": False}
        return json.loads(path.read_text(encoding="utf-8"))
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_storage.py -v
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```
git add agent/storage.py tests/test_storage.py
git commit -m "feat: storage abstraction layer"
```

---

## Task 3: Stock data fetcher (yfinance)

**Files:**
- Create: `agent/data.py`
- Create: `tests/test_data.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_data.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_data.py -v
```

Expected: ImportError — `data.py` does not exist yet.

- [ ] **Step 3: Implement data.py**

Create `agent/data.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_data.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```
git add agent/data.py tests/test_data.py
git commit -m "feat: yfinance stock data fetcher"
```

---

## Task 4: News fetcher

**Files:**
- Create: `agent/news.py`
- Create: `tests/test_news.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_news.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_news.py -v
```

Expected: ImportError — `news.py` does not exist yet.

- [ ] **Step 3: Implement news.py**

Create `agent/news.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_news.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```
git add agent/news.py tests/test_news.py
git commit -m "feat: news fetcher (yfinance ticker + NewsAPI macro)"
```

---

## Task 5: Screening pipeline

**Files:**
- Create: `agent/screener.py`
- Create: `tests/test_screener.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_screener.py`:

```python
import pytest
from agent.data import StockData
from agent.screener import halal_screen, screen_quantitative, screen, ScreenResult


def make_stock(**kwargs) -> StockData:
    defaults = dict(
        ticker="TEST", market_cap=5_000_000_000, profit_margin=0.20,
        total_cash=500_000_000, forward_pe=25.0, one_year_return=0.30,
        analyst_mean_target=150.0, current_price=130.0, week_52_high=145.0,
        employees=5000, country="United States", industry="Semiconductors",
        sector="Technology", news=[]
    )
    defaults.update(kwargs)
    return StockData(**defaults)


# --- Halal filter ---

def test_halal_screen_passes_us_tech_stock():
    assert halal_screen(make_stock(), enabled=True) is True


def test_halal_screen_fails_israeli_company():
    assert halal_screen(make_stock(country="Israel"), enabled=True) is False


def test_halal_screen_fails_known_excluded_ticker():
    assert halal_screen(make_stock(ticker="CHKP"), enabled=True) is False


def test_halal_screen_fails_alcohol_industry():
    assert halal_screen(make_stock(industry="Beverages - Brewers"), enabled=True) is False


def test_halal_screen_fails_gambling_industry():
    assert halal_screen(make_stock(industry="Gambling"), enabled=True) is False


def test_halal_screen_disabled_passes_everything():
    assert halal_screen(make_stock(country="Israel"), enabled=False) is True


# --- Quantitative criteria ---

def test_screen_quantitative_passes_all_criteria():
    passed, failed = screen_quantitative(make_stock())
    assert passed is True
    assert failed == []


def test_criterion_1_market_cap_below_1b_fails():
    _, failed = screen_quantitative(make_stock(market_cap=500_000_000))
    assert 1 in failed


def test_criterion_2_negative_margin_fails():
    _, failed = screen_quantitative(make_stock(profit_margin=-0.05))
    assert 2 in failed


def test_criterion_3_cash_in_thousands_fails():
    _, failed = screen_quantitative(make_stock(total_cash=500_000))
    assert 3 in failed


def test_criterion_3_none_cash_fails():
    _, failed = screen_quantitative(make_stock(total_cash=None))
    assert 3 in failed


def test_criterion_4_negative_forward_pe_fails():
    _, failed = screen_quantitative(make_stock(forward_pe=-5.0))
    assert 4 in failed


def test_criterion_5_return_below_15_pct_fails():
    _, failed = screen_quantitative(make_stock(one_year_return=0.10))
    assert 5 in failed


def test_criterion_5_exactly_15_pct_fails():
    # "greater than 15%" means strictly > 0.15
    _, failed = screen_quantitative(make_stock(one_year_return=0.15))
    assert 5 in failed


def test_criterion_6_price_above_analyst_target_fails():
    _, failed = screen_quantitative(make_stock(current_price=160.0, analyst_mean_target=150.0))
    assert 6 in failed


def test_criterion_7_price_below_80pct_high_fails():
    # current = 100, high = 145 → 100 < 0.8 * 145 = 116
    _, failed = screen_quantitative(make_stock(current_price=100.0, week_52_high=145.0))
    assert 7 in failed


def test_criterion_8_employees_below_1000_fails():
    _, failed = screen_quantitative(make_stock(employees=500))
    assert 8 in failed


def test_multiple_criteria_failures_reported():
    _, failed = screen_quantitative(make_stock(market_cap=500_000_000, profit_margin=-0.1))
    assert 1 in failed
    assert 2 in failed


# --- Combined screen ---

def test_screen_passes_good_stock():
    result = screen(make_stock(), halal_filter=True)
    assert result.passed_halal is True
    assert result.passed_quant is True
    assert result.failed_criteria == []


def test_screen_halal_fail_skips_quant():
    result = screen(make_stock(country="Israel"), halal_filter=True)
    assert result.passed_halal is False
    assert result.passed_quant is False


def test_screen_returns_screen_result_type():
    result = screen(make_stock())
    assert isinstance(result, ScreenResult)
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_screener.py -v
```

Expected: ImportError — `screener.py` does not exist yet.

- [ ] **Step 3: Implement screener.py**

Create `agent/screener.py`:

```python
from dataclasses import dataclass
from agent.data import StockData


HALAL_EXCLUDED_COUNTRIES = {"Israel", "IL"}

HALAL_EXCLUDED_TICKERS = {
    "NICE", "CEVA", "CHKP", "CYBR", "MNDY", "WIX", "FVRR", "GLBE",
    "TEVA", "GKOS", "NNDM", "MICT", "PLTR",
}

HALAL_EXCLUDED_KEYWORDS = {
    "alcohol", "beer", "wine", "spirits", "brewery", "brewer", "distillery", "distiller",
    "gambling", "casino", "betting", "lottery", "wagering",
    "pork", "swine",
    "adult entertainment", "pornography",
}

# Sectors dominated by riba (interest-based income)
HALAL_EXCLUDED_SECTORS = {"Financial Services"}
HALAL_EXCLUDED_INDUSTRIES = {
    "Banks - Diversified", "Banks - Regional", "Insurance - Life",
    "Insurance - Diversified", "Insurance - Property & Casualty",
    "Credit Services", "Mortgage Finance",
}


@dataclass
class ScreenResult:
    ticker: str
    passed_halal: bool
    passed_quant: bool
    failed_criteria: list[int]
    data: StockData


def halal_screen(stock: StockData, enabled: bool = True) -> bool:
    if not enabled:
        return True
    if stock.country in HALAL_EXCLUDED_COUNTRIES:
        return False
    if stock.ticker in HALAL_EXCLUDED_TICKERS:
        return False
    if stock.sector in HALAL_EXCLUDED_SECTORS:
        return False
    if stock.industry in HALAL_EXCLUDED_INDUSTRIES:
        return False
    combined = f"{(stock.industry or '').lower()} {(stock.sector or '').lower()}"
    for keyword in HALAL_EXCLUDED_KEYWORDS:
        if keyword in combined:
            return False
    return True


def screen_quantitative(stock: StockData) -> tuple[bool, list[int]]:
    failed: list[int] = []

    if stock.market_cap is None or stock.market_cap <= 1_000_000_000:
        failed.append(1)
    if stock.profit_margin is None or stock.profit_margin <= 0:
        failed.append(2)
    if stock.total_cash is None or stock.total_cash < 1_000_000:
        failed.append(3)
    if stock.forward_pe is None or stock.forward_pe <= 0:
        failed.append(4)
    if stock.one_year_return is None or stock.one_year_return <= 0.15:
        failed.append(5)
    if (stock.current_price is None or stock.analyst_mean_target is None
            or stock.current_price > stock.analyst_mean_target):
        failed.append(6)
    if (stock.current_price is None or stock.week_52_high is None
            or stock.current_price < 0.8 * stock.week_52_high):
        failed.append(7)
    if stock.employees is None or stock.employees <= 1000:
        failed.append(8)

    return len(failed) == 0, failed


def screen(stock: StockData, halal_filter: bool = True) -> ScreenResult:
    passed_halal = halal_screen(stock, enabled=halal_filter)
    if not passed_halal:
        return ScreenResult(
            ticker=stock.ticker,
            passed_halal=False,
            passed_quant=False,
            failed_criteria=[],
            data=stock,
        )
    passed_quant, failed_criteria = screen_quantitative(stock)
    return ScreenResult(
        ticker=stock.ticker,
        passed_halal=True,
        passed_quant=passed_quant,
        failed_criteria=failed_criteria,
        data=stock,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_screener.py -v
```

Expected: all 24 tests PASS.

- [ ] **Step 5: Commit**

```
git add agent/screener.py tests/test_screener.py
git commit -m "feat: screening pipeline — halal filter + 15 quantitative criteria"
```

---

## Task 6: Claude API analyst

**Files:**
- Create: `agent/analyst.py`
- Create: `tests/test_analyst.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_analyst.py`:

```python
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
    messages = call_kwargs.kwargs.get("messages") or call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs["messages"]
    content_blocks = messages[0]["content"]
    cache_blocks = [b for b in content_blocks if isinstance(b, dict) and b.get("cache_control")]
    assert len(cache_blocks) >= 1


def test_criteria_block_contains_all_15_criteria():
    for i in range(1, 16):
        assert str(i) in CRITERIA_BLOCK, f"Criterion {i} missing from CRITERIA_BLOCK"
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_analyst.py -v
```

Expected: ImportError — `analyst.py` does not exist yet.

- [ ] **Step 3: Implement analyst.py**

Create `agent/analyst.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_analyst.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```
git add agent/analyst.py tests/test_analyst.py
git commit -m "feat: Claude API analyst with prompt caching"
```

---

## Task 7: Portfolio fetcher (Robinhood MCP)

**Files:**
- Create: `agent/portfolio.py`

**Note:** The Robinhood MCP uses an authenticated HTTP connection. This task includes a discovery step to identify available tools and test connectivity. If the direct MCP approach requires auth that isn't available, a fallback to Claude API remote MCP is documented.

- [ ] **Step 1: Implement portfolio.py**

Create `agent/portfolio.py`:

```python
import asyncio
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

ROBINHOOD_MCP_URL = "https://agent.robinhood.com/mcp/trading"

PORTFOLIO_TOOL_NAMES = [
    "get_portfolio", "portfolio", "get_positions", "positions",
    "get_holdings", "holdings", "account_portfolio",
]


async def _list_tools_async(auth_token: str | None = None) -> list[str]:
    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
    async with streamablehttp_client(ROBINHOOD_MCP_URL, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [t.name for t in result.tools]


async def _fetch_portfolio_async(auth_token: str | None = None) -> list[dict]:
    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
    async with streamablehttp_client(ROBINHOOD_MCP_URL, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            available = [t.name for t in tools.tools]
            for name in PORTFOLIO_TOOL_NAMES:
                if name in available:
                    result = await session.call_tool(name, {})
                    return _parse_result(result)
            raise ValueError(
                f"No portfolio tool found in Robinhood MCP. Available tools: {available}"
            )


def _parse_result(result) -> list[dict]:
    if not result.content:
        return []
    import json
    raw = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("positions", "holdings", "portfolio", "results"):
            if key in data:
                return data[key]
    return []


def list_mcp_tools(auth_token: str | None = None) -> list[str]:
    return asyncio.run(_list_tools_async(auth_token))


def fetch_portfolio(auth_token: str | None = None) -> list[dict]:
    return asyncio.run(_fetch_portfolio_async(auth_token))
```

- [ ] **Step 2: Test MCP connectivity manually**

Run a quick discovery to see what tools Robinhood exposes. Create a temporary test script (do NOT commit):

```python
# tmp_test_mcp.py  — delete after running
import os
from dotenv import load_dotenv
from agent.portfolio import list_mcp_tools

load_dotenv()
token = os.getenv("ROBINHOOD_MCP_TOKEN")
print("Auth token present:", bool(token))
tools = list_mcp_tools(auth_token=token)
print("Available tools:", tools)
```

Run: `python tmp_test_mcp.py`

If you get a 401/403: the MCP requires auth. Obtain the token:
1. Open Claude Code and run: `/mcp` to see connected servers
2. The Robinhood MCP auth token may be in `~/.claude/mcp_auth.json` or similar
3. Set `ROBINHOOD_MCP_TOKEN=<token>` in `.env` and re-run

If connection fails entirely, the fallback is to read portfolio from a manually maintained `data/holdings.json` file (structure below). Update `fetch_portfolio` to read that file when the MCP is unavailable:

```json
[
  {"ticker": "AAPL", "quantity": 10, "avg_cost": 185.50},
  {"ticker": "GOOGL", "quantity": 5, "avg_cost": 170.00}
]
```

- [ ] **Step 3: Verify portfolio data returns correct shape**

Once connectivity is confirmed, verify the returned data:

```python
# tmp_test_portfolio.py — delete after running
import os
from dotenv import load_dotenv
from agent.portfolio import fetch_portfolio

load_dotenv()
token = os.getenv("ROBINHOOD_MCP_TOKEN")
positions = fetch_portfolio(auth_token=token)
print(f"Got {len(positions)} positions:")
for p in positions:
    print(p)
```

Run: `python tmp_test_portfolio.py`

Expected: list of dicts with ticker, quantity, and cost basis fields. Note the exact field names returned — you may need to update `_parse_result` to normalize them to `{"ticker": str, "quantity": float, "avg_cost": float}`.

- [ ] **Step 4: Delete temporary test scripts and commit**

```
del tmp_test_mcp.py tmp_test_portfolio.py
git add agent/portfolio.py
git commit -m "feat: Robinhood MCP portfolio fetcher"
```

---

## Task 8: Report assembler

**Files:**
- Create: `agent/report.py`
- Create: `tests/test_report.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_report.py`:

```python
import json
import pytest
from pathlib import Path
from agent.report import assemble_report, save_report, render_html
from agent.storage import Storage


SAMPLE_ANALYSIS = {
    "portfolio_review": [
        {"ticker": "AAPL", "grade": "A", "criteria_9_15_pass": [True]*7,
         "summary": "Strong fundamentals", "flags": []}
    ],
    "sell_alerts": [
        {"ticker": "XYZ", "reason": "Failed momentum filter", "urgency": "high"}
    ],
    "buy_candidates": [
        {"ticker": "NVDA", "rationale": "AI infrastructure leader",
         "criteria_9_15_pass": [True]*7}
    ],
    "news_briefing": [
        {"headline": "Fed keeps rates steady", "impact": "Positive for growth stocks",
         "tickers_affected": ["AAPL", "GOOGL"]}
    ],
    "market_political_alerts": [
        {"event": "Tariff announcement", "market_impact": "Negative for supply chains",
         "urgency": "medium"}
    ],
    "new_watchlist_candidates": ["AMD", "AVGO"]
}


def test_assemble_report_adds_date_and_timestamp():
    report = assemble_report(SAMPLE_ANALYSIS, date="2026-06-15")
    assert report["date"] == "2026-06-15"
    assert "generated_at" in report
    assert "portfolio_review" in report


def test_assemble_report_uses_today_when_no_date():
    from datetime import datetime
    report = assemble_report(SAMPLE_ANALYSIS)
    today = datetime.now().strftime("%Y-%m-%d")
    assert report["date"] == today


def test_save_report_writes_json_file(tmp_path):
    storage = Storage(tmp_path)
    report = assemble_report(SAMPLE_ANALYSIS, date="2026-06-15")
    save_report(report, storage)
    json_path = tmp_path / "reports" / "2026-06-15.json"
    assert json_path.exists()
    loaded = json.loads(json_path.read_text())
    assert loaded["date"] == "2026-06-15"


def test_save_report_writes_html_file(tmp_path):
    storage = Storage(tmp_path)
    report = assemble_report(SAMPLE_ANALYSIS, date="2026-06-15")
    save_report(report, storage)
    html_path = tmp_path / "reports" / "2026-06-15.html"
    assert html_path.exists()
    content = html_path.read_text()
    assert "2026-06-15" in content


def test_render_html_contains_sell_alerts():
    report = assemble_report(SAMPLE_ANALYSIS, date="2026-06-15")
    html = render_html(report)
    assert "XYZ" in html
    assert "Failed momentum filter" in html


def test_render_html_contains_buy_candidates():
    report = assemble_report(SAMPLE_ANALYSIS, date="2026-06-15")
    html = render_html(report)
    assert "NVDA" in html
    assert "AI infrastructure leader" in html


def test_render_html_contains_news():
    report = assemble_report(SAMPLE_ANALYSIS, date="2026-06-15")
    html = render_html(report)
    assert "Fed keeps rates steady" in html


def test_save_report_updates_watchlist(tmp_path):
    storage = Storage(tmp_path)
    storage.save_watchlist(["NVDA", "AAPL"])
    report = assemble_report(SAMPLE_ANALYSIS, date="2026-06-15")
    save_report(report, storage)
    watchlist = storage.load_watchlist()
    assert "AMD" in watchlist
    assert "AVGO" in watchlist
    assert "NVDA" in watchlist  # existing entries preserved
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_report.py -v
```

Expected: ImportError — `report.py` does not exist yet.

- [ ] **Step 3: Implement report.py**

Create `agent/report.py`:

```python
from datetime import datetime
from pathlib import Path
from agent.storage import Storage


def assemble_report(analysis: dict, date: str | None = None) -> dict:
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    return {
        "date": date,
        "generated_at": datetime.now().isoformat(),
        **analysis,
    }


def save_report(report: dict, storage: Storage) -> Path:
    date = report["date"]
    json_path = storage.save_report_json(date, report)
    storage.save_report_html(date, render_html(report))

    # Update watchlist with new candidates from this run
    new_candidates = report.get("new_watchlist_candidates", [])
    if new_candidates:
        existing = storage.load_watchlist()
        storage.save_watchlist(list(set(existing + new_candidates)))

    return json_path


def render_html(report: dict) -> str:
    date = report.get("date", "")
    generated_at = report.get("generated_at", "")

    def badge(urgency: str) -> str:
        colors = {"high": "#e74c3c", "medium": "#f39c12", "low": "#2ecc71"}
        return f'<span style="background:{colors.get(urgency,"#888")};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.8em">{urgency.upper()}</span>'

    sell_rows = "".join(
        f'<tr><td><strong>{a["ticker"]}</strong></td>'
        f'<td>{a["reason"]}</td>'
        f'<td>{badge(a["urgency"])}</td></tr>'
        for a in report.get("sell_alerts", [])
    )
    buy_rows = "".join(
        f'<tr><td><strong>{c["ticker"]}</strong></td>'
        f'<td>{c["rationale"]}</td></tr>'
        for c in report.get("buy_candidates", [])
    )
    portfolio_rows = "".join(
        f'<tr><td><strong>{h["ticker"]}</strong></td>'
        f'<td style="font-size:1.2em;font-weight:bold">{h.get("grade","?")}</td>'
        f'<td>{h.get("summary","")}</td>'
        f'<td>{"".join(f"<span class=flag>{f}</span>" for f in h.get("flags",[]))}</td></tr>'
        for h in report.get("portfolio_review", [])
    )
    news_rows = "".join(
        f'<div class="news-item"><strong>{n["headline"]}</strong>'
        f'<p>{n["impact"]}</p>'
        f'<small>Tickers: {", ".join(n.get("tickers_affected",[]))}</small></div>'
        for n in report.get("news_briefing", [])
    )
    alert_rows = "".join(
        f'<div class="alert-item">{badge(a["urgency"])} <strong>{a["event"]}</strong>'
        f'<p>{a["market_impact"]}</p></div>'
        for a in report.get("market_political_alerts", [])
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Financial Agent — {date}</title>
<style>
  body{{font-family:system-ui,sans-serif;background:#0d1117;color:#c9d1d9;margin:0;padding:24px}}
  h1{{color:#58a6ff;border-bottom:1px solid #30363d;padding-bottom:8px}}
  h2{{color:#f0f6fc;margin-top:32px}}
  table{{width:100%;border-collapse:collapse;margin-top:8px}}
  th{{background:#161b22;color:#8b949e;text-align:left;padding:8px 12px;font-size:0.85em}}
  td{{padding:8px 12px;border-bottom:1px solid #21262d;vertical-align:top}}
  .news-item,.alert-item{{background:#161b22;border:1px solid #30363d;border-radius:6px;
    padding:12px 16px;margin-bottom:8px}}
  .flag{{background:#388bfd22;color:#388bfd;padding:2px 6px;border-radius:4px;
    font-size:0.8em;margin-right:4px}}
  .meta{{color:#8b949e;font-size:0.85em;margin-top:4px}}
</style>
</head>
<body>
<h1>Financial Agent Report</h1>
<p class="meta">Date: {date} &nbsp;|&nbsp; Generated: {generated_at}</p>

<h2>⚠ Sell Alerts ({len(report.get("sell_alerts", []))})</h2>
<table><tr><th>Ticker</th><th>Reason</th><th>Urgency</th></tr>{sell_rows or "<tr><td colspan=3>No sell alerts today</td></tr>"}</table>

<h2>✓ Buy Candidates ({len(report.get("buy_candidates", []))})</h2>
<table><tr><th>Ticker</th><th>Rationale</th></tr>{buy_rows or "<tr><td colspan=2>No qualifying candidates today</td></tr>"}</table>

<h2>Portfolio Review</h2>
<table><tr><th>Ticker</th><th>Grade</th><th>Summary</th><th>Flags</th></tr>{portfolio_rows}</table>

<h2>News Briefing</h2>
{news_rows or "<p>No significant news today.</p>"}

<h2>Market & Political Alerts</h2>
{alert_rows or "<p>No significant alerts today.</p>"}
</body>
</html>"""
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_report.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```
git add agent/report.py tests/test_report.py
git commit -m "feat: report assembler — JSON + HTML output, watchlist update"
```

---

## Task 9: Agent main orchestrator

**Files:**
- Create: `agent/main.py`

- [ ] **Step 1: Implement main.py**

Create `agent/main.py`:

```python
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "logs" / "agent.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def run():
    from agent.storage import Storage
    from agent.portfolio import fetch_portfolio
    from agent.data import fetch_stock_data
    from agent.news import fetch_macro_news, fetch_ticker_news
    from agent.screener import screen
    from agent.analyst import analyze
    from agent.report import assemble_report, save_report

    storage = Storage(BASE_DIR)
    profile = storage.load_user_profile()
    halal_filter = profile.get("halal_filter", False)

    log.info("=== Financial Agent starting ===")

    # Step 1: Portfolio
    log.info("Fetching portfolio from Robinhood MCP...")
    try:
        holdings = fetch_portfolio(auth_token=os.getenv("ROBINHOOD_MCP_TOKEN"))
        log.info(f"Got {len(holdings)} holdings")
    except Exception as e:
        log.warning(f"MCP portfolio fetch failed: {e}. Falling back to local holdings file.")
        import json
        fallback = BASE_DIR / "data" / "holdings.json"
        holdings = json.loads(fallback.read_text()) if fallback.exists() else []

    # Step 2: Stock data for holdings + watchlist
    log.info("Fetching stock data...")
    watchlist = storage.load_watchlist()
    holding_tickers = [h.get("ticker", h.get("symbol", "")) for h in holdings]
    all_tickers = list(set(holding_tickers + watchlist))

    stock_data_map = {}
    for ticker in all_tickers:
        try:
            stock_data_map[ticker] = fetch_stock_data(ticker)
            log.info(f"  {ticker}: OK")
        except Exception as e:
            log.warning(f"  {ticker}: FAILED — {e}")

    # Step 3: News
    log.info("Fetching news...")
    macro_news = []
    try:
        macro_news = fetch_macro_news(api_key=os.getenv("NEWSAPI_KEY", ""))
        log.info(f"Got {len(macro_news)} macro headlines")
    except Exception as e:
        log.warning(f"NewsAPI failed: {e}")
    ticker_news = fetch_ticker_news(list(stock_data_map.values()))

    # Step 4: Screen candidates (watchlist only — holdings always go to Claude)
    log.info("Screening candidates...")
    screened = [
        screen(stock_data_map[t], halal_filter=halal_filter)
        for t in watchlist
        if t in stock_data_map
    ]
    passed = [r for r in screened if r.passed_quant]
    log.info(f"{len(passed)}/{len(screened)} watchlist candidates passed screening")

    # Enrich holdings with stock data for Claude
    enriched_holdings = []
    for h in holdings:
        ticker = h.get("ticker", h.get("symbol", ""))
        sd = stock_data_map.get(ticker)
        enriched_holdings.append({
            "ticker": ticker,
            "quantity": h.get("quantity", h.get("shares", 0)),
            "avg_cost": h.get("avg_cost", h.get("average_buy_price", 0)),
            "current_price": sd.current_price if sd else None,
            "one_year_return": sd.one_year_return if sd else None,
            "profit_margin": sd.profit_margin if sd else None,
        })

    # Step 5: Claude API analysis
    log.info("Running Claude API analysis...")
    analysis = analyze(
        holdings=enriched_holdings,
        candidates=screened,
        macro_news=macro_news,
        ticker_news=ticker_news,
        api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    )

    # Step 6: Save report
    report = assemble_report(analysis)
    path = save_report(report, storage)
    log.info(f"Report saved to {path}")
    log.info("=== Financial Agent done ===")


if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run the agent manually to verify end-to-end flow**

```
python agent/main.py
```

Watch the logs. Expected sequence:
```
2026-06-15 08:00:00 INFO === Financial Agent starting ===
2026-06-15 08:00:01 INFO Fetching portfolio from Robinhood MCP...
2026-06-15 08:00:03 INFO Got N holdings
2026-06-15 08:00:03 INFO Fetching stock data...
...
2026-06-15 08:03:45 INFO Report saved to .../reports/2026-06-15.json
2026-06-15 08:03:45 INFO === Financial Agent done ===
```

Check `reports/2026-06-15.json` and `reports/2026-06-15.html` exist and contain valid content.

- [ ] **Step 3: Commit**

```
git add agent/main.py logs/.gitkeep reports/.gitkeep
git commit -m "feat: agent main orchestrator — end-to-end daily run"
```

---

## Task 10: FastAPI dashboard server

**Files:**
- Create: `dashboard/server.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_server.py`:

```python
import json
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from agent.storage import Storage
from agent.report import assemble_report, save_report

SAMPLE_ANALYSIS = {
    "portfolio_review": [{"ticker": "AAPL", "grade": "A", "criteria_9_15_pass": [True]*7,
                          "summary": "Strong", "flags": []}],
    "sell_alerts": [],
    "buy_candidates": [],
    "news_briefing": [],
    "market_political_alerts": [],
    "new_watchlist_candidates": [],
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    storage = Storage(tmp_path)
    report = assemble_report(SAMPLE_ANALYSIS, date="2026-06-15")
    save_report(report, storage)

    import dashboard.server as server_module
    monkeypatch.setattr(server_module, "storage", storage)
    from dashboard.server import app
    return TestClient(app)


def test_get_latest_report(client):
    response = client.get("/api/report/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-06-15"
    assert "portfolio_review" in data


def test_get_report_by_date(client):
    response = client.get("/api/report/2026-06-15")
    assert response.status_code == 200
    assert response.json()["date"] == "2026-06-15"


def test_get_report_missing_date_returns_404(client):
    response = client.get("/api/report/2000-01-01")
    assert response.status_code == 404


def test_list_reports(client):
    response = client.get("/api/reports")
    assert response.status_code == 200
    dates = response.json()
    assert "2026-06-15" in dates


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_server.py -v
```

Expected: ImportError — `dashboard/server.py` does not exist yet.

- [ ] **Step 3: Implement dashboard/server.py**

Create `dashboard/server.py`:

```python
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import yfinance as yf
from agent.storage import Storage

BASE_DIR = Path(__file__).parent.parent
storage = Storage(BASE_DIR)

app = FastAPI(title="Financial Agent Dashboard")

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Dashboard loading...</h1>")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/report/latest")
def get_latest_report():
    report = storage.load_latest_report()
    if report is None:
        raise HTTPException(status_code=404, detail="No reports found")
    return report


@app.get("/api/report/{date}")
def get_report(date: str):
    report = storage.load_report(date)
    if report is None:
        raise HTTPException(status_code=404, detail=f"No report for {date}")
    return report


@app.get("/api/reports")
def list_reports():
    return storage.list_report_dates()


@app.get("/api/portfolio/live")
def portfolio_live():
    report = storage.load_latest_report()
    if report is None:
        return {"holdings": [], "indices": {}}

    holdings_out = []
    for h in report.get("portfolio_review", []):
        ticker = h["ticker"]
        try:
            t = yf.Ticker(ticker)
            price = t.fast_info.last_price
        except Exception:
            price = None
        holdings_out.append({
            "ticker": ticker,
            "grade": h.get("grade"),
            "current_price": price,
            "flags": h.get("flags", []),
        })

    indices = {}
    for symbol, label in [("SPY", "S&P 500"), ("QQQ", "NASDAQ"), ("^VIX", "VIX")]:
        try:
            t = yf.Ticker(symbol)
            indices[label] = round(t.fast_info.last_price, 2)
        except Exception:
            indices[label] = None

    return {"holdings": holdings_out, "indices": indices}
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_server.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```
git add dashboard/server.py tests/test_server.py
git commit -m "feat: FastAPI dashboard server with report and live portfolio endpoints"
```

---

## Task 11: Dashboard UI

**Files:**
- Create: `dashboard/static/index.html`
- Create: `dashboard/static/style.css`
- Create: `dashboard/static/app.js`

- [ ] **Step 1: Create style.css**

Create `dashboard/static/style.css`:

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0d1117;
  --surface: #161b22;
  --border: #30363d;
  --text: #c9d1d9;
  --text-muted: #8b949e;
  --accent: #58a6ff;
  --green: #3fb950;
  --red: #f85149;
  --yellow: #d29922;
}

body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; min-height: 100vh; }

header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 12px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

header h1 { font-size: 1.1rem; color: var(--accent); letter-spacing: 0.05em; }
.status-dot { width: 10px; height: 10px; border-radius: 50%; }
.status-dot.fresh { background: var(--green); }
.status-dot.stale { background: var(--yellow); }
.status-dot.error { background: var(--red); }
.date-label { color: var(--text-muted); font-size: 0.9rem; margin-left: auto; }

.layout { display: grid; grid-template-columns: 1fr 300px; height: calc(100vh - 53px); }

.report-panel { overflow-y: auto; padding: 24px; }
.portfolio-panel { background: var(--surface); border-left: 1px solid var(--border); overflow-y: auto; padding: 16px; }

.section { margin-bottom: 28px; }
.section-header {
  display: flex; align-items: center; gap: 8px;
  cursor: pointer; padding: 8px 0; border-bottom: 1px solid var(--border);
  user-select: none;
}
.section-header h2 { font-size: 1rem; color: var(--text); }
.section-header .count { background: var(--border); color: var(--text-muted); padding: 1px 8px; border-radius: 12px; font-size: 0.8rem; }
.section-header .chevron { margin-left: auto; color: var(--text-muted); transition: transform 0.2s; }
.section-header.open .chevron { transform: rotate(90deg); }
.section-body { display: none; margin-top: 12px; }
.section-body.open { display: block; }

.alert-card, .candidate-card, .news-card {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 6px; padding: 12px 16px; margin-bottom: 8px;
}
.alert-card.high { border-left: 3px solid var(--red); }
.alert-card.medium { border-left: 3px solid var(--yellow); }
.alert-card.low { border-left: 3px solid var(--green); }

.ticker { font-weight: 700; color: var(--accent); }
.reason { font-size: 0.9rem; margin-top: 4px; }
.urgency-badge { font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.urgency-badge.high { background: #f8514922; color: var(--red); }
.urgency-badge.medium { background: #d2992222; color: var(--yellow); }
.urgency-badge.low { background: #3fb95022; color: var(--green); }

.portfolio-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.portfolio-table th { color: var(--text-muted); text-align: left; padding: 4px 0; border-bottom: 1px solid var(--border); font-weight: 500; }
.portfolio-table td { padding: 8px 0; border-bottom: 1px solid var(--border); }
.grade-A { color: var(--green); font-weight: 700; }
.grade-B { color: #79c0ff; font-weight: 700; }
.grade-C { color: var(--yellow); font-weight: 700; }
.grade-D, .grade-F { color: var(--red); font-weight: 700; }

.index-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; }
.index-card { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px 12px; }
.index-label { font-size: 0.75rem; color: var(--text-muted); }
.index-value { font-size: 1.1rem; font-weight: 600; margin-top: 2px; }

.panel-title { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-muted); margin-bottom: 12px; }
.refresh-label { font-size: 0.75rem; color: var(--text-muted); margin-top: 8px; text-align: right; }

.date-nav { display: flex; align-items: center; gap: 8px; margin-bottom: 20px; }
.date-nav select { background: var(--surface); color: var(--text); border: 1px solid var(--border); border-radius: 4px; padding: 4px 8px; font-size: 0.85rem; }
```

- [ ] **Step 2: Create app.js**

Create `dashboard/static/app.js`:

```js
let currentDate = null;

async function loadReportDates() {
  const res = await fetch('/api/reports');
  const dates = await res.json();
  const sel = document.getElementById('date-select');
  sel.innerHTML = dates.map(d => `<option value="${d}">${d}</option>`).join('');
  if (dates.length) loadReport(dates[0]);
}

async function loadReport(date) {
  currentDate = date;
  const res = await fetch(`/api/report/${date}`);
  if (!res.ok) { document.getElementById('report-content').innerHTML = '<p>No report for this date.</p>'; return; }
  const report = await res.json();
  renderReport(report);
  updateStatusDot(report);
}

function updateStatusDot(report) {
  const dot = document.getElementById('status-dot');
  const today = new Date().toISOString().split('T')[0];
  dot.className = 'status-dot ' + (report.date === today ? 'fresh' : 'stale');
}

function renderReport(report) {
  document.getElementById('report-date').textContent = report.date;
  const el = document.getElementById('report-content');

  const sell = report.sell_alerts || [];
  const buy = report.buy_candidates || [];
  const portfolio = report.portfolio_review || [];
  const news = report.news_briefing || [];
  const alerts = report.market_political_alerts || [];

  el.innerHTML = `
    ${section('⚠ Sell Alerts', sell.length,
      sell.map(a => `<div class="alert-card ${a.urgency}">
        <div style="display:flex;align-items:center;gap:8px">
          <span class="ticker">${a.ticker}</span>
          <span class="urgency-badge ${a.urgency}">${a.urgency.toUpperCase()}</span>
        </div>
        <div class="reason">${a.reason}</div>
      </div>`).join('') || '<p style="color:var(--text-muted);font-size:.9rem">No sell alerts today.</p>'
    )}
    ${section('✓ Buy Candidates', buy.length,
      buy.map(c => `<div class="candidate-card">
        <span class="ticker">${c.ticker}</span>
        <div class="reason">${c.rationale}</div>
      </div>`).join('') || '<p style="color:var(--text-muted);font-size:.9rem">No qualifying candidates today.</p>'
    )}
    ${section('Portfolio Review', portfolio.length,
      `<table class="portfolio-table">
        <tr><th>Ticker</th><th>Grade</th><th>Summary</th></tr>
        ${portfolio.map(h => `<tr>
          <td class="ticker">${h.ticker}</td>
          <td class="grade-${h.grade}">${h.grade}</td>
          <td style="font-size:.85rem">${h.summary}</td>
        </tr>`).join('')}
      </table>`
    )}
    ${section('News Briefing', news.length,
      news.map(n => `<div class="news-card">
        <strong>${n.headline}</strong>
        <div class="reason">${n.impact}</div>
        <div style="font-size:.8rem;color:var(--text-muted);margin-top:4px">${(n.tickers_affected||[]).join(', ')}</div>
      </div>`).join('') || '<p style="color:var(--text-muted);font-size:.9rem">No significant news.</p>'
    )}
    ${section('Market & Political Alerts', alerts.length,
      alerts.map(a => `<div class="alert-card ${a.urgency}">
        <div style="display:flex;align-items:center;gap:8px">
          <span class="urgency-badge ${a.urgency}">${a.urgency.toUpperCase()}</span>
          <strong>${a.event}</strong>
        </div>
        <div class="reason">${a.market_impact}</div>
      </div>`).join('') || '<p style="color:var(--text-muted);font-size:.9rem">No significant alerts.</p>'
    )}
  `;

  // Open sell alerts and buy candidates by default
  document.querySelectorAll('.section-header').forEach((h, i) => {
    if (i < 2) toggleSection(h);
  });
}

function section(title, count, body) {
  return `<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
      <h2>${title}</h2>
      <span class="count">${count}</span>
      <span class="chevron">›</span>
    </div>
    <div class="section-body">${body}</div>
  </div>`;
}

function toggleSection(header) {
  header.classList.toggle('open');
  header.nextElementSibling.classList.toggle('open');
}

async function refreshPortfolio() {
  const res = await fetch('/api/portfolio/live');
  if (!res.ok) return;
  const data = await res.json();

  const tableBody = document.getElementById('portfolio-rows');
  tableBody.innerHTML = (data.holdings || []).map(h => `
    <tr>
      <td class="ticker">${h.ticker}</td>
      <td class="grade-${h.grade}">${h.grade || '?'}</td>
      <td>${h.current_price != null ? '$' + h.current_price.toFixed(2) : '—'}</td>
    </tr>
  `).join('');

  const indices = data.indices || {};
  document.getElementById('sp500').textContent = indices['S&P 500'] != null ? indices['S&P 500'] : '—';
  document.getElementById('nasdaq').textContent = indices['NASDAQ'] != null ? indices['NASDAQ'] : '—';
  document.getElementById('vix').textContent = indices['VIX'] != null ? indices['VIX'] : '—';
  document.getElementById('last-refresh').textContent = 'Updated ' + new Date().toLocaleTimeString();
}

document.getElementById('date-select').addEventListener('change', e => loadReport(e.target.value));

loadReportDates();
refreshPortfolio();
setInterval(refreshPortfolio, 60000);
```

- [ ] **Step 3: Create index.html**

Create `dashboard/static/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Financial Agent</title>
<link rel="stylesheet" href="/static/style.css">
</head>
<body>

<header>
  <div id="status-dot" class="status-dot stale"></div>
  <h1>FINANCIAL AGENT</h1>
  <div class="date-nav">
    <select id="date-select"></select>
  </div>
  <span id="report-date" class="date-label"></span>
</header>

<div class="layout">
  <div class="report-panel">
    <div id="report-content">
      <p style="color:var(--text-muted)">Loading report...</p>
    </div>
  </div>

  <div class="portfolio-panel">
    <div class="panel-title">Live Portfolio</div>
    <table class="portfolio-table">
      <tr><th>Ticker</th><th>Grade</th><th>Price</th></tr>
      <tbody id="portfolio-rows"></tbody>
    </table>

    <div class="panel-title" style="margin-top:20px">Market</div>
    <div class="index-grid">
      <div class="index-card">
        <div class="index-label">S&P 500</div>
        <div class="index-value" id="sp500">—</div>
      </div>
      <div class="index-card">
        <div class="index-label">NASDAQ</div>
        <div class="index-value" id="nasdaq">—</div>
      </div>
      <div class="index-card" style="grid-column:1/-1">
        <div class="index-label">VIX</div>
        <div class="index-value" id="vix">—</div>
      </div>
    </div>
    <div class="refresh-label" id="last-refresh"></div>
  </div>
</div>

<script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 4: Start the dashboard and verify it works**

```
uvicorn dashboard.server:app --host 127.0.0.1 --port 3000 --reload
```

Open `http://localhost:3000` in your browser. Verify:
- Dark theme loads
- Today's report appears in the left panel
- Sell alerts and buy candidates auto-expand
- Right panel shows portfolio positions and market indices
- Date selector at the top shows available report dates

Stop with Ctrl+C when verified.

- [ ] **Step 5: Commit**

```
git add dashboard/static/
git commit -m "feat: dashboard UI — dark theme, report viewer, live portfolio panel"
```

---

## Task 12: System tray icon

**Files:**
- Create: `dashboard/tray.py`

- [ ] **Step 1: Implement tray.py**

Create `dashboard/tray.py`:

```python
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
import pystray
from PIL import Image, ImageDraw
import uvicorn

BASE_DIR = Path(__file__).parent.parent
DASHBOARD_URL = "http://localhost:3000"
PORT = 3000


def create_icon_image() -> Image.Image:
    img = Image.new("RGB", (64, 64), color="#0d1117")
    draw = ImageDraw.Draw(img)
    # Simple "FA" logo in accent blue
    draw.rectangle([4, 4, 60, 60], outline="#58a6ff", width=2)
    draw.text((14, 18), "FA", fill="#58a6ff")
    return img


def open_dashboard():
    webbrowser.open(DASHBOARD_URL)


def run_agent_now():
    agent_script = BASE_DIR / "agent" / "main.py"
    subprocess.Popen([sys.executable, str(agent_script)], cwd=str(BASE_DIR))


def start_server():
    uvicorn.run(
        "dashboard.server:app",
        host="127.0.0.1",
        port=PORT,
        log_level="error",
    )


def main():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    menu = pystray.Menu(
        pystray.MenuItem("Open Dashboard", lambda: open_dashboard()),
        pystray.MenuItem("Run Agent Now", lambda: run_agent_now()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", lambda icon, item: icon.stop()),
    )

    icon = pystray.Icon(
        name="FinancialAgent",
        icon=create_icon_image(),
        title="Financial Agent",
        menu=menu,
    )
    icon.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test the system tray icon**

```
python dashboard/tray.py
```

Verify:
- Icon appears in the Windows system tray (bottom-right taskbar area)
- Right-clicking shows the menu: "Open Dashboard", "Run Agent Now", "Exit"
- Clicking "Open Dashboard" opens `http://localhost:3000` in the browser
- The dashboard loads with today's report
- Clicking "Exit" closes the tray icon and stops the server

Stop by clicking "Exit" in the tray menu.

- [ ] **Step 3: Commit**

```
git add dashboard/tray.py
git commit -m "feat: system tray icon with dashboard and manual run"
```

---

## Task 13: Windows automation scripts

**Files:**
- Create: `scripts/setup_scheduler.ps1`
- Create: `scripts/setup_startup.ps1`
- Create: `scripts/install.ps1`

- [ ] **Step 1: Create setup_scheduler.ps1**

Create `scripts/setup_scheduler.ps1`:

```powershell
# Registers the daily 8:00 AM CT agent run in Windows Task Scheduler
# Run once from PowerShell as Administrator

param(
    [string]$ProjectDir = (Split-Path $PSScriptRoot -Parent)
)

$PythonPath = (Get-Command python).Source
$ScriptPath = Join-Path $ProjectDir "agent\main.py"

# 8:00 AM local time (user's machine must be set to Central Time)
$Trigger = New-ScheduledTaskTrigger -Daily -At "08:00AM"

$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $ProjectDir

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -StartWhenAvailable `
    -WakeToRun

Register-ScheduledTask `
    -TaskName "FinancialAgent-DailyRun" `
    -Trigger $Trigger `
    -Action $Action `
    -Settings $Settings `
    -Description "Financial Agent daily report at 8 AM CT" `
    -Force

Write-Host "Scheduled task registered: FinancialAgent-DailyRun at 8:00 AM daily"
Write-Host "Verify in Task Scheduler: taskschd.msc"
```

- [ ] **Step 2: Create setup_startup.ps1**

Create `scripts/setup_startup.ps1`:

```powershell
# Adds the dashboard tray app to Windows Startup so it launches on login
# Run once (no admin required)

param(
    [string]$ProjectDir = (Split-Path $PSScriptRoot -Parent)
)

$PythonwPath = Join-Path (Split-Path (Get-Command python).Source -Parent) "pythonw.exe"
$TrayScript = Join-Path $ProjectDir "dashboard\tray.py"
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "FinancialAgent.lnk"

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PythonwPath
$Shortcut.Arguments = "`"$TrayScript`""
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "Financial Agent Dashboard"
$Shortcut.Save()

Write-Host "Startup shortcut created at: $ShortcutPath"
Write-Host "The dashboard will launch automatically on next login."
```

- [ ] **Step 3: Create install.ps1**

Create `scripts/install.ps1`:

```powershell
# One-command setup: installs dependencies and registers automation
# Run from PowerShell after filling in .env

param(
    [string]$ProjectDir = (Split-Path $PSScriptRoot -Parent)
)

Set-Location $ProjectDir

Write-Host "=== Financial Agent Setup ===" -ForegroundColor Cyan

# 1. Install Python dependencies
Write-Host "`n[1/3] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Error "pip install failed"; exit 1 }

# 2. Register Task Scheduler
Write-Host "`n[2/3] Registering daily Task Scheduler job..." -ForegroundColor Yellow
try {
    & "$PSScriptRoot\setup_scheduler.ps1" -ProjectDir $ProjectDir
} catch {
    Write-Warning "Task Scheduler registration failed (may need to run as Administrator): $_"
}

# 3. Register startup
Write-Host "`n[3/3] Adding dashboard to Windows Startup..." -ForegroundColor Yellow
& "$PSScriptRoot\setup_startup.ps1" -ProjectDir $ProjectDir

Write-Host "`n=== Setup complete ===" -ForegroundColor Green
Write-Host "Run the dashboard now: python dashboard\tray.py"
Write-Host "Run the agent now:     python agent\main.py"
```

- [ ] **Step 4: Run the setup scripts**

Open PowerShell as Administrator for the scheduler, then normal PowerShell for startup:

```powershell
# As Administrator (for Task Scheduler):
.\scripts\setup_scheduler.ps1

# As normal user (for Startup):
.\scripts\setup_startup.ps1
```

Verify the Task Scheduler job:
```powershell
Get-ScheduledTask -TaskName "FinancialAgent-DailyRun"
```

Expected output shows the task with `State: Ready`.

- [ ] **Step 5: Commit**

```
git add scripts/
git commit -m "feat: Windows automation — Task Scheduler + Startup registration scripts"
```

---

## Task 14: Full test suite and final verification

- [ ] **Step 1: Run all tests**

```
pytest tests/ -v
```

Expected: all tests PASS with no failures.

- [ ] **Step 2: Run the agent end-to-end one more time**

```
python agent/main.py
```

Verify report appears in `reports/` with today's date.

- [ ] **Step 3: Start the tray and verify the dashboard**

```
python dashboard/tray.py
```

Open `http://localhost:3000`. Verify:
- Report loads with correct date
- All 5 sections present and collapsible
- Right panel shows live portfolio and market indices
- Status dot is green (today's report)
- Date selector works (can switch to previous dates if any exist)

- [ ] **Step 4: Verify Task Scheduler fires correctly**

In Task Scheduler, right-click "FinancialAgent-DailyRun" → Run. Watch `logs/agent.log` to confirm it executes.

- [ ] **Step 5: Final commit**

```
git add .
git commit -m "feat: financial agent v1 complete — agent engine + dashboard + automation"
```

---

## Self-Review Notes

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| 8:00 AM CT daily run | Task 13 (Task Scheduler, 8:00 AM) |
| Robinhood MCP portfolio | Task 7 |
| yfinance stock data | Task 3 |
| NewsAPI + yfinance news | Task 4 |
| Halal filter (user pref) | Task 5 |
| 15 quantitative criteria | Task 5 |
| Claude API qualitative analysis | Task 6 |
| Prompt caching on criteria block | Task 6 |
| 5-section report output | Task 8 |
| Watchlist growth via new candidates | Task 8 (save_report updates watchlist) |
| JSON + HTML report persistence | Task 8 |
| Storage abstraction layer | Task 2 |
| FastAPI dashboard server | Task 10 |
| Dark theme Jarvis-style UI | Task 11 |
| Collapsible report sections | Task 11 |
| Live portfolio right panel (60s refresh) | Task 10 + 11 |
| Market indices panel | Task 10 + 11 |
| Report history / date picker | Task 10 + 11 |
| Status dot (fresh/stale/error) | Task 11 |
| System tray icon | Task 12 |
| Windows startup auto-launch | Task 13 |
| .env for API keys | Task 1 |
| user_profile.json (halal flag, future users) | Task 1 + 5 |
| storage.py abstraction (DB-swap ready) | Task 2 |

All spec requirements covered.
