from __future__ import annotations

import argparse
import socket
from .audit import AuditLogger
from .brokers.mock import MockBroker
from .brokers.moomoo_broker import MoomooBroker
from .config import load_config
from .data.sample_data import generate_prices
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/example.toml")
    parser.add_argument("--dry-run", action="store_true", help="generate orders but do not submit")
    parser.add_argument("--execute", action="store_true", help="submit approved orders to broker")
    parser.add_argument("--offline-dry-run", action="store_true", help="when OpenD is unavailable, fall back to mock broker in dry-run mode")
    parser.add_argument("--audit-log", default="logs/audit.log")
    args = parser.parse_args()

    cfg = load_config(args.config)
    offline_fallback = args.dry_run and not args.execute and args.offline_dry_run
    broker = build_broker(cfg, offline_fallback=offline_fallback)
    strategy = MovingAverageCrossStrategy(cfg.strategy.fast_window, cfg.strategy.slow_window)
    risk = RiskEngine(cfg.risk)
    audit = AuditLogger(args.audit_log)

    account = broker.get_account_state()
    print(f"Account equity={account.equity:.2f} cash={account.cash:.2f}")

    for symbol in cfg.strategy.symbols:
        prices = generate_prices(symbol)
        signal = strategy.generate_signal(prices)
        if signal is None:
            print(f"{symbol}: no signal")
            continue
        decision = risk.evaluate(signal, account)
        audit.write("risk_decision", {"signal": signal, "decision": decision})
        print(f"{symbol}: {signal.side.value} conf={signal.confidence:.2f} approved={decision.approved} reason={decision.reason}")
        if decision.approved and decision.order:
            if args.execute and not args.dry_run:
                result = broker.place_order(decision.order)
                audit.write("order_submitted", {"order": decision.order, "result": result})
                print(f"submitted: {result}")
            else:
                audit.write("order_dry_run", {"order": decision.order})
                print(f"dry-run order: {decision.order}")

    close = getattr(broker, "close", None)
    if callable(close):
        close()


if __name__ == "__main__":
    main()
