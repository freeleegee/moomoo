from ai_moomoo_trader.config import RiskConfig
from ai_moomoo_trader.models import AccountState, Signal, Side
from ai_moomoo_trader.risk import RiskEngine
from datetime import datetime, timezone


def test_low_confidence_rejected():
    engine = RiskEngine(RiskConfig())
    sig = Signal("US.AAPL", Side.BUY, 0.40, "weak", 100, datetime.now(timezone.utc))
    acc = AccountState(cash=10000, equity=10000, positions={})
    decision = engine.evaluate(sig, acc)
    assert not decision.approved


def test_buy_is_position_sized():
    engine = RiskEngine(RiskConfig(max_order_value=500, risk_per_trade_pct=0.005))
    sig = Signal("US.AAPL", Side.BUY, 0.80, "strong", 100, datetime.now(timezone.utc))
    acc = AccountState(cash=10000, equity=10000, positions={})
    decision = engine.evaluate(sig, acc)
    assert decision.approved
    assert decision.order is not None
    assert decision.order.qty <= 5


def test_buy_qty_is_whole_share_by_default():
    engine = RiskEngine(RiskConfig(max_order_value=500, risk_per_trade_pct=0.005, whole_share_only=True))
    sig = Signal("US.GOOGL", Side.BUY, 0.80, "strong", 284.46, datetime.now(timezone.utc))
    acc = AccountState(cash=10000, equity=10000, positions={})
    decision = engine.evaluate(sig, acc)
    assert decision.approved
    assert decision.order is not None
    assert decision.order.qty == 1
