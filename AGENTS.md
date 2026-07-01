# A股AI投研系统 v0.4.1

基于 Codex 多智能体架构的 A 股二级市场投资研究系统。四个领域分析师并行工作，由首席分析师协调，输出研究报告，并沉淀到 Obsidian 知识库。

---

## 快速开始

```bash
pip install -r requirements.txt
copy .mcp.json.template .mcp.json
python tools/self-test.py
```

把 `.mcp.json` 中的 `{{PYTHON_PATH}}` 和 `{{REPO_PATH}}` 替换为本机 Python 路径和项目路径。

```text
/analyze-initial 002463 沪电股份
/analyze-daily
```

研究完成后，使用当前入库主线：

```bash
python tools/archive-to-vault.py <报告路径> <代码>-<名称> <行业名> --emit-plan reports/archive-plan-<代码>.json
# Codex 填写 plan 后：
python tools/archive-to-vault.py <报告路径> <代码>-<名称> <行业名> --plan reports/archive-plan-<代码>.json
```

---

## 架构

```text
用户 -> /analyze-xxx 命令
    -> analyst-chief 首席分析师
       -> analyst-fundamental 基本面
       -> analyst-chip-flow 筹码面
       -> analyst-technical 技术面
       -> analyst-sentiment 情绪面
    -> analyst-data-qa 交叉验证
    -> 首席合成报告 -> reports/
    -> tools/archive-to-vault.py
    -> obsidian-vault/
```

入库到：

```text
obsidian-vault/行业知识库/<行业>.md
obsidian-vault/个股逻辑/<代码-名称>/_index.md
obsidian-vault/个股逻辑/<代码-名称>/基本面.md
obsidian-vault/个股逻辑/<代码-名称>/技术面.md
obsidian-vault/个股逻辑/<代码-名称>/筹码面.md
obsidian-vault/个股逻辑/<代码-名称>/情绪面.md
obsidian-vault/个股逻辑/<代码-名称>/投资决策.md
obsidian-vault/个股逻辑/<代码-名称>/原始报告/
obsidian-vault/跟踪面板/<代码-名称>.md
obsidian-vault/组合管理/白名单.md
```

---

## 目录结构

```text
ai-investment-agent/
├── skills/analysts/
│   ├── analyst-chief/
│   ├── analyst-fundamental/
│   ├── analyst-chip-flow/
│   ├── analyst-technical/
│   ├── analyst-sentiment/
│   ├── analyst-data-qa/
│   ├── analyst-portfolio-manager/
│   ├── analyst-beautifier/
│   ├── analyst-archive/
│   └── analyst-daily/
├── commands/
│   ├── analyze-initial.md
│   ├── analyze-weekly.md
│   ├── analyze-monthly.md
│   ├── analyze-quarterly.md
│   ├── analyze-annual.md
│   ├── analyze-daily.md
│   ├── analyze-portfolio-weekly.md
│   ├── archive-research.md
│   ├── beautify-report.md
│   └── help.md
├── mcp-servers/
│   ├── finance-data/
│   ├── tech-analysis/
│   ├── official-announcement/
│   ├── macro-policy/
│   ├── market-news/
│   └── industry-data/
├── knowledge/
├── tools/
│   ├── archive-to-vault.py
│   ├── daily_collect.py
│   ├── daily_score.py
│   ├── daily_report.py
│   ├── daily_to_vault.py
│   ├── md-to-html.py
│   └── self-test.py
├── web/api/
├── obsidian-vault/
├── reports/
└── docs/
```

---

## 核心脚本

| 脚本 | 用途 | 是否依赖外部 AI |
|---|---|:--:|
| `python tools/archive-to-vault.py <路径> <代码>-<名称> <行业> --emit-plan <plan>` | 生成入库分类计划模板 | 否 |
| `python tools/archive-to-vault.py <路径> <代码>-<名称> <行业> --plan <plan>` | Codex 分类计划驱动的研报入库 | 否 |
| `python tools/daily_collect.py --date YYYY-MM-DD` | 接收 MCP/web/manual 证据并落盘 | 否 |
| `python tools/daily_score.py reports/daily/YYYY-MM-DD/evidence.json` | 日报证据基础评分 | 否 |
| `python tools/daily_report.py reports/daily/YYYY-MM-DD/scoring.json` | 生成日报 Markdown | 否 |
| `python tools/daily_to_vault.py reports/daily/YYYY-MM-DD/日报.md` | 日报入库 Obsidian | 否 |
| `python tools/md-to-html.py <代码>-<名称>` | 生成 HTML 报告 | 否 |
| `python tools/self-test.py` | 依赖、MCP、Skill、命令、工具自测 | 否 |

---

## Obsidian 工作区

用 Obsidian 打开 `obsidian-vault/` 文件夹，建议安装 Dataview 插件。

| 文件 | 面板内容 |
|---|---|
| `_index.md` | 全部股票概览 |
| `_行业知识库.md` | 行业列表、产业链、TAM、财务基准覆盖 |
| `_跟踪面板.md` | 跟踪指标与事件覆盖情况 |

入库原则：初次覆盖建立四面基线；后续跟踪默认只进入投资决策日志；只有重大逻辑变化才更新四面或行业知识库；原始报告只做 Python 原文复制。

---

## 日报流程

```text
Step 0: 确定时间窗口，覆盖分析指令发出当天以及上一天
Step 1: Codex 调用新闻/公告/政策 MCP 或可信 web 来源采集证据
Step 2: 写入 reports/daily/YYYY-MM-DD/evidence.json
Step 3: 代码评分 + Codex 重要性判断 + 影响链推理
Step 4: 生成 reports/daily/YYYY-MM-DD/日报.md
Step 5: 入库 obsidian-vault/日报/YYYY-MM-DD.md
Step 6: 重大事项写入跟踪面板，不直接改写四面逻辑
```

日报是新闻整理，不默认调用行情、资金、估值或技术指标 MCP。

---

## 初次覆盖流程

```text
Step 0: 判断周期，初次覆盖采用深度模式
Step 1: 创建目录，并行启动 4 个分析师
Step 2: 验证文件完整性，执行数据 QA
Step 3: 首席合成报告并写入磁盘
Step 4: 入库 Obsidian，更新组合管理研究记录
```

| 周期 | 模式 | 参与分析师 |
|---|---|---|
| 初次覆盖 | 深度 | 全 4 个 |
| 周度 | 快速扫描 | 全 4 个，偏边际变化 |
| 月度 | 趋势确认 | 全 4 个 |
| 季度 | 财务核心 | 基本面深度，其余简略 |
| 年度 | 战略复盘 | 全 4 个 |

---

## MCP 工具一览

### finance-data（10 个工具）

`get_financial_indicators` `get_financial_history` `get_valuation` `get_historical_data` `get_fund_flow` `get_shareholders` `get_margin_data` `get_hsgt_holdings` `get_lhb_details` `get_chip_distribution`

### tech-analysis（10 个工具）

`compute_ma` `compute_macd` `compute_rsi` `compute_kdj` `compute_bollinger` `compute_atr` `compute_volume` `detect_patterns` `support_resistance` `technical_score`

### 日报新闻类 MCP

- `official-announcement`：`search_company_announcements` `search_exchange_announcements` `get_announcement_detail` `extract_announcement_entities`
- `macro-policy`：`get_policy_news` `get_macro_calendar` `get_policy_detail`
- `market-news`：`search_news` `get_hot_news` `get_news_detail`
- `industry-data`：`get_industry_news` `get_industry_chain_events` `get_industry_detail`

---

## Codex 使用模式

本项目已完全切换到 Codex 开发与使用。项目入口为 `AGENTS.md`，运行配置以 `.mcp.json`、`skills/analysts/`、`commands/` 和 `tools/` 为准。
