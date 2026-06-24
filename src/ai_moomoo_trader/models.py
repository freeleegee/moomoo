from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass(frozen=True)
class Signal:
    symbol: str
    side: Side
    confidence: float
    reason: str
    price: float
    timestamp: datetime


@dataclass(frozen=True)
class Position:
    symbol: str
    qty: float
    avg_price: float

    @property
    def market_value(self) -> float:
        return self.qty * self.avg_price


@dataclass(frozen=True)
class AccountState:
    cash: float
    equity: float
    positions: dict[str, Position]
    realized_pnl_today: float = 0.0


@dataclass(frozen=True)
class OrderPlan:
    symbol: str
    side: Side
    qty: float
    order_type: OrderType
    limit_price: float | None
    reason: str
    dry_run: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def estimated_value(self) -> float:
        if self.limit_price is None:
            return 0.0
        return self.qty * self.limit_price
