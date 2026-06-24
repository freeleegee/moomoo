from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .models import AccountState, Signal, Side


@dataclass(frozen=True)
class PositionSnapshot:
    symbol: str
    qty: float
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pct: float
    holding_days: int | None


class PositionManager:
    """Small persistent position monitor for exits and readable position reports.

    Moomoo returns quantity and average cost, but not always a clean first-seen date
    through the lightweight adapter. This manager stores the first date a position is
    observed locally, then uses it for max holding-day exits.
    """

    def __init__(self, state_path: str | Path = "logs/positions.json"):
        self.state_path = Path(state_path)
        self.state: dict[str, dict[str, str]] = self._load_state()

    def _load_state(self) -> dict[str, dict[str, str]]:
        if not self.state_path.exists():
            return {}
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, indent=2, sort_keys=True), encoding="utf-8")

    def sync(self, account: AccountState, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        current_symbols = set(account.positions.keys())
        for symbol in current_symbols:
            self.state.setdefault(symbol, {"first_seen": now.isoformat()})
        for symbol in list(self.state.keys()):
            if symbol not in current_symbols:
                del self.state[symbol]
        self._save_state()

    def snapshot(self, account: AccountState, symbol: str, current_price: float) -> PositionSnapshot | None:
        pos = account.positions.get(symbol)
        if not pos or pos.qty <= 0:
            return None
        market_value = pos.qty * current_price
        cost_value = pos.qty * pos.avg_price
        unrealized_pnl = market_value - cost_value
        unrealized_pct = 0.0 if cost_value <= 0 else unrealized_pnl / cost_value
        holding_days = self._holding_days(symbol)
        return PositionSnapshot(
            symbol=symbol,
            qty=pos.qty,
            avg_price=pos.avg_price,
            current_price=current_price,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pct=unrealized_pct,
            holding_days=holding_days,
        )

    def exit_signal(
        self,
        account: AccountState,
        symbol: str,
        current_price: float,
        *,
        stop_loss_pct: float,
        take_profit_pct: float,
        max_holding_days: int,
    ) -> Signal | None:
        snap = self.snapshot(account, symbol, current_price)
        if snap is None:
            return None

        if snap.unrealized_pct <= -stop_loss_pct:
            return Signal(
                symbol,
                Side.SELL,
                0.95,
                f"position stop loss: pnl={snap.unrealized_pct:.2%}, avg={snap.avg_price:.2f}",
                current_price,
                datetime.now(timezone.utc),
            )
        if snap.unrealized_pct >= take_profit_pct:
            return Signal(
                symbol,
                Side.SELL,
                0.90,
                f"position take profit: pnl={snap.unrealized_pct:.2%}, avg={snap.avg_price:.2f}",
                current_price,
                datetime.now(timezone.utc),
            )
        if snap.holding_days is not None and snap.holding_days >= max_holding_days:
            return Signal(
                symbol,
                Side.SELL,
                0.75,
                f"position max holding days: holding_days={snap.holding_days}",
                current_price,
                datetime.now(timezone.utc),
            )
        return None

    def _holding_days(self, symbol: str) -> int | None:
        raw = self.state.get(symbol, {}).get("first_seen")
        if not raw:
            return None
        try:
            first_seen = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if first_seen.tzinfo is None:
            first_seen = first_seen.replace(tzinfo=timezone.utc)
        return max(0, (datetime.now(timezone.utc) - first_seen).days)
