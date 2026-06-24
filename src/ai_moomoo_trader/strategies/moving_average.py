from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd
from ..models import Signal, Side


class MovingAverageCrossStrategy:
    def __init__(self, fast_window: int = 5, slow_window: int = 20):
        if fast_window >= slow_window:
            raise ValueError("fast_window must be smaller than slow_window")
        self.fast_window = fast_window
        self.slow_window = slow_window

    def generate_signal(self, prices: pd.DataFrame) -> Signal | None:
        if len(prices) < self.slow_window + 2:
            return None
        df = prices.copy()
        df["fast"] = df["close"].rolling(self.fast_window).mean()
        df["slow"] = df["close"].rolling(self.slow_window).mean()
        prev = df.iloc[-2]
        last = df.iloc[-1]
        symbol = str(last.get("symbol", "UNKNOWN"))
        price = float(last["close"])

        if prev["fast"] <= prev["slow"] and last["fast"] > last["slow"]:
            spread = (last["fast"] - last["slow"]) / last["slow"]
            return Signal(symbol, Side.BUY, min(0.95, 0.60 + float(spread) * 10), "fast MA crossed above slow MA", price, datetime.now(timezone.utc))
        if prev["fast"] >= prev["slow"] and last["fast"] < last["slow"]:
            return Signal(symbol, Side.SELL, 0.70, "fast MA crossed below slow MA", price, datetime.now(timezone.utc))
        return None
