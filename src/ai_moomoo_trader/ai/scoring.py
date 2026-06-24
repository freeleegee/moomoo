from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class AIScore:
    symbol: str
    trend_score: float
    momentum_score: float
    volatility_risk: float
    final_score: float
    reason: str


class HeuristicAIScorer:
    """A safe local AI placeholder.

    This is intentionally deterministic and does not call an LLM yet. It creates
    an AI-like research score from price-derived features, so the trading
    pipeline can already support an AI factor without leaking API keys or
    relying on unstable external services.
    """

    def score(self, prices: pd.DataFrame) -> AIScore:
        if len(prices) < 30:
            symbol = str(prices["symbol"].iloc[-1]) if len(prices) else "UNKNOWN"
            return AIScore(symbol, 50.0, 50.0, 50.0, 50.0, "insufficient data; neutral score")

        df = prices.copy()
        symbol = str(df["symbol"].iloc[-1])
        close = df["close"].astype(float)
        ret20 = close.iloc[-1] / close.iloc[-21] - 1
        ma20 = close.rolling(20).mean().iloc[-1]
        ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else close.rolling(30).mean().iloc[-1]
        daily_ret = close.pct_change().dropna()
        vol20 = daily_ret.tail(20).std()

        trend_score = 50 + max(-25, min(25, ((ma20 / ma60) - 1) * 500))
        momentum_score = 50 + max(-25, min(25, ret20 * 200))
        volatility_risk = max(0, min(100, vol20 * 1000))
        final_score = max(0, min(100, 0.45 * trend_score + 0.45 * momentum_score + 0.10 * (100 - volatility_risk)))
        reason = f"trend={trend_score:.1f}, momentum={momentum_score:.1f}, vol_risk={volatility_risk:.1f}"
        return AIScore(symbol, trend_score, momentum_score, volatility_risk, final_score, reason)
