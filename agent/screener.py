from dataclasses import dataclass
from agent.data import StockData


HALAL_EXCLUDED_COUNTRIES = {"Israel", "IL"}

HALAL_EXCLUDED_TICKERS = {
    "NICE", "CEVA", "CHKP", "CYBR", "MNDY", "WIX", "FVRR", "GLBE",
    "TEVA", "GKOS", "NNDM", "MICT",
}

HALAL_EXCLUDED_KEYWORDS = {
    "alcohol", "beer", "wine", "spirits", "brewery", "brewer", "distillery", "distiller",
    "gambling", "casino", "betting", "lottery", "wagering",
    "pork", "swine",
    "adult entertainment", "pornography",
}

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

    # Criterion 1: Market cap > $1 billion
    if stock.market_cap is None or stock.market_cap <= 1_000_000_000:
        failed.append(1)

    # Criterion 2: Profit margin positive
    if stock.profit_margin is None or stock.profit_margin <= 0:
        failed.append(2)

    # Criterion 3: Total cash >= $1,000,000 (in the millions minimum)
    if stock.total_cash is None or stock.total_cash < 1_000_000:
        failed.append(3)

    # Criterion 4: Forward P/E positive
    if stock.forward_pe is None or stock.forward_pe <= 0:
        failed.append(4)

    # Criterion 5: One-year return strictly > 15%
    if stock.one_year_return is None or stock.one_year_return <= 0.15:
        failed.append(5)

    # Criterion 6: Current price <= analyst mean target
    if (stock.current_price is None or stock.analyst_mean_target is None
            or stock.current_price > stock.analyst_mean_target):
        failed.append(6)

    # Criterion 7: Current price >= 80% of 52-week high (momentum filter)
    if (stock.current_price is None or stock.week_52_high is None
            or stock.current_price < 0.8 * stock.week_52_high):
        failed.append(7)

    # Criterion 8: More than 1,000 employees
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
