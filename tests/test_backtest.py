from ai_moomoo_trader.backtest import run_long_only_backtest
from ai_moomoo_trader.data.sample_data import generate_prices


def test_backtest_returns_metrics():
    prices = generate_prices("US.AAPL", days=80)
    result = run_long_only_backtest("US.AAPL", prices, 5, 20)
    assert result.symbol == "US.AAPL"
    assert isinstance(result.total_return, float)
    assert result.max_drawdown <= 0
