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

- Python 3.10+
- Claude Code（CLI / 桌面版 / IDE 插件）
- DeepSeek API Key 或 Anthropic API Key

### Claude Code CLI 用户（推荐，三步完成，Codex用户可自行适配）

```bash
# 1. 克隆 + 安装
git clone https://github.com/jules385/ai-investment-agent.git && cd ai-investment-agent
pip install -r requirements.txt && python install.py

# 2. 配置 API Key
# 编辑 ~/.claude/settings.json，模板见下方

# 3. 启动 Claude Code，直接使用

#注意：Codex用户安装完成后请输入以下提示词-"阅读 docs/CODEX适配指南.md，然后读取所有 skills/analysts/ 下的 SKILL.md 和 commands/ 下的命令文件，把它们全部改写为 Codex 原生格式，保存到新建的 codex-agents/ 和 codex-commands/ 目录"
claude
```

然后输入 `/analyze-initial 002414 高德红外` 即可开始第一次分析。

### 桌面版 / IDE 插件用户

```bash
git clone https://github.com/jules385/ai-investment-agent.git
cd ai-investment-agent
pip install -r requirements.txt
python install.py
```

### 配置 API Key

编辑 `~/.claude/settings.json`，参考模板：

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "sk-your-api-key",
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_MODEL": "deepseek-v4-pro"
  },
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch(domain:*)",
      "mcp__finance-data__*",
      "mcp__tech-analysis__*",
      "mcp__akshare__*"
    ]
  }
}
```

> 完整模板见 `workspace-template/.claude/settings.json.template`。用 DeepSeek 填 DeepSeek 的 Key，用 Anthropic 填 Anthropic 的 Key，两套都支持。

### 创建用户工作区

```bash
cp -r workspace-template ~/ai-investment
```

然后在 `~/ai-investment/reports/白名单组合.md` 中添加你的标的。

### 验证安装

```bash
# 检查 MCP Server 是否正常
python tools/self-test.py

# 预期输出：4/4 通过
```

### 开始使用

> 🔴 **尽可能使用斜杠命令**（`/analyze-initial`），不要输入自然语言。斜杠命令是 Claude Code 的确定性加载机制——只要命令文件存在，就一定会被加载。自然语言依赖 Skill 的触发词匹配，可能失败。

```bash
claude                                                    # CLI 用户启动

# 🔴 使用斜杠命令+股票名称或代码（仅支持A股）：
/analyze-initial                                          # 初次覆盖
/analyze-weekly                                           # 周度跟踪
/analyze-monthly                                          # 月度跟踪
/analyze-quarterly                                        # 季度跟踪
/analyze-annual                                           # 年度战略复盘
/analyze-portfolio-weekly（或者monthly等）                # 组合批量周度跟踪
/beautify-report                                          # 生成 HTML 报告
/help                                                     # 查看所有可用命令

# 自然语言也可用（备选，可能不稳定）：
# "对高德红外进行初次覆盖"
```

**首次使用验证**：输入 `/analyze-initial` 后，如果 Claude 的回复开头出现 `🔴 总分析师已激活`，说明一切正常。如果没出现 → 运行 `python install.py` 重装。

## 目录结构

```
ai-investment-agent/
├── README.md
├── install.py                 ← 一键安装
├── requirements.txt
│
├── skills/analysts/           ← 8 个 AI 角色 Skill
│   ├── analyst-chief/         编排
│   ├── analyst-fundamental/   基本面
│   ├── analyst-chip-flow/     筹码面
│   ├── analyst-technical/     技术面
│   ├── analyst-sentiment/     情绪面
│   ├── analyst-data-qa/       数据QA
│   ├── analyst-beautifier/    美化
│   └── analyst-portfolio-mgr/ 组合管理
│
├── commands/                  ← 7 条斜杠命令
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
| 周度跟踪 | 边际监控 | 快速扫描 | 日线+60min | 温度更新 |
| 月度跟踪 | 4周趋势提炼 | 趋势汇总 | 周线+月线 | 4周温度曲线 |
| 季度跟踪 | 三表联动分析 | 简略 | 简略 | 简略 |
| 年度跟踪 | 战略复盘+行业重评 | 全年回顾 | 全年信号审计 | 年度周期定位 |

## 常见问题

### 输入分析指令后，Chief 分析师没有按工作流执行

**症状**：输入 `/analyze-initial`，Claude 没有 spawn 4 个 Subagent，而是自己搜索数据、自己写报告。

**诊断**：

1. **Chief Skill 是否加载？** — 如果回复开头没有 `🔴 总分析师已激活`，说明 Skill 未触发。检查 `~/.claude/skills/analysts/analyst-chief/SKILL.md`。
2. **MCP Server 是否存活？** — 运行 `python tools/self-test.py`，确保 5/5 通过。
3. **子 Agent 能否访问 MCP？** — `self-test.py` 的 Gate 5 有手动验证指令。如果子 Agent 用 WebSearch 代替了 MCP，属于已知限制（取决于 Claude Code 版本），降级可用。

**快速修复**：
```bash
python install.py          # 重新安装所有 Skill + 生成项目级 .mcp.json
python tools/self-test.py  # 验证安装（预期 5/5）
```
重启 Claude Code 后重试。

### MCP Server 启动失败

**症状**：`self-test.py` Gate 1/3 报错，或 Claude 提示 MCP 工具不可用。

**诊断**：

1. **`.mcp.json` 是否在项目根目录？** — `install.py` v0.1.0+ 会同时写入项目根目录（优先）和 `~/.mcp.json`（兜底）。
2. **Python 依赖是否完整？** — 运行 `pip install -r requirements.txt`。`install.py` 会检查核心依赖。
3. **`ta` 包是否为空壳？** — `pip show ta` 查看版本。如果 wheel 仅 1-2 KB，说明是空壳。修复：`pip uninstall ta -y && pip install "ta>=0.10.0,<0.12.0"`。

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
