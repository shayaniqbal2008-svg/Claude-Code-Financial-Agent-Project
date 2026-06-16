import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# Ensure logs directory exists before configuring file handler
(BASE_DIR / "logs").mkdir(parents=True, exist_ok=True)

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
    from agent.portfolio import fetch_portfolio, load_portfolio_fallback
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
    auth_token = os.getenv("ROBINHOOD_MCP_TOKEN")
    try:
        holdings = fetch_portfolio(auth_token=auth_token)
        if not holdings:
            raise ValueError("MCP returned empty portfolio")
        log.info(f"Got {len(holdings)} holdings from MCP")
    except Exception as e:
        log.warning(f"MCP portfolio fetch failed ({e}). Falling back to local holdings file.")
        holdings = load_portfolio_fallback(BASE_DIR)
        log.info(f"Loaded {len(holdings)} holdings from fallback file")

    # Step 2: Stock data
    log.info("Fetching stock data...")
    watchlist = storage.load_watchlist()
    holding_tickers = [
        h.get("ticker") or h.get("symbol") or h.get("instrument_id", "")
        for h in holdings
    ]
    holding_tickers = [t for t in holding_tickers if t]
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
    newsapi_key = os.getenv("NEWSAPI_KEY", "")
    if newsapi_key:
        try:
            macro_news = fetch_macro_news(api_key=newsapi_key)
            log.info(f"Got {len(macro_news)} macro headlines")
        except Exception as e:
            log.warning(f"NewsAPI failed: {e}")
    else:
        log.warning("NEWSAPI_KEY not set — skipping macro news")
    ticker_news = fetch_ticker_news(list(stock_data_map.values()))

    # Step 4: Screen candidates (watchlist only)
    log.info("Screening watchlist candidates...")
    screened = [
        screen(stock_data_map[t], halal_filter=halal_filter)
        for t in watchlist
        if t in stock_data_map
    ]
    passed = [r for r in screened if r.passed_quant]
    log.info(f"{len(passed)}/{len(screened)} candidates passed screening")

    # Step 5: Enrich holdings with stock data
    enriched_holdings = []
    for h in holdings:
        ticker = h.get("ticker") or h.get("symbol", "")
        sd = stock_data_map.get(ticker)
        enriched_holdings.append({
            "ticker": ticker,
            "quantity": h.get("quantity") or h.get("shares", 0),
            "avg_cost": h.get("avg_cost") or h.get("average_buy_price", 0),
            "current_price": sd.current_price if sd else None,
            "one_year_return": sd.one_year_return if sd else None,
            "profit_margin": sd.profit_margin if sd else None,
        })

    # Step 6: Claude API analysis
    log.info("Running Claude API analysis...")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        log.error("ANTHROPIC_API_KEY not set — cannot run analysis")
        sys.exit(1)

    analysis = analyze(
        holdings=enriched_holdings,
        candidates=screened,
        macro_news=macro_news,
        ticker_news=ticker_news,
        api_key=anthropic_key,
    )

    # Step 7: Save report
    report = assemble_report(analysis)
    path = save_report(report, storage)
    log.info(f"Report saved to {path}")
    log.info("=== Financial Agent done ===")


if __name__ == "__main__":
    run()
