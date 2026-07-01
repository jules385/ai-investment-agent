# A股AI投研系统

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.4.1-blue.svg)](VERSION)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](requirements.txt)

基于 Codex 多智能体架构的 A 股二级市场投研系统。四个领域分析师并行工作，由首席分析师协调，输出研究报告，并沉淀到 Obsidian 知识库。

## 快速开始

```bash
pip install -r requirements.txt
copy .mcp.json.template .mcp.json
python tools/self-test.py
```

复制 `.mcp.json.template` 后，把其中的 `{{PYTHON_PATH}}` 和 `{{REPO_PATH}}` 替换为你的本机 Python 路径和项目路径。

在 Codex 中发起投研：

```text
/analyze-initial 002463 沪电股份
/analyze-weekly 002463
/analyze-monthly 002463
/analyze-quarterly 002463
/analyze-annual 002463
/analyze-daily
/beautify-report 002463-沪电股份
```

研究成果入库使用当前唯一主线：

```bash
python tools/archive-to-vault.py <报告路径> <代码>-<名称> <行业名> --emit-plan reports/archive-plan-<代码>.json
# Codex 填写 archive-plan 后：
python tools/archive-to-vault.py <报告路径> <代码>-<名称> <行业名> --plan reports/archive-plan-<代码>.json
```

## 架构

```text
用户指令
  -> analyst-chief 首席分析师
     -> analyst-fundamental 基本面
     -> analyst-chip-flow 筹码面
     -> analyst-technical 技术面
     -> analyst-sentiment 情绪面
  -> analyst-data-qa 数据交叉验证
  -> 首席合成报告
  -> tools/archive-to-vault.py
  -> Obsidian vault
```

## Obsidian 工作区

用 Obsidian 打开 `obsidian-vault/`，建议安装 Dataview 插件。

```text
obsidian-vault/
├── _index.md
├── _行业知识库.md
├── _跟踪面板.md
├── 行业知识库/
├── 个股逻辑/
│   └── <代码-名称>/
│       ├── _index.md
│       ├── 基本面.md
│       ├── 技术面.md
│       ├── 筹码面.md
│       ├── 情绪面.md
│       ├── 投资决策.md
│       └── 原始报告/
├── 跟踪面板/
├── 组合管理/
└── 日报/
```

入库原则：

- 初次覆盖建立四面基线和投资决策。
- 后续跟踪默认只更新 `投资决策.md` 的结论日志。
- 只有重大逻辑变化才更新基本面、技术面、筹码面、情绪面或行业知识库。
- `原始报告/` 由 Python 直接复制 reports 中的 Markdown 原文，不经过 AI 改写。

## 核心目录

```text
commands/          Codex 斜杠命令
skills/analysts/   10 个 AI 分析师 Skill
mcp-servers/       投研与日报 MCP 服务器
tools/             入库、日报、美化、自测脚本
knowledge/         方法论与工作流设计
docs/              使用手册与迭代文档
reports/           研究报告输出
obsidian-vault/    Obsidian 知识库
```

## 核心脚本

| 脚本 | 用途 |
|---|---|
| `python tools/archive-to-vault.py ... --emit-plan <plan>` | 生成入库分类计划模板 |
| `python tools/archive-to-vault.py ... --plan <plan>` | 按 Codex 分类计划入库到 Obsidian |
| `python tools/daily_collect.py --date YYYY-MM-DD` | 接收 MCP/web/manual 证据并生成日报证据池 |
| `python tools/daily_score.py reports/daily/YYYY-MM-DD/evidence.json` | 日报证据基础评分 |
| `python tools/daily_report.py reports/daily/YYYY-MM-DD/scoring.json` | 生成日报 Markdown |
| `python tools/daily_to_vault.py reports/daily/YYYY-MM-DD/日报.md` | 日报入库 Obsidian |
| `python tools/md-to-html.py <代码>-<名称>` | 生成 HTML 报告 |
| `python tools/self-test.py` | 检查依赖、MCP、命令、工具和本地链路 |

## 日报工作流

`/analyze-daily` 生成指令发出当天以及上一天的 A 股投研新闻日报，覆盖宏观、行业、个股三类信息。

```text
Codex 调用新闻/公告/政策 MCP 或可信 web 来源采集证据
  -> reports/daily/YYYY-MM-DD/evidence.json
  -> tools/daily_score.py
  -> Codex 做重要性判断与影响链推理
  -> tools/daily_report.py
  -> tools/daily_to_vault.py
  -> obsidian-vault/日报/YYYY-MM-DD.md
```

日报是新闻整理与影响判断，不默认调用行情、资金、估值或技术指标 MCP，也不直接改写个股四面逻辑。

## MCP 工具

- `finance-data`：10 个工具，覆盖财务、估值、行情、资金、股东、两融、北向、龙虎榜、筹码分布。
- `tech-analysis`：10 个工具，覆盖 MA、MACD、RSI、KDJ、BOLL、ATR、成交量、形态、支撑阻力、技术评分。
- `official-announcement`：公告与交易所信息。
- `macro-policy`：宏观政策新闻。
- `market-news`：市场新闻。
- `industry-data`：行业与产业链新闻。

## API Key

当前 Codex + Obsidian 主流程不依赖 DeepSeek 或 Anthropic API。`.env.example` 只保留给历史解析模块或个人扩展使用，真实 `.env` 不应提交。

## 免责声明

本系统仅供学习研究参考，不构成投资建议。AI 生成内容可能存在错误或遗漏，使用者应独立判断并自行承担投资风险。
