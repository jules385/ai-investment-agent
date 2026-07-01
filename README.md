# A股AI投研系统

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)](VERSION)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](requirements.txt)

基于 Codex 多智能体架构的 A 股二级市场投资研究系统。四个领域分析师并行工作，由首席分析师协调，输出结构化研报，并同步到 Obsidian 知识库。

## 架构

```
用户触发分析
      │
      ▼
首席分析师 analyst-chief
      │
      ├── 基本面分析师：财务/估值/产业链
      ├── 筹码面分析师：主力/北向/融资/龙虎榜
      ├── 技术面分析师：MACD/RSI/KDJ/布林/形态
      └── 情绪面分析师：舆情/资金情绪/散户逆向
      │
      ▼
数据 QA 交叉验证
      │
      ▼
结构化研报 → Obsidian vault
```

## 快速开始

1. 安装 Python 依赖：

```bash
pip install -r requirements.txt
```

2. 可选：配置外部数据或历史兼容 API Key：

当前本地入库流程不依赖 DeepSeek / Anthropic；投研与入库由 Codex agent + 本地 Python 管道完成。若保留旧解析模块，可在 `.env` 中设置：

```text
```

3. 确认 `.mcp.json` 指向当前 Python 与项目路径。当前仓库已包含 Codex 可用的项目级 MCP 配置。

4. 在 Codex 中发起分析：

```text
/analyze-initial 002463 沪电股份
/analyze-weekly 002463
/analyze-monthly 002463
/analyze-quarterly 002463
/analyze-annual 002463
/analyze-daily
/beautify-report 002463-沪电股份
```

5. 同步 Obsidian：

```bash
python tools/update-workspace.py
```

或直接入库外部研报：

```bash
python tools/archive-to-vault.py <报告路径> <代码>-<名称> <行业名> --emit-plan reports/archive-plan-<代码>.json
# Codex 填写 archive-plan 后：
python tools/archive-to-vault.py <报告路径> <代码>-<名称> <行业名> --plan reports/archive-plan-<代码>.json
```

## Obsidian 工作区

用 Obsidian 打开 `obsidian-vault/` 文件夹，并安装 Dataview 插件。

主要入口：

- `_index.md`：全部股票概览
- `_行业知识库.md`：行业列表与产业链覆盖
- `_投资逻辑.md`：多空逻辑排行
- `_跟踪面板.md`：指标与事件覆盖情况

研究成果入库后采用分面结构：

```text
obsidian-vault/
├── 行业知识库/<行业名>.md
├── 个股逻辑/<代码-名称>/
│   ├── _index.md
│   ├── 基本面.md
│   ├── 技术面.md
│   ├── 筹码面.md
│   ├── 情绪面.md
│   ├── 投资决策.md
│   └── 原始报告/
└── 跟踪面板/<代码-名称>.md
```

初次覆盖完整建立基线；周度、月度、季度和年度跟踪默认只进入 `投资决策.md` 的跟踪记录。只有重大逻辑变化才更新基本面、技术面、筹码面、情绪面或行业知识库，且只保留带日期的逻辑变化，不按来源堆叠全文。
`原始报告/` 由 Python 自动保存 `reports/` 中的 Markdown 原文副本，独立于 Codex 分类计划，内容不做任何改写。

## 目录结构

```
ai-investment-agent/
├── AGENTS.md                 Codex 项目说明
├── README.md
├── requirements.txt
├── .mcp.json                 Codex MCP 配置
├── commands/                 Codex 斜杠命令
├── skills/analysts/          9 个 AI 分析师 Skill
├── mcp-servers/              finance-data + tech-analysis + 新闻类MCP
├── knowledge/                方法论与工作流
├── tools/                    入库、同步、美化、自测脚本
├── web/api/                  研报解析模块，无 Flask 依赖
├── reports/                  研报输出与组合文件
├── obsidian-vault/           Obsidian 工作区
└── docs/                     使用手册
```

开发维护请先阅读 [持续迭代开发文档](docs/持续迭代开发文档.md)，其中记录了入库工作流、常见问题和回归验证清单。

## 核心脚本

| 脚本 | 用途 |
|------|------|
| `python tools/update-workspace.py` | 全量解析 `reports/` 并同步 vault |
| `python tools/archive-to-vault.py <路径> <代码>-<名称> <行业> --emit-plan <plan>` | 导出入库分类计划 |
| `python tools/archive-to-vault.py <路径> <代码>-<名称> <行业> --plan <plan>` | 按 Codex 分类计划入库到行业、个股分面和跟踪面板，并由 Python 自动复制原始报告 |
| `python tools/sync-to-vault.py` | 仅同步 `workspace-data.json` 到 vault |
| `python tools/md-to-html.py <代码>-<名称>` | 生成 HTML 报告 |
| `python tools/self-test.py` | MCP、Skill、命令与解析模块自测 |

## 日报工作流

`/analyze-daily` 生成分析指令发出当天及上一天的 A 股投研日报，分为宏观、行业、个股三块。

```text
新闻/公告/政策 MCP 或 web 证据采集 → reports/daily/YYYY-MM-DD/evidence.json
    → tools/daily_score.py
    → tools/daily_report.py
    → tools/daily_to_vault.py
    → obsidian-vault/日报/YYYY-MM-DD.md
```

日报是新闻整理和影响判断，不是行情日报。默认不调用行情、资金、估值、技术指标 MCP，也不改写个股四面逻辑。重大事项只进入跟踪面板，后续由周度、季度或专题研究决定是否更新四面逻辑。
当 `scoring.json` 中的证据包含 `follow_up` 和 `related_stocks` 时，`daily_to_vault.py` 会自动把任务追加到对应单股跟踪面板。

## 免责声明

本系统仅供学习研究参考，不构成任何投资建议。AI 生成的分析结果可能存在错误或遗漏，使用者应独立判断并承担投资风险。
