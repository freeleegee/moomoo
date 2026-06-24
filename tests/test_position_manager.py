from datetime import datetime, timezone, timedelta

from ai_moomoo_trader.models import AccountState, Position, Side
from ai_moomoo_trader.position_manager import PositionManager


def test_snapshot_calculates_unrealized_pnl(tmp_path):
    manager = PositionManager(tmp_path / "positions.json")
    acc = AccountState(cash=1000, equity=2000, positions={"US.GOOGL": Position("US.GOOGL", 2, 100)})
    manager.sync(acc)
    snap = manager.snapshot(acc, "US.GOOGL", 115)
    assert snap is not None
    assert snap.unrealized_pnl == 30
    assert round(snap.unrealized_pct, 4) == 0.15


def test_take_profit_generates_sell_signal(tmp_path):
    manager = PositionManager(tmp_path / "positions.json")
    acc = AccountState(cash=1000, equity=2000, positions={"US.GOOGL": Position("US.GOOGL", 2, 100)})
    manager.sync(acc)
    sig = manager.exit_signal(acc, "US.GOOGL", 116, stop_loss_pct=0.05, take_profit_pct=0.15, max_holding_days=20)
    assert sig is not None
    assert sig.side == Side.SELL
    assert "take profit" in sig.reason


def test_stop_loss_generates_sell_signal(tmp_path):
    manager = PositionManager(tmp_path / "positions.json")
    acc = AccountState(cash=1000, equity=2000, positions={"US.GOOGL": Position("US.GOOGL", 2, 100)})
    manager.sync(acc)
    sig = manager.exit_signal(acc, "US.GOOGL", 94, stop_loss_pct=0.05, take_profit_pct=0.15, max_holding_days=20)
    assert sig is not None
    assert sig.side == Side.SELL
    assert "stop loss" in sig.reason


def test_max_holding_days_generates_sell_signal(tmp_path):
    path = tmp_path / "positions.json"
    manager = PositionManager(path)
    acc = AccountState(cash=1000, equity=2000, positions={"US.GOOGL": Position("US.GOOGL", 2, 100)})
    manager.sync(acc)
    old = datetime.now(timezone.utc) - timedelta(days=30)
    manager.state["US.GOOGL"] = {"first_seen": old.isoformat()}
    manager._save_state()
    sig = manager.exit_signal(acc, "US.GOOGL", 101, stop_loss_pct=0.05, take_profit_pct=0.15, max_holding_days=20)
    assert sig is not None
    assert "max holding days" in sig.reason
