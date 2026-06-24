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
    min_confidence: float = Field(default=0.55, ge=0, le=1)
    max_position_pct: float = Field(default=0.10, gt=0, le=1)
    max_order_value: float = Field(default=500, gt=0)
    max_daily_loss_pct: float = Field(default=0.02, gt=0, le=1)
    max_drawdown_pct: float = Field(default=0.08, gt=0, le=1)
    risk_per_trade_pct: float = Field(default=0.005, gt=0, le=1)
    min_cash_pct: float = Field(default=0.20, ge=0, le=1)
    stop_loss_pct: float = Field(default=0.05, gt=0, le=1)
    take_profit_pct: float = Field(default=0.15, gt=0, le=2)
    max_holding_days: int = Field(default=20, ge=1)
    max_open_positions: int = Field(default=8, ge=1)
    whole_share_only: bool = True


class StrategyConfig(BaseModel):
    name: str = "moving_average_cross"
    symbols: list[str]
    fast_window: int = 5
    slow_window: int = 20
    ai_score_min: float = Field(default=55.0, ge=0, le=100)
    lookback_days: int = Field(default=140, ge=30)


class DataConfig(BaseModel):
    source: str = "sample"  # sample | moomoo


class AppConfig(BaseModel):
    broker: BrokerConfig
    account: AccountConfig
    risk: RiskConfig
    strategy: StrategyConfig
    data: DataConfig = DataConfig()


def load_config(path: str | Path) -> AppConfig:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return AppConfig(**data)
