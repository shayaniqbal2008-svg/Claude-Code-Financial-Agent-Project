from datetime import datetime
from pathlib import Path
from agent.storage import Storage


def assemble_report(analysis: dict, date: str | None = None) -> dict:
    """Add metadata (date, generated_at) to the raw Claude analysis dict."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    return {
        "date": date,
        "generated_at": datetime.now().isoformat(),
        **analysis,
    }


def save_report(report: dict, storage: Storage) -> Path:
    """Write JSON and HTML to storage, then append new watchlist candidates."""
    date = report["date"]
    json_path = storage.save_report_json(date, report)
    storage.save_report_html(date, render_html(report))

    # Append new candidates to watchlist (preserves existing entries)
    new_candidates = report.get("new_watchlist_candidates", [])
    if new_candidates:
        existing = storage.load_watchlist()
        storage.save_watchlist(list(set(existing + new_candidates)))

    return json_path


def render_html(report: dict) -> str:
    """Produce a self-contained dark-theme HTML file for the report."""
    date = report.get("date", "")
    generated_at = report.get("generated_at", "")

    def badge(urgency: str) -> str:
        colors = {"high": "#e74c3c", "medium": "#f39c12", "low": "#2ecc71"}
        return (
            f'<span style="background:{colors.get(urgency, "#888")};color:#fff;'
            f'padding:2px 8px;border-radius:4px;font-size:0.8em">'
            f'{urgency.upper()}</span>'
        )

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
        f'<td style="font-size:1.2em;font-weight:bold">{h.get("grade", "?")}</td>'
        f'<td>{h.get("summary", "")}</td></tr>'
        for h in report.get("portfolio_review", [])
    )
    news_items = "".join(
        f'<div class="news-item"><strong>{n["headline"]}</strong>'
        f'<p>{n["impact"]}</p>'
        f'<small>Tickers: {", ".join(n.get("tickers_affected", []))}</small></div>'
        for n in report.get("news_briefing", [])
    )
    alert_items = "".join(
        f'<div class="alert-item">{badge(a["urgency"])} <strong>{a["event"]}</strong>'
        f'<p>{a["market_impact"]}</p></div>'
        for a in report.get("market_political_alerts", [])
    )

    no_sell = "<tr><td colspan=3>No sell alerts today</td></tr>"
    no_buy = "<tr><td colspan=2>No qualifying candidates today</td></tr>"

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
  .meta{{color:#8b949e;font-size:0.85em;margin-top:4px}}
</style>
</head>
<body>
<h1>Financial Agent Report</h1>
<p class="meta">Date: {date} &nbsp;|&nbsp; Generated: {generated_at}</p>

<h2>⚠ Sell Alerts ({len(report.get("sell_alerts", []))})</h2>
<table><tr><th>Ticker</th><th>Reason</th><th>Urgency</th></tr>
{sell_rows or no_sell}</table>

<h2>✓ Buy Candidates ({len(report.get("buy_candidates", []))})</h2>
<table><tr><th>Ticker</th><th>Rationale</th></tr>
{buy_rows or no_buy}</table>

<h2>Portfolio Review</h2>
<table><tr><th>Ticker</th><th>Grade</th><th>Summary</th></tr>
{portfolio_rows}</table>

<h2>News Briefing</h2>
{news_items or "<p>No significant news today.</p>"}

<h2>Market &amp; Political Alerts</h2>
{alert_items or "<p>No significant alerts today.</p>"}
</body>
</html>"""
