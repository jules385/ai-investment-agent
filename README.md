# A股AI投研系统 · AI-Powered A-Share Investment Research

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.0.0-blue.svg)](VERSION)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](requirements.txt)

> **English** | [中文](#中文)

A Claude Code multi-agent system for Chinese A-share equity research. Four domain analysts work in parallel, coordinated by a Chief Analyst, producing structured initial-coverage and ongoing-tracking reports.

Built on: **Claude Code Subagent orchestration** · **MCP protocol** · **AKShare (1000+ free APIs)** · **DeepSeek V4 Pro**

---

## 中文

基于 Claude Code 多智能体架构的 A 股二级市场投资研究系统。四个领域分析师并行工作，由首席分析师协调，输出结构化的初次覆盖报告和持续跟踪报告。

## 架构

```
用户触发分析
      │
      ▼
┌─────────────┐
│ 首席分析师    │ ← 编排协调、矛盾检测、投资决策
│ analyst-chief │
└──┬──┬──┬──┘
   │  │  │  └──────────┐
   ▼  ▼  ▼             ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│基本面 │ │筹码面 │ │技术面 │ │情绪面 │
│分析师 │ │分析师 │ │分析师 │ │分析师 │
└──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
   │        │        │        │
   ▼        ▼        ▼        ▼
┌──────────────────────────────────┐
│         MCP 数据服务层            │
│  finance-data │ tech-analysis    │
│  同花顺/East Money │ ta 指标库    │
└──────────────────────────────────┘
```

**四个分析维度：**
- **基本面分析师** — 行业赛道 + 增长逻辑（供给端/需求端/竞争格局）+ 财务交叉验证 + 估值判断
- **筹码面分析师** — 股东结构 + 主力资金流向 + 北向/融资融券 + 龙虎榜 + 筹码分布
- **技术面分析师** — 多周期趋势定位 + MACD/RSI/KDJ/布林/量价/K线形态 + 买卖信号 + 价格锚点
- **情绪面分析师** — 市场情绪 + 个股舆情 + 散户行为监测 → 情绪温度计 (0-100)

**辅助角色：**
- **数据分析师** — 数据质量检查，自动补充缺失数据，生成缺口清单
- **AI 美化师** — Markdown→精美 HTML 报告

## 快速开始

### 环境要求

- Python 3.11+
- Claude Code（桌面版/CLI/IDE 插件）
- DeepSeek API Key（或 Anthropic API Key）

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/jules385/ai-investment-agent.git
cd ai-investment-agent

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 运行安装脚本
python install.py
```

### 配置

1. **配置 API Key**：编辑 `~/.claude/settings.json`，参考 `workspace-template/.claude/settings.json.template`
2. **创建工作区**：复制 `workspace-template/` 到你的工作目录（如 `~/ai-investment/`）
3. **添加白名单**：在 `reports/白名单.md` 中添加你想覆盖的标的

### 使用

```bash
# 启动 Claude Code，执行：
/analyze-initial 002414 高德红外    # 初次覆盖
/analyze-weekly                    # 周度跟踪（遍历白名单）
/analyze-monthly  002414           # 月度跟踪（指定标的）
/analyze-quarterly                 # 季度跟踪
/beautify-report 002414-高德红外    # 生成 HTML 报告
```

## 目录结构

```
ai-investment-agent/
├── README.md
├── install.py                 ← 一键安装
├── requirements.txt
│
├── skills/analysts/           ← 7 个 AI 角色 Skill
│   ├── analyst-chief/         组
│   ├── analyst-fundamental/   协
│   ├── analyst-chip-flow/     分
│   ├── analyst-technical/     析
│   ├── analyst-sentiment/     师
│   ├── analyst-data-qa/       QA
│   └── analyst-beautifier/    美化
│
├── commands/                  ← 5 条斜杠命令
├── mcp-servers/               ← 2 个 MCP 数据服务
│   ├── finance-data/         基本面 + 资金流 + 股东
│   └── tech-analysis/        技术指标 (ta 库)
│
├── knowledge/                 ← 方法论手册 + 工作流设计
├── tools/                     ← md-to-html 等工具
├── docs/                      ← 使用手册 + 项目介绍
│
└── workspace-template/        ← 用户工作区模板
    ├── reports/              研报 + 白名单 + 决策日志
    └── .claude/              settings 模板
```

## 分析周期

| 周期 | 基本面 | 筹码面 | 技术面 | 情绪面 |
|------|--------|--------|--------|--------|
| 初次覆盖 | 深度全流程 | 深度五步 | 深度全指标 | 深度温度计 |
| 周度跟踪 | 边际监控 | 快速扫描 | 日线+60min | 快速扫描 |
| 月度跟踪 | 边际+财务 | 深度五步 | 中期支撑阻力 | 深度温度计 |
| 季度跟踪 | 深度全流程 | 深度五步 | 深度全指标 | 深度温度计 |

## 免责声明

**本系统仅供学习研究参考，不构成任何投资建议。** AI 生成的分析结果可能存在错误或遗漏，使用者应独立判断并承担投资风险。投资有风险，入市需谨慎。

## License

MIT License — 详见 [LICENSE](LICENSE)

---

## English

### What is this?

A multi-agent investment research system running on Claude Code. It simulates a buy-side analyst team:

- **4 Domain Analysts** — Fundamental, Chip-Flow (capital), Technical, Sentiment — each runs as an independent Claude Subagent
- **Chief Analyst** — Orchestrates the 4 analysts in parallel, detects contradictions, applies regime-adaptive weighting, outputs final investment decision
- **Data QA Analyst** — Scans every claim in the report for data sufficiency and causal chain completeness
- **Report Beautifier** — Converts Markdown reports to styled HTML

### Architecture

```
User triggers analysis
        │
        ▼
┌──────────────────┐
│  Chief Analyst    │ ← Orchestration, contradiction detection, decision
│  analyst-chief    │
└──┬───┬───┬───┘
   │   │   │
   ▼   ▼   ▼   ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Fundam.│ │Chip  │ │Tech. │ │Sentim.│
│Analyst│ │Flow  │ │Analyst│ │Analyst│
└──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
   │        │        │        │
   ▼        ▼        ▼        ▼
┌──────────────────────────────────┐
│         MCP Data Layer            │
│  finance-data │ tech-analysis     │
└──────────────────────────────────┘
```

### Quick Start

```bash
git clone https://github.com/jules385/ai-investment-agent.git
cd ai-investment-agent
pip install -r requirements.txt
python install.py
```

Then configure your API key in `~/.claude/settings.json` and start analyzing:

```
/analyze-initial 002414         # Initial coverage
/analyze-weekly                 # Weekly tracking
/beautify-report 002414-XXXX    # Generate HTML report
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Engine | Claude Code + DeepSeek V4 Pro (Subagent orchestration) |
| Protocol | MCP (Model Context Protocol) — stdio transport |
| Data | AKShare (1000+ free A-share APIs) + East Money + THS |
| Tech Indicators | `ta` library (MACD/RSI/Bollinger/KDJ/ATR/patterns) |
| Language | Python 3.10+ |
| Output | Markdown (archive) + HTML (presentation) |

### Key Design Decisions

- **Four-dimensional cross-validation**: Each analyst uses entirely different data sources and frameworks. Fundamental looks at "is it worth it?", sentiment looks at "are people fearful?", chip-flow looks at "who's buying?", technical looks at "when to buy?"
- **Causal chain enforcement**: Qualitative conclusions must show ≥4-step causal reasoning with data at each step. No "data → conclusion" jumps.
- **Standardized signal interface**: Every analyst outputs a YAML block with `direction`, `strength`, `confidence`, `score`, `key_evidence`, `red_flags` — making cross-dimensional synthesis mechanical rather than subjective.
- **Period-adaptive depth**: Initial coverage runs full deep analysis; weekly tracking runs quick scans; quarterly re-runs full deep analysis with financial focus.

### Disclaimer

**This system is for educational and research purposes only. It does NOT constitute investment advice.** AI-generated analysis may contain errors or omissions. Users should exercise independent judgment and assume all investment risks.

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Contributions welcome — new analyst roles, MCP tools, data sources, or documentation improvements.
