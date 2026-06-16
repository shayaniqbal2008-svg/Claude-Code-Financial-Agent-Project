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
