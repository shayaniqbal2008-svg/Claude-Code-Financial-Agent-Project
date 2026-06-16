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
