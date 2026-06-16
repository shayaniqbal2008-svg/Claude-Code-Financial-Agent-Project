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
