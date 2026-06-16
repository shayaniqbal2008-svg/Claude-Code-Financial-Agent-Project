import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from agent.portfolio import _parse_result, load_portfolio_fallback


def make_mcp_result(content_text: str):
    result = MagicMock()
    content_item = MagicMock()
    content_item.text = content_text
    result.content = [content_item]
    return result


def test_parse_result_list_response():
    positions = [{"ticker": "AAPL", "quantity": 10}, {"ticker": "GOOGL", "quantity": 5}]
    result = make_mcp_result(json.dumps(positions))
    assert _parse_result(result) == positions


def test_parse_result_dict_with_positions_key():
    data = {"positions": [{"ticker": "NVDA", "quantity": 2}], "total": 1}
    result = make_mcp_result(json.dumps(data))
    assert _parse_result(result) == [{"ticker": "NVDA", "quantity": 2}]


def test_parse_result_dict_with_holdings_key():
    data = {"holdings": [{"ticker": "AMD", "quantity": 3}]}
    result = make_mcp_result(json.dumps(data))
    assert _parse_result(result) == [{"ticker": "AMD", "quantity": 3}]


def test_parse_result_empty_content():
    result = MagicMock()
    result.content = []
    assert _parse_result(result) == []


def test_parse_result_unknown_dict_returns_empty():
    data = {"unknown_key": [{"ticker": "XYZ"}]}
    result = make_mcp_result(json.dumps(data))
    assert _parse_result(result) == []


def test_load_portfolio_fallback_reads_file(tmp_path):
    holdings = [{"ticker": "AAPL", "quantity": 10, "avg_cost": 185.0}]
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "holdings.json").write_text(json.dumps(holdings))
    result = load_portfolio_fallback(tmp_path)
    assert result == holdings


def test_load_portfolio_fallback_returns_empty_when_missing(tmp_path):
    result = load_portfolio_fallback(tmp_path)
    assert result == []
