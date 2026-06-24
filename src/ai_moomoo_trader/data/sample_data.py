from __future__ import annotations

import numpy as np
import pandas as pd


def generate_prices(symbol: str, days: int = 80, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed + abs(hash(symbol)) % 10_000)
    dates = pd.date_range(end=pd.Timestamp.utcnow().normalize(), periods=days, freq="B")
    drift = 0.001
    noise = rng.normal(0, 0.018, size=days)
    close = 100 * np.cumprod(1 + drift + noise)
    return pd.DataFrame({"symbol": symbol, "close": close}, index=dates)
