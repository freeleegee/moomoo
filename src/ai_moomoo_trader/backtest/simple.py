from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from ..models import Side
from ..strategies.moving_average import MovingAverageCrossStrategy


@dataclass(frozen=True)
class BacktestResult:
    symbol: str
    trades: int
    total_return: float
    buy_and_hold_return: float
    max_drawdown: float


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = equity / peak - 1
    return float(dd.min())


def run_long_only_backtest(symbol: str, prices: pd.DataFrame, fast: int, slow: int) -> BacktestResult:
    strategy = MovingAverageCrossStrategy(fast, slow)
    cash = 1.0
    qty = 0.0
    trades = 0
    equity_curve: list[float] = []
    close = prices["close"].astype(float)

    for end in range(slow + 2, len(prices) + 1):
        window = prices.iloc[:end]
        price = float(window["close"].iloc[-1])
        sig = strategy.generate_signal(window)
        if sig and sig.side == Side.BUY and qty == 0:
            qty = cash / price
            cash = 0.0
            trades += 1
        elif sig and sig.side == Side.SELL and qty > 0:
            cash = qty * price
            qty = 0.0
            trades += 1
        equity_curve.append(cash + qty * price)

    if qty > 0:
        cash = qty * float(close.iloc[-1])
    equity = pd.Series(equity_curve or [1.0])
    total_return = cash - 1.0
    buy_hold = float(close.iloc[-1] / close.iloc[0] - 1)
    return BacktestResult(symbol, trades, float(total_return), buy_hold, _max_drawdown(equity))
