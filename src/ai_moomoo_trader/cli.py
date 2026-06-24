from __future__ import annotations

import argparse
import socket
from .ai import HeuristicAIScorer
from .audit import AuditLogger
from .backtest import run_long_only_backtest
from .brokers.mock import MockBroker
from .brokers.moomoo_broker import MoomooBroker
from .config import load_config
from .data.market_data import MoomooMarketData, SampleMarketData
from .position_manager import PositionManager
from .risk import RiskEngine
from .strategies.moving_average import MovingAverageCrossStrategy


def _is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def build_broker(cfg, *, offline_fallback: bool = False):
    if cfg.broker.type == "mock":
        return MockBroker(cfg.account.initial_cash)
    if cfg.broker.type == "moomoo":
        if not _is_port_open(cfg.broker.host, cfg.broker.port):
            message = (
                f"moomoo OpenD is not reachable at {cfg.broker.host}:{cfg.broker.port}. "
                "Start OpenD and log in, or use broker.type='mock'."
            )
            if offline_fallback:
                print(f"WARNING: {message} Falling back to MockBroker for offline dry-run.")
                return MockBroker(cfg.account.initial_cash)
            raise RuntimeError(message)
        return MoomooBroker(cfg.broker.host, cfg.broker.port, cfg.broker.env, cfg.broker.market)
    raise ValueError(f"unknown broker type: {cfg.broker.type}")


def build_market_data(cfg, *, offline_fallback: bool = False):
    if cfg.data.source == "sample":
        return SampleMarketData(days=cfg.strategy.lookback_days)
    if cfg.data.source == "moomoo":
        if not _is_port_open(cfg.broker.host, cfg.broker.port):
            message = f"moomoo OpenD quote service is not reachable at {cfg.broker.host}:{cfg.broker.port}."
            if offline_fallback:
                print(f"WARNING: {message} Falling back to sample data for offline dry-run.")
                return SampleMarketData(days=cfg.strategy.lookback_days)
            raise RuntimeError(message)
        return MoomooMarketData(cfg.broker.host, cfg.broker.port)
    raise ValueError(f"unknown data source: {cfg.data.source}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/example.toml")
    parser.add_argument("--dry-run", action="store_true", help="generate orders but do not submit")
    parser.add_argument("--execute", action="store_true", help="submit approved orders to broker")
    parser.add_argument("--backtest", action="store_true", help="run simple long-only backtest instead of trading loop")
    parser.add_argument("--offline-dry-run", action="store_true", help="when OpenD is unavailable, fall back to mock/sample providers in dry-run mode")
    parser.add_argument("--audit-log", default="logs/audit.log")
    parser.add_argument("--position-state", default="logs/positions.json")
    args = parser.parse_args()

    cfg = load_config(args.config)
    offline_fallback = args.dry_run and not args.execute and args.offline_dry_run
    market_data = build_market_data(cfg, offline_fallback=offline_fallback)
    strategy = MovingAverageCrossStrategy(cfg.strategy.fast_window, cfg.strategy.slow_window)
    scorer = HeuristicAIScorer()

    if args.backtest:
        for symbol in cfg.strategy.symbols:
            prices = market_data.get_daily_bars(symbol, cfg.strategy.lookback_days)
            result = run_long_only_backtest(symbol, prices, cfg.strategy.fast_window, cfg.strategy.slow_window)
            print(
                f"{symbol}: trades={result.trades} "
                f"strategy_return={result.total_return:.2%} "
                f"buy_hold={result.buy_and_hold_return:.2%} "
                f"max_drawdown={result.max_drawdown:.2%}"
            )
        market_data.close()
        return

    broker = build_broker(cfg, offline_fallback=offline_fallback)
    risk = RiskEngine(cfg.risk)
    audit = AuditLogger(args.audit_log)
    positions = PositionManager(args.position_state)

    def handle_signal(signal, ai_payload=None):
        decision = risk.evaluate(signal, account)
        audit.write("risk_decision", {"signal": signal, "ai_score": ai_payload, "decision": decision})
        print(f"{signal.symbol}: {signal.side.value} conf={signal.confidence:.2f} approved={decision.approved} reason={decision.reason}")
        if decision.approved and decision.order:
            if args.execute and not args.dry_run:
                result = broker.place_order(decision.order)
                audit.write("order_submitted", {"order": decision.order, "result": result})
                print(f"submitted: {result}")
            else:
                audit.write("order_dry_run", {"order": decision.order})
                print(f"dry-run order: {decision.order}")

    account = broker.get_account_state()
    positions.sync(account)
    print(f"Account equity={account.equity:.2f} cash={account.cash:.2f}")

    for symbol in cfg.strategy.symbols:
        prices = market_data.get_daily_bars(symbol, cfg.strategy.lookback_days)
        current_price = float(prices.iloc[-1]["close"])

        snap = positions.snapshot(account, symbol, current_price)
        if snap is not None:
            holding = "unknown" if snap.holding_days is None else str(snap.holding_days)
            print(
                f"{symbol}: position qty={snap.qty:g} avg={snap.avg_price:.2f} "
                f"price={snap.current_price:.2f} pnl={snap.unrealized_pct:.2%} holding_days={holding}"
            )
            exit_signal = positions.exit_signal(
                account,
                symbol,
                current_price,
                stop_loss_pct=cfg.risk.stop_loss_pct,
                take_profit_pct=cfg.risk.take_profit_pct,
                max_holding_days=cfg.risk.max_holding_days,
            )
            if exit_signal is not None:
                handle_signal(exit_signal)
                continue

        ai = scorer.score(prices)
        print(f"{symbol}: ai_score={ai.final_score:.1f} ({ai.reason})")
        if ai.final_score < cfg.strategy.ai_score_min:
            audit.write("ai_rejected", {"symbol": symbol, "ai_score": ai.__dict__})
            print(f"{symbol}: skipped by AI score threshold {cfg.strategy.ai_score_min:.1f}")
            continue

        signal = strategy.generate_signal(prices, ai_score=ai.final_score)
        if signal is None:
            print(f"{symbol}: no signal")
            continue
        handle_signal(signal, ai.__dict__)

    for obj in (market_data, broker):
        close = getattr(obj, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    main()
