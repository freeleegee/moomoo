from __future__ import annotations

from ..models import AccountState, OrderPlan, Position, Side
from .base import Broker


class MoomooBroker(Broker):
    """Thin adapter for moomoo OpenD.

    This adapter is intentionally small. It keeps the rest of the system broker-agnostic.
    You must run moomoo OpenD locally and log in before using it.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 11111, env: str = "SIMULATE", market: str = "US"):
        try:
            from moomoo import OpenSecTradeContext, TrdEnv, TrdMarket, OrderType, TrdSide
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Install moomoo SDK first: pip install moomoo-api") from exc

        self._sdk = {
            "TrdEnv": TrdEnv,
            "TrdMarket": TrdMarket,
            "OrderType": OrderType,
            "TrdSide": TrdSide,
        }
        trd_market = getattr(TrdMarket, market)
        self.env = getattr(TrdEnv, env)
        self.ctx = OpenSecTradeContext(filter_trdmarket=trd_market, host=host, port=port)

    def close(self) -> None:  # pragma: no cover
        self.ctx.close()

    def get_account_state(self) -> AccountState:  # pragma: no cover
        ret, acc = self.ctx.accinfo_query(trd_env=self.env)
        if ret != 0:
            raise RuntimeError(f"accinfo_query failed: {acc}")
        row = acc.iloc[0]
        cash = float(row.get("cash", row.get("power", 0.0)))
        equity = float(row.get("total_assets", row.get("net_cash_power", cash)))

        ret, pos = self.ctx.position_list_query(trd_env=self.env)
        if ret != 0:
            raise RuntimeError(f"position_list_query failed: {pos}")
        positions: dict[str, Position] = {}
        for _, r in pos.iterrows():
            code = str(r["code"])
            qty = float(r.get("qty", 0.0))
            avg_price = float(r.get("cost_price", r.get("average_cost", 0.0)))
            if qty > 0:
                positions[code] = Position(code, qty, avg_price)
        return AccountState(cash=cash, equity=equity, positions=positions)

    def _normalize_us_price(self, price: float) -> float:
        if price >= 1:
            return round(price, 2)
        return round(price, 4)

    def place_order(self, order: OrderPlan) -> dict:  # pragma: no cover
        OrderType = self._sdk["OrderType"]
        TrdSide = self._sdk["TrdSide"]

        side = TrdSide.BUY if order.side == Side.BUY else TrdSide.SELL
        price = self._normalize_us_price(float(order.limit_price))
        qty = float(order.qty)

        ret, data = self.ctx.place_order(
            price=price,
            qty=qty,
            code=order.symbol,
            trd_side=side,
            order_type=OrderType.NORMAL,
            trd_env=self.env,
        )

        return {
            "ok": ret == 0,
            "price": price,
            "qty": qty,
            "raw": data.to_dict() if hasattr(data, "to_dict") else str(data),
        }





