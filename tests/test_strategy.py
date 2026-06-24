import pandas as pd
from ai_moomoo_trader.strategies.moving_average import MovingAverageCrossStrategy


def test_strategy_returns_none_without_enough_data():
    s = MovingAverageCrossStrategy(3, 5)
    df = pd.DataFrame({"symbol": "US.AAPL", "close": [1, 2, 3]})
    assert s.generate_signal(df) is None


def test_strategy_can_emit_buy_signal():
    s = MovingAverageCrossStrategy(2, 4)
    closes = [10, 10, 10, 10, 9, 12]
    df = pd.DataFrame({"symbol": ["US.AAPL"] * len(closes), "close": closes})
    sig = s.generate_signal(df)
    assert sig is not None
    assert sig.side.value == "BUY"
