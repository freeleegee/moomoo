from __future__ import annotations

from dataclasses import dataclass
from .models import AccountState, OrderPlan, OrderType, Side, Signal
from .config import RiskConfig


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    order: OrderPlan | None
    reason: str


class RiskEngine:
    def __init__(self, config: RiskConfig):
        self.config = config

    def evaluate(self, signal: Signal, account: AccountState) -> RiskDecision:
        if signal.confidence < self.config.min_confidence:
            return RiskDecision(False, None, "confidence below threshold")
        if signal.price <= 0:
            return RiskDecision(False, None, "invalid signal price")

        max_daily_loss = account.equity * self.config.max_daily_loss_pct
        if account.realized_pnl_today <= -max_daily_loss:
            return RiskDecision(False, None, "daily loss limit reached")

        min_cash = account.equity * self.config.min_cash_pct
        if account.cash <= min_cash and signal.side == Side.BUY:
            return RiskDecision(False, None, "minimum cash reserve reached")

        current_position_value = account.positions.get(signal.symbol).market_value if signal.symbol in account.positions else 0.0
        max_position_value = account.equity * self.config.max_position_pct
        available_position_room = max(0.0, max_position_value - current_position_value)

        if signal.side == Side.SELL:
            pos = account.positions.get(signal.symbol)
            if not pos or pos.qty <= 0:
                return RiskDecision(False, None, "no long position to sell")
            return RiskDecision(True, OrderPlan(signal.symbol, signal.side, pos.qty, OrderType.LIMIT, signal.price, signal.reason), "approved sell")

        if len(account.positions) >= self.config.max_open_positions and signal.symbol not in account.positions:
            return RiskDecision(False, None, "max open positions reached")

        usable_cash = max(0.0, account.cash - min_cash)
        risk_budget = account.equity * self.config.risk_per_trade_pct
        stop_loss_distance = max(signal.price * self.config.stop_loss_pct, 0.01)
        risk_sized_value = (risk_budget / stop_loss_distance) * signal.price
        order_value = min(self.config.max_order_value, available_position_room, usable_cash, risk_sized_value)

        if order_value < 5:
            return RiskDecision(False, None, "order value too small after risk filters")

        qty = round(order_value / signal.price, 6)
        if qty <= 0:
            return RiskDecision(False, None, "quantity is zero")

        return RiskDecision(True, OrderPlan(signal.symbol, signal.side, qty, OrderType.LIMIT, signal.price, signal.reason), "approved buy")
