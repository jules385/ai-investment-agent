# A股AI投研系统 v0.4.0

基于 Codex 多智能体架构的 A 股二级市场投资研究系统。四个领域分析师并行工作，由首席分析师协调，输出结构化研报 → Obsidian 知识库。

---

## 快速开始

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 确认 .mcp.json 指向当前 Python 和项目路径

# 进行一次投研分析（在 Codex 中）
/analyze-initial 002463 沪电股份

# 生成 A 股投研日报
/analyze-daily

# 分析完成后，更新 Obsidian 知识库
python tools/update-workspace.py

# 或直接入库（支持外部研报）
python tools/archive-to-vault.py <报告路径> <代码>-<名称> <行业名>
```

---

## 架构

```
用户 → /analyze-xxx 命令
    ↓
首席分析师 (analyst-chief)
    ├── 基本面分析师 → 财务/估值/产业链
    ├── 筹码流向分析师 → 主力/北向/融资/龙虎榜
    ├── 技术面分析师 → 多周期 MACD/RSI/KDJ/布林
    └── 情绪面分析师 → 舆情/资金情绪/散户逆向
    ↓
4个QA分析师交叉验证
    ↓
首席合成报告 → reports/stocks/{代码}-{名称}/{周期}/
    ↓
入库 Obsidian: tools/archive-to-vault.py
    → obsidian-vault/行业知识库/{行业}.md
    → obsidian-vault/个股逻辑/{代码}-{名称}/基本面.md
    → obsidian-vault/个股逻辑/{代码}-{名称}/技术面.md
    → obsidian-vault/个股逻辑/{代码}-{名称}/筹码面.md
    → obsidian-vault/个股逻辑/{代码}-{名称}/情绪面.md
    → obsidian-vault/个股逻辑/{代码}-{名称}/投资决策.md
    → obsidian-vault/个股逻辑/{代码}-{名称}/原始报告/ (reports md 原文副本)
    → obsidian-vault/跟踪面板/{代码}-{名称}.md
    → obsidian-vault/组合管理/白名单.md (研究记录追加)
```

---

## 目录结构

```
ai-investment-agent/
├── skills/analysts/       ← AI分析师 SKILL.md（核心）
│   ├── analyst-chief/        首席分析师（编排器，不调MCP）
│   ├── analyst-fundamental/  基本面分析师（5步法）
│   ├── analyst-chip-flow/    筹码面分析师（5步法）
│   ├── analyst-technical/    技术面分析师（5周期×13指标）
│   ├── analyst-sentiment/    情绪面分析师（温度计模型）
│   ├── analyst-data-qa/      数据QA（交叉验证）
│   ├── analyst-portfolio-manager/ 组合管理员
│   ├── analyst-beautifier/   报告美化（md→html）
│   ├── analyst-archive/      研报入库
│   └── analyst-daily/        A股投研日报
│
├── commands/              ← Codex 斜杠命令
│   ├── analyze-initial.md    /analyze-initial 初次覆盖
│   ├── analyze-weekly.md     /analyze-weekly 周度跟踪
│   ├── analyze-monthly.md    /analyze-monthly 月度跟踪
│   ├── analyze-quarterly.md  /analyze-quarterly 季度跟踪
│   ├── analyze-annual.md     /analyze-annual 年度跟踪
│   ├── analyze-daily.md      /analyze-daily 日报
│   ├── analyze-portfolio-weekly.md 批量周度
│   ├── archive-research.md   /archive-research 外部研报入库
│   ├── beautify-report.md    /beautify-report 生成HTML
│   └── help.md               /help 命令速查
│
├── mcp-servers/           ← MCP数据服务器
│   ├── finance-data/        基本面+资金面（East Money）
│   ├── tech-analysis/       技术指标（MACD/RSI/KDJ/布林/形态）
│   ├── official-announcement/ 公告与监管新闻
│   ├── macro-policy/        宏观政策新闻
│   ├── market-news/         市场新闻
│   └── industry-data/       行业与产业链新闻
│
├── knowledge/             ← 研究方法论 & 工作流设计
│   ├── 增长逻辑分析方法手册.md
│   └── workflows/           各分析师工作流详细设计
│
├── tools/                 ← 工具脚本
│   ├── update-workspace.py  🔑 一键解析+同步 vault
│   ├── archive-to-vault.py  🔑 入库管道（Codex分类→Python入库→本地校验）
│   ├── daily_collect.py      日报证据池生成
│   ├── daily_score.py        日报证据评分
│   ├── daily_report.py       日报Markdown生成
│   ├── daily_to_vault.py     日报入库Obsidian
│   ├── sync-to-vault.py     Dataview 数据同步（由上面两个脚本调用）
│   ├── md-to-html.py        Markdown→HTML报告
│   └── self-test.py         MCP + Skills 全链路自测
│
├── web/api/               ← 研报解析模块（无Flask依赖）
│   ├── parser.py            AI提取核心（DeepSeek/Anthropic）+ 本地回退 + 章节定位
│   └── report_parser.py     解析编排层（分子报告定向提取）
│
├── obsidian-vault/        ← Obsidian 工作区（用Obsidian打开此文件夹）
│   ├── 行业知识库/         产业链/市场空间/竞争格局/政策
│   ├── 个股逻辑/           多空逻辑链/关键假设/跟踪指标/事件
│   ├── 组合管理/           白名单/持仓名单/黑名单 + 研究记录
│   └── _index.md           总面板（Dataview 渲染）
│
├── reports/               ← 研报输出
│   ├── stocks/{代码}-{名称}/ 初次覆盖+周度+月度+季度+年度
│   ├── daily/{日期}/          日报 evidence + scoring + 日报.md
│   ├── workspace-data.json  AI解析后的结构化数据
│   ├── 白名单组合.md         用户手动维护
│   ├── 持仓组合.md           用户手动维护
│   └── 黑名单组合.md         用户手动维护
│
├── docs/                  ← 文档
│   ├── 使用手册.md
│   └── 持续迭代开发文档.md
│
├── .codex/                ← Codex 本地配置
├── .mcp.json              ← Codex MCP 配置
├── .mcp.json.template     ← MCP配置模板
├── .env                   ← API Key（DEEPSEEK_API_KEY / ANTHROPIC_API_KEY）
├── requirements.txt
└── README.md
```

---

## 核心脚本

| 脚本 | 用途 | 是否依赖外部AI |
|------|------|:--:|
| `python tools/archive-to-vault.py <路径> <代码>-<名称> <行业>` | Codex分类计划驱动的研报入库（推荐） | ❌ |
| `python tools/daily_collect.py --date YYYY-MM-DD` | 生成日报证据池 | ❌ |
| `python tools/daily_score.py reports/daily/YYYY-MM-DD/evidence.json` | 证据重要性基础评分 | ❌ |
| `python tools/daily_report.py reports/daily/YYYY-MM-DD/scoring.json` | 生成日报 Markdown | ❌ |
| `python tools/daily_to_vault.py reports/daily/YYYY-MM-DD/日报.md` | 日报入库 Obsidian | ❌ |
| `python tools/update-workspace.py` | 全量解析 reports/ → vault（旧解析兼容路径） | 可选 |
| `python tools/sync-to-vault.py` | 仅同步 workspace-data.json → vault | ❌ |
| `python tools/md-to-html.py <代码>-<名称>` | 生成 HTML 报告 | ❌ |
| `python tools/self-test.py` | 全链路自测（MCP + Skills） | ❌ |

---

## API Key 配置

当前本地 Codex + Obsidian 入库流程不依赖外部 LLM API。若保留旧解析模块，可在 `.env` 中设置：
```
```

旧解析模块优先级：ANTHROPIC_API_KEY > DEEPSEEK_API_KEY

---

## Obsidian 工作区

用 Obsidian 打开 `obsidian-vault/` 文件夹，安装 Dataview 插件。

### 面板说明

| 文件 | 面板内容 |
|------|---------|
| `_index.md` | 全部股票概览（信号方向、评分、跟踪指标数） |
| `_行业知识库.md` | 行业列表（产业链节点、TAM覆盖、财务基准覆盖） |
| `_跟踪面板.md` | 跟踪指标与事件覆盖情况 |

### 知识入库两种方式

**方式1 — Python管道（推荐，每次投研后运行）：**
```bash
python tools/archive-to-vault.py reports/stocks/002463-沪电股份 002463-沪电股份 "AI服务器PCB" --emit-plan reports/archive-plan-002463.json
# Codex 填写 plan 后：
python tools/archive-to-vault.py reports/stocks/002463-沪电股份 002463-沪电股份 "AI服务器PCB" --plan reports/archive-plan-002463.json
```

入库原则：初次覆盖建立四面基线；后续跟踪默认只进入投资决策日志，只有重大逻辑变化才更新四面或行业知识库。

**方式2 — AI Agent（交互式，适合手动入库）：**
```
/archive-research [文件路径或粘贴文本]
```

---

## 多智能体工作流

### 日报流程
```
Step 0: 确定时间窗口（上一日00:00 ~ 当日23:59:59）
Step 1: 新闻/公告/政策 MCP 或官方源/可信新闻源采集证据
Step 2: 写入 reports/daily/YYYY-MM-DD/evidence.json
Step 3: 代码评分 + AI重要性判断 + 影响链推理
Step 4: 生成 reports/daily/YYYY-MM-DD/日报.md
Step 5: 入库 obsidian-vault/日报/YYYY-MM-DD.md
Step 6: 重大事项只写入跟踪面板，不直接改写四面逻辑
```

日报是新闻整理，不默认调用 finance-data、tech-analysis 等行情/资金/技术指标 MCP。

### 初次覆盖流程
```
Step 0: 判断周期（初次覆盖 = 深度模式）
Step 1: 创建目录 + 并行启动4个分析师
Step 2a: 验证文件完整性
Step 2b: 强制QA（4个QA并行交叉验证）
Step 3: 首席合成报告 → 写入磁盘
Step 4: 入库Obsidian + 更新组合管理
完成检查表: 7/7
```

### 各周期模式

| 周期 | 模式 | 参与分析师 |
|------|------|-----------|
| 初次覆盖 | 深度（5步法） | 全4个 |
| 周度 | 快速扫描 | 基本面(边际) + 筹码(快速) + 技术(标准) + 情绪(速览) |
| 月度 | 趋势确认 | 全4个（加趋势提炼） |
| 季度 | 深度（财务核心） | 基本面(三表联动) + 其余简略 |
| 年度 | 战略复盘 | 全4个（全年回顾+行业重评） |

---

## MCP 工具一览

### finance-data（15个工具）
`get_financial_indicators` `get_financial_history` `get_valuation` `get_historical_data` `get_fund_flow` `get_shareholders` `get_margin_data` `get_hsgt_holdings` `get_lhb_details` `get_chip_distribution`

### tech-analysis（10个工具）
`compute_ma` `compute_macd` `compute_rsi` `compute_kdj` `compute_bollinger` `compute_atr` `compute_volume` `detect_patterns` `support_resistance` `technical_score`

### 日报新闻类 MCP

`official-announcement`: `search_company_announcements` `search_exchange_announcements` `get_announcement_detail` `extract_announcement_entities`

`macro-policy`: `get_policy_news` `get_macro_calendar` `get_policy_detail`

`market-news`: `search_news` `get_hot_news` `get_news_detail`

`industry-data`: `get_industry_news` `get_industry_chain_events` `get_industry_detail`

---

## Codex 使用模式

本项目已完全切换到 Codex 开发与使用。项目入口为 `AGENTS.md`，运行配置以 `.mcp.json`、`skills/analysts/`、`commands/` 和 `tools/` 为准。
