# Financial Agent — Design Spec
**Date:** 2026-06-15  
**Author:** Shayan Iqbal (via Claude Code)  
**Status:** Approved
---

## What We're Building

A personal automated financial analysis agent that runs every morning at 8:00 AM CT, reads Shayan's live Robinhood portfolio, screens stocks against a strict 15-criteria investment framework, weighs current news and political developments heavily, and produces a structured daily advisory report viewable in an always-on local dashboard. Shayan executes all trades manually — this is a recommendation and research engine, not a trading bot.

---

## Architecture Overview

Four loosely-coupled layers, each with one job:

```
SCHEDULER (Windows Task Scheduler)
  Fires Python at 8:00 AM CT daily
        │
AGENT ENGINE (Python)
  1. Fetch portfolio       ← Robinhood MCP
  2. Fetch stock data      ← yfinance
  3. Fetch news            ← yfinance (ticker) + NewsAPI (macro)
  4. Screen candidates     ← 15 criteria (+ halal filter if user pref on)
  5. Claude API analysis   ← portfolio + news + screened stocks → report
        │
STORAGE (local files, storage abstraction layer)
  reports/YYYY-MM-DD.json   structured report data
  reports/YYYY-MM-DD.html   rendered standalone report
  data/watchlist.json       candidate stocks (grows over time)
  data/user_profile.json    per-user settings
        │
DASHBOARD (FastAPI + browser)
  localhost:3000 — always-on, auto-starts with Windows
  System tray icon (pystray) — one click opens browser
  Left panel: today's full report (scrollable, sections collapsible)
  Right panel: live portfolio + top market indices (refreshes every 60s)
```

The agent engine and dashboard are independent. The engine writes files; the dashboard reads and serves them. The dashboard is always live even when no report is running.

---

## Agent Engine — Daily Run Sequence

Runs at **8:00 AM CT** (market opens 8:30 AM CT) so the report is ready before market open.

### Step 1 — Portfolio Fetch
Connects to Robinhood MCP (`https://agent.robinhood.com/mcp/trading`). Pulls current positions: ticker, quantity, current price, average cost basis.

### Step 2 — Stock Data Fetch
For every holding and every watchlist candidate, fetches via yfinance:
- Market cap, profit margin, total cash
- Forward P/E, 1-year price return
- Analyst mean price target, 52-week high, current price
- Employee count

### Step 3 — News Fetch
- **Ticker-level:** yfinance `ticker.news` for all holdings + watchlist stocks
- **Macro/political/economic:** NewsAPI free tier — US business, technology, top headlines from the last 24 hours

### Step 4 — Screening Pipeline
Runs before any expensive API calls:
1. **Halal pre-filter** (only if `user_profile.halal_filter == true`) — drops excluded stocks silently, no further processing
2. **Quantitative criteria 1–8** — hard pass/fail on the numbers fetched in Step 2
3. Stocks passing both advance to Step 5 for qualitative analysis

### Step 5 — Claude API Analysis
Single structured prompt with prompt caching on the static 15-criteria block. Input contains:
- Current holdings with quantitative scores
- Candidates that cleared quantitative screening
- Today's news (ticker-level + macro headlines)
- Full 15-criteria framework + instructions

Output is structured JSON with five sections:
1. **Portfolio Review** — grade each holding against all 15 criteria
2. **Sell Alerts** — holdings failing criteria or carrying news/political risk
3. **Buy Candidates** — screened stocks passing all 15 criteria
4. **News Briefing** — headlines materially affecting portfolio and candidates
5. **Market & Political Alerts** — macro/political developments that could move the market

Saved as both `reports/YYYY-MM-DD.json` and `reports/YYYY-MM-DD.html`.

Claude's analysis also returns a list of new candidate tickers worth tracking (AI-infrastructure stocks from its training knowledge that fit the thesis). Any new tickers not already in `watchlist.json` are appended automatically. This is how the watchlist grows — each morning run can surface new candidates, which then get fully screened on subsequent runs.

**Estimated runtime:** 2–4 minutes.

---

## The 15 Investment Criteria

These are the sole decision framework. No additions, removals, or reinterpretations.

### Quantitative (hard pass/fail)
1. Market cap > $1 billion
2. Profit margin positive
3. Total cash positive and in the millions minimum
4. Forward P/E positive
5. One-year price return > 15%
6. Current price ≤ analyst mean price target
7. Current price ≥ 80% of 52-week high (momentum filter)
8. Employee count > 1,000

### Qualitative (Claude API judgment)
9. NOT an Israeli company, NOT primarily Israel-funded
10. No significant war/political/geopolitical exposure materially affecting the stock
11. Strong, robust technology with genuine growth potential
12. Fits AI-infrastructure theme (memory, storage, power, cooling, networking, chips)
13. Financial highlights overall positive — healthy trends, no major red flags
14. Acts as supplier or enabler to AI hyperscalers (NVDA, Google, Microsoft, Amazon, Meta)
15. GOOGL and AAPL are always standing positions — flag if underweight, never recommend selling without significant specific cause

---

## Halal Filter (User Preference)

A lightweight pre-screen that runs before the 15 criteria, activated only when `user_profile.halal_filter == true`. Currently on for Shayan; off by default for any future user. Excludes companies that:
- Are headquartered in Israel or primarily Israel-funded
- Derive significant revenue from haram activities (alcohol, pork, gambling, haram entertainment, adult content, interest-based banking/insurance)
- Carry interest-bearing debt exceeding ~one-third of total assets

Implemented as a single `halal_screen(ticker)` function in `screener.py`. Not a main architectural concern — a user preference that activates a simple check.

---

## Dashboard UI

**Always-on local web app** served by FastAPI at `localhost:3000`. Auto-starts with Windows. System tray icon (pystray) sits in taskbar — one click opens the browser.

**Layout:**
- Dark theme (Jarvis aesthetic)
- **Left panel (primary):** Today's full report, scrollable, sections collapsed by default with expand-on-click. Report history nav at top — date picker loads archived reports.
- **Right panel (secondary):** Live portfolio positions with P&L per holding (refreshes every 60s via Robinhood MCP). Below: S&P 500, NASDAQ, VIX.
- **Status indicator:** Green = today's report is fresh. Yellow = stale (yesterday's). Red = last run failed.

---

## Storage & File Structure

```
Financial Agent/
├── agent/
│   ├── main.py           # daily run entry point
│   ├── portfolio.py      # Robinhood MCP integration
│   ├── screener.py       # 15-criteria + halal filter
│   ├── news.py           # yfinance + NewsAPI fetching
│   ├── analyst.py        # Claude API calls
│   ├── report.py         # assembles + saves report
│   └── storage.py        # storage abstraction layer (swap to DB for multi-user)
├── dashboard/
│   ├── server.py         # FastAPI app
│   ├── tray.py           # pystray system tray icon
│   └── static/           # HTML/CSS/JS for the UI
├── reports/              # daily report files (JSON + HTML)
├── data/
│   ├── watchlist.json    # candidate stocks (grows over time)
│   └── user_profile.json # settings per user (halal_filter, etc.)
├── logs/
│   └── agent.log
└── .env                  # API keys — never committed
```

**Storage abstraction:** All file reads/writes go through `storage.py`. When the system expands to multi-user/SaaS, only this module changes — the rest of the codebase is unaffected.

---

## Scheduling & Auto-Start

- **Daily run:** Windows Task Scheduler fires `python agent/main.py` at **8:00 AM CT** every day. Survives reboots.
- **Dashboard:** Added to Windows Startup folder — launches `python dashboard/tray.py` on login. Runs silently in background until the tray icon is clicked.

---

## Dependencies

```
anthropic         # Claude API (qualitative analysis + report generation)
yfinance          # stock data + ticker-level news
fastapi           # dashboard web server
uvicorn           # ASGI server
pystray           # system tray icon
pillow            # icon image rendering (required by pystray)
newsapi-python    # macro/political/economic headlines
httpx             # HTTP client for Robinhood MCP
python-dotenv     # loads .env
```

---

## One-Time Setup Steps

1. Install Python 3.11+ from python.org (real installer, not Windows Store stub)
2. Create Anthropic account → generate API key at console.anthropic.com
3. Create NewsAPI account → get free API key at newsapi.org
4. Add Robinhood MCP: `claude mcp add robinhood-trading --transport http https://agent.robinhood.com/mcp/trading`
5. Add API keys to `.env`
6. `pip install -r requirements.txt`
7. Register Windows Task Scheduler job (script provided)
8. Register dashboard in Windows Startup folder (script provided)

---

## Multi-User / Future Considerations

- `user_profile.json` is the hook for per-user preferences. Halal filter is opt-in, off by default.
- `storage.py` abstraction makes a future database migration a one-file change.
- When going multi-user or SaaS: swap local files for PostgreSQL/Supabase. The agent engine and dashboard code don't change.
- Data collection from users (for improving the model) requires opt-in consent and a central server — designed for later, not now.

---

## Constraints

1. Advisory only — no auto-execution in v1
2. 15 criteria are the sole decision framework
3. Halal filter is user preference (on for Shayan, off by default for others)
4. News and politics are primary signals, weighted heavily in every Claude call
5. Research casts wide net but only surfaces stocks passing every criterion
6. Run halal + quantitative screening before Claude API calls to avoid waste
