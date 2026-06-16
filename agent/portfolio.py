import asyncio
import json
import logging
from pathlib import Path
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

log = logging.getLogger(__name__)

ROBINHOOD_MCP_URL = "https://agent.robinhood.com/mcp/trading"

PORTFOLIO_TOOL_NAMES = [
    "get_portfolio", "portfolio", "get_positions", "positions",
    "get_holdings", "holdings", "account_portfolio",
]


async def _fetch_portfolio_async(auth_token: str | None = None) -> list[dict]:
    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
    async with streamablehttp_client(ROBINHOOD_MCP_URL, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            available = [t.name for t in tools.tools]
            log.info(f"Robinhood MCP available tools: {available}")
            for name in PORTFOLIO_TOOL_NAMES:
                if name in available:
                    result = await session.call_tool(name, {})
                    return _parse_result(result)
            raise ValueError(
                f"No portfolio tool found in Robinhood MCP. Available: {available}"
            )


def _parse_result(result) -> list[dict]:
    if not result.content:
        return []
    raw = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("positions", "holdings", "portfolio", "results"):
            if key in data:
                return data[key]
    return []


def fetch_portfolio(auth_token: str | None = None) -> list[dict]:
    """Fetch portfolio from Robinhood MCP. Returns list of position dicts."""
    return asyncio.run(_fetch_portfolio_async(auth_token))


def load_portfolio_fallback(base_dir: Path) -> list[dict]:
    """Fallback: read holdings from data/holdings.json if MCP is unavailable."""
    path = base_dir / "data" / "holdings.json"
    if not path.exists():
        log.warning("No data/holdings.json fallback file found. Returning empty portfolio.")
        return []
    return json.loads(path.read_text(encoding="utf-8"))
