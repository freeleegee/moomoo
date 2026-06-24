# ai_moomoo_trader

Risk-first AI-assisted moomoo paper trading MVP.

当前版本 v0.4 做了五件事：

1. 默认配置脱敏：`example.toml` 使用 mock/sample，真实配置放 `config/local.toml`。
2. 真实行情入口：支持通过 moomoo OpenD 拉取日 K 线，不再强制使用 sample_data。
3. 扩大股票池：默认覆盖 AI/科技核心股票池。
4. 风控增强：最小置信度、现金保留、单票仓位、最大持仓数、日亏损、止损距离仓位计算。
5. AI 评分骨架：先用本地确定性特征生成 AI-like score，后续可替换成 LLM/RAG 新闻因子。
6. 回测入口：支持对当前股票池跑简单 long-only 回测。

> 重要：这仍然是研究/模拟盘项目，不是实盘盈利保证。

## Mac 安装

```bash
cd moomoo
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e '.[test]'
python3 -m pip install moomoo-api
pytest -q
```

## 离线 dry-run

不需要 OpenD：

```bash
PYTHONPATH=src python3 -m ai_moomoo_trader.cli --config config/example.toml --dry-run --offline-dry-run
```

## 回测

```bash
PYTHONPATH=src python3 -m ai_moomoo_trader.cli --config config/example.toml --backtest
```

## moomoo 模拟盘配置

复制模板：

```bash
cp config/local.example.toml config/local.toml
```

确认 Mac 上已经打开并登录 moomoo OpenD，端口为 `11111`。

`config/local.toml`：

```toml
[broker]
type = "moomoo"
env = "SIMULATE"
host = "127.0.0.1"
port = 11111
market = "US"

[data]
source = "moomoo"
```

连接 OpenD 但不下单：

```bash
PYTHONPATH=src python3 -m ai_moomoo_trader.cli --config config/local.toml --dry-run
```

提交到 moomoo 模拟盘：

```bash
PYTHONPATH=src python3 -m ai_moomoo_trader.cli --config config/local.toml --execute
```

## Git 安全

不要提交这些文件：

```text
.env*
logs/
data/
config/local.toml
.venv/
.pytest_cache/
*.egg-info/
__pycache__/
```

## 下一步

v0.5 建议加入：

- 真实订单状态查询和成交确认
- 每日净值曲线
- 更严肃的回测统计：夏普、胜率、盈亏比、交易成本
- 新闻/RAG/LLM 研究 Agent
