# ai_moomoo_trader

AI 驱动投资助手 MVP。当前版本先做技术验证：策略生成信号、风控过滤、生成订单计划、dry-run/execute 分离、审计日志，并预留 moomoo OpenD 模拟交易接口。

## 安装

```bash
cd ai_moomoo_trader
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q
```

如需连接 moomoo/OpenD：

```bash
pip install moomoo-api
```

## 快速离线测试

把 `config/example.toml` 中 broker 改为：

```toml
[broker]
type = "mock"
```

运行：

```bash
PYTHONPATH=src python -m ai_moomoo_trader.cli --config config/example.toml --dry-run
```

## moomoo/OpenD dry-run

先启动 moomoo OpenD，登录账户，并确认端口是 11111。配置：

```toml
[broker]
type = "moomoo"
env = "SIMULATE"
host = "127.0.0.1"
port = 11111
market = "US"
```

运行：

```bash
PYTHONPATH=src python -m ai_moomoo_trader.cli --config config/example.toml --dry-run
```

如果你只是想在 moomoo 配置下先跑程序，但 OpenD 还没开，可以用离线降级：

```bash
PYTHONPATH=src python -m ai_moomoo_trader.cli --config config/example.toml --dry-run --offline-dry-run
```

## 真实提交到模拟盘

只在确认 OpenD、账户、模拟环境无误后使用：

```bash
PYTHONPATH=src python -m ai_moomoo_trader.cli --config config/example.toml --execute
```

安全设计：默认不会提交订单；只有 `--execute` 且没有 `--dry-run` 时才调用 broker.place_order。
