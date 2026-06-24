from __future__ import annotations

import tomllib
from pathlib import Path
from pydantic import BaseModel, Field


class BrokerConfig(BaseModel):
    type: str = "mock"
    env: str = "SIMULATE"
    host: str = "127.0.0.1"
    port: int = 11111
    market: str = "US"


class AccountConfig(BaseModel):
    base_currency: str = "USD"
    initial_cash: float = 10_000


class RiskConfig(BaseModel):
    max_position_pct: float = Field(default=0.10, gt=0, le=1)
    max_order_value: float = Field(default=500, gt=0)
    max_daily_loss_pct: float = Field(default=0.02, gt=0, le=1)
    risk_per_trade_pct: float = Field(default=0.005, gt=0, le=1)
    min_cash_pct: float = Field(default=0.20, ge=0, le=1)


class StrategyConfig(BaseModel):
    name: str = "moving_average_cross"
    symbols: list[str]
    fast_window: int = 5
    slow_window: int = 20


class AppConfig(BaseModel):
    broker: BrokerConfig
    account: AccountConfig
    risk: RiskConfig
    strategy: StrategyConfig


def load_config(path: str | Path) -> AppConfig:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return AppConfig(**data)
