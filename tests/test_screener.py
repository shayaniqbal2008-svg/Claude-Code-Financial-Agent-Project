import pytest
from agent.data import StockData
from agent.screener import halal_screen, screen_quantitative, screen, ScreenResult


def make_stock(**kwargs) -> StockData:
    defaults = dict(
        ticker="TEST", market_cap=5_000_000_000, profit_margin=0.20,
        total_cash=500_000_000, forward_pe=25.0, one_year_return=0.30,
        analyst_mean_target=150.0, current_price=130.0, week_52_high=145.0,
        employees=5000, country="United States", industry="Semiconductors",
        sector="Technology", news=[]
    )
    defaults.update(kwargs)
    return StockData(**defaults)


# --- Halal filter ---

def test_halal_screen_passes_us_tech_stock():
    assert halal_screen(make_stock(), enabled=True) is True


def test_halal_screen_fails_israeli_company():
    assert halal_screen(make_stock(country="Israel"), enabled=True) is False


def test_halal_screen_fails_known_excluded_ticker():
    assert halal_screen(make_stock(ticker="CHKP"), enabled=True) is False


def test_halal_screen_fails_alcohol_industry():
    assert halal_screen(make_stock(industry="Beverages - Brewers"), enabled=True) is False


def test_halal_screen_fails_gambling_industry():
    assert halal_screen(make_stock(industry="Gambling"), enabled=True) is False


def test_halal_screen_disabled_passes_everything():
    assert halal_screen(make_stock(country="Israel"), enabled=False) is True


# --- Quantitative criteria ---

def test_screen_quantitative_passes_all_criteria():
    passed, failed = screen_quantitative(make_stock())
    assert passed is True
    assert failed == []


def test_criterion_1_market_cap_below_1b_fails():
    _, failed = screen_quantitative(make_stock(market_cap=500_000_000))
    assert 1 in failed


def test_criterion_2_negative_margin_fails():
    _, failed = screen_quantitative(make_stock(profit_margin=-0.05))
    assert 2 in failed


def test_criterion_3_cash_in_thousands_fails():
    _, failed = screen_quantitative(make_stock(total_cash=500_000))
    assert 3 in failed


def test_criterion_3_none_cash_fails():
    _, failed = screen_quantitative(make_stock(total_cash=None))
    assert 3 in failed


def test_criterion_4_negative_forward_pe_fails():
    _, failed = screen_quantitative(make_stock(forward_pe=-5.0))
    assert 4 in failed


def test_criterion_5_return_below_15_pct_fails():
    _, failed = screen_quantitative(make_stock(one_year_return=0.10))
    assert 5 in failed


def test_criterion_5_exactly_15_pct_fails():
    # "greater than 15%" means strictly > 0.15
    _, failed = screen_quantitative(make_stock(one_year_return=0.15))
    assert 5 in failed


def test_criterion_6_price_above_analyst_target_fails():
    _, failed = screen_quantitative(make_stock(current_price=160.0, analyst_mean_target=150.0))
    assert 6 in failed


def test_criterion_7_price_below_80pct_high_fails():
    # current = 100, high = 145 → 100 < 0.8 * 145 = 116
    _, failed = screen_quantitative(make_stock(current_price=100.0, week_52_high=145.0))
    assert 7 in failed


def test_criterion_8_employees_below_1000_fails():
    _, failed = screen_quantitative(make_stock(employees=500))
    assert 8 in failed


def test_multiple_criteria_failures_reported():
    _, failed = screen_quantitative(make_stock(market_cap=500_000_000, profit_margin=-0.1))
    assert 1 in failed
    assert 2 in failed


# --- Combined screen ---

def test_screen_passes_good_stock():
    result = screen(make_stock(), halal_filter=True)
    assert result.passed_halal is True
    assert result.passed_quant is True
    assert result.failed_criteria == []


def test_screen_halal_fail_skips_quant():
    result = screen(make_stock(country="Israel"), halal_filter=True)
    assert result.passed_halal is False
    assert result.passed_quant is False


def test_screen_returns_screen_result_type():
    result = screen(make_stock())
    assert isinstance(result, ScreenResult)


def test_screen_quantitative_exactly_at_80pct_high_passes():
    # current = 116, high = 145 → 116 >= 0.8 * 145 = 116 exactly — should PASS
    passed, failed = screen_quantitative(make_stock(current_price=116.0, week_52_high=145.0))
    assert 7 not in failed


def test_screen_quantitative_none_fields_fail():
    _, failed = screen_quantitative(make_stock(
        market_cap=None, forward_pe=None, one_year_return=None,
        analyst_mean_target=None, current_price=None
    ))
    assert 1 in failed
    assert 4 in failed
    assert 5 in failed
    assert 6 in failed
    assert 7 in failed
