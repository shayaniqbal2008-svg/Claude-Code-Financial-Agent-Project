import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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
