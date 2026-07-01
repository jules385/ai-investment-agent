# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.0] - 2026-07-01

### Added
- Added the A-share daily research workflow: `/analyze-daily`, `analyst-daily`, daily evidence pool, scoring, Markdown report generation, and Obsidian daily-note ingestion.
- Added four daily-news MCP servers: `official-announcement`, `macro-policy`, `market-news`, and `industry-data`.
- Added `tools/daily_mcp_check.py` to validate local news MCP configuration, server paths, and syntax before daily report execution.
- Added daily evidence metadata for MCP exposure status, collection rounds, time confidence, verification status, fallback notes, and pending-verification items.
- Added `原始报告/` as a code-only raw Markdown archive folder for stock logic entries.
- Added a local-first `tools/self-test.py` covering MCP config, Skills, Commands, Python syntax, daily workflow, and vault health.

### Changed
- Bumped project version to `0.4.0`.
- Reworked the Obsidian archive workflow as a Codex-only local process with no required external LLM API.
- Unified all research inputs as non-standard research outputs; removed any special standardized-report path.
- Split stock logic into `_index.md`, four analysis faces, `投资决策.md`, and `原始报告/`.
- Changed follow-up report ingestion policy: initial coverage establishes the baseline; later tracking defaults to decision-log updates unless major logic changes require updating a face or industry note.
- Updated daily window semantics to previous day `00:00:00` through report day `23:59:59` in `Asia/Shanghai`.
- Rewrote slash command files in clean UTF-8 Chinese and aligned them with current Codex workflows.

### Fixed
- Fixed stale daily workflow checks that treated unavailable online data sources as local workflow failure.
- Fixed command-entry mojibake that made several slash commands difficult for users and agents to read.
- Fixed daily report transparency by explicitly recording whether news MCP tools were exposed in the active Codex session or whether web fallback was used.
- Fixed documentation drift around 9:00 daily windows, external AI archive formatting, and deprecated source callout wrappers.

### Known Issues
- Newly configured MCP servers may require a Codex session restart or MCP reload before their tools are exposed to the active session.
- Some historical vault notes still contain deprecated source callouts and should be cleaned when those tickers are re-ingested.
- Online data connectivity remains dependent on third-party sources and should be checked with `python tools/self-test.py --online`.

---

## [0.3.0] — 2026-06-29

### Added
- **Obsidian 研究员工作区**：vault 三区架构（`行业知识库/` + `个股逻辑/` + `组合管理/`）、Dataview 面板、双向 wikilink
- `tools/archive-to-vault.py`：3阶段入库管道（AI分类标题→Python完整复制→AI排版callout），≤3分钟、~8k token
- `tools/update-workspace.py`：一键解析研报 + 同步 vault
- `tools/sync-to-vault.py`：workspace-data.json → vault 同步（callout + Mermaid流程图 + 增量保留用户笔记）
- `skills/analysts/analyst-archive/SKILL.md`：研报入库分析师
- `commands/archive-research.md`：外部研报入库命令
- `组合管理/白名单.md` `持仓名单.md` `黑名单.md`：组合管理三文件，含 `[[个股逻辑/...]]` 双向链接
- `AGENTS.md`：Codex 项目入口文档

### Improved
- 研报解析质量：分子报告定向提取（基本面 Step 5.5 → 12项跟踪指标；chief + 结论段 → 多空逻辑；4个子报告全部参与提取）
- 四维信号评分：筹码/技术/情绪子报告结论段单独提取，评分不再为零
- `web/api/parser.py`：新增 `extract_section()` 精准定位报告章节 + `industry_comprehensive` / `stock_thesis_complete` 完整提取 prompt
- 首席分析师新增 **Step 4（入库 Obsidian+ 更新组合管理）**，完成检查表升为 7/7
- Mermaid 流程图：LR→TD（纵向）`\n`→`<br/>`

### Changed
- Vault 目录重构：`stocks/`→`个股逻辑/`，`industries/`→`行业知识库/`，`_投资逻辑.md`→`组合管理/`
- 架构精简：移除 Flask 服务器及 `web/api/server.py`，解析逻辑迁移至 `web/api/report_parser.py`
- `python tools/update-workspace.py` 替代 `POST /api/parse-all`
- `analyst-archive` SKILL.md 设计哲学从"提取字段"改为"搬运+排版"

### Removed
- `web/api/server.py`（Flask 服务器）
- 旧版 HTML 产品手册 / 使用手册
- `workspace-template/`
- Claude/Codex 迁移残留：`CLAUDE.md`、`docs/CODEX适配指南.md`、`.codex-claude/`、`install.py`

---

## [0.2.0] — 2026-06-24

### Added
- 本地 Web 工作台：投研对话（SSE 流式）+ 研究员工作区三模块
- AI 研报解析器（DeepSeek / Anthropic 双 API，含本地规则回退）
- Flask 后端（`/api/chat` / `/api/parse-all` / `/api/workspace` / `/api/research-note`）

---

## [0.1.0] — 2026-06-19

### Added

#### AI Agent Skills (9 roles)

- `analyst-chief` — 6-cycle orchestration (initial coverage / weekly / monthly / quarterly / annual / portfolio batch). Whitelist traversal, mandatory QA gate, upgrade/downgrade decision rules.
- `analyst-fundamental` — 4 modes: deep (5-step: industry chain → growth logic → financial verification → valuation → whitelist), quarterly (3-statement linkage analysis), monthly (4-week trend synthesis), weekly (marginal monitoring with 5-round news search)
- `analyst-chip-flow` — 4 modes: deep (5-step: shareholders → capital flow → northbound/margin → LHB → chip distribution), quarterly/weekly (quick scan), monthly (4-week trend summary), annual (full-year review)
- `analyst-technical` — 4 modes: deep (5 timeframe × 13 indicators), weekly/quarterly (daily + 60min), monthly (weekly + monthly trend + signal hit rate), annual (yearly audit)
- `analyst-sentiment` — 4 modes: deep (3-dimension sentiment thermometer), weekly/quarterly (temperature update), monthly (4-week temperature curve), annual (yearly cycle positioning)
- `analyst-data-qa` — Post-report data quality verification. MCP real-time cross-checking, autonomous gap filling, structured passport YAML output. Mandatory gate before chief synthesis.
- `analyst-beautifier` — Markdown-to-HTML with dark theme + automatic visual enhancement (score badges, chain-tree diagrams, flow-step cards, highlight boxes)
- `analyst-portfolio-manager` — 3-portfolio system (holdings / whitelist / blacklist). Human-only write for positions; AI auto-appends research records after each analysis.
- `analyst-financial-db` — Complete 3-statement CSV database builder (income statement / balance sheet / cash flow). Multi-period retrieval, cross-verification against official filings.

#### Slash Commands (7)

| Command | Purpose |
|---------|---------|
| `/analyze-initial` | Initial coverage (full 4-dimensional deep analysis) |
| `/analyze-weekly` | Weekly tracking (quick scan mode, 5-round news search) |
| `/analyze-monthly` | Monthly tracking (4-week trend synthesis + monthly-only data) |
| `/analyze-quarterly` | Quarterly tracking (3-statement linkage: profit quality + balance sheet health + cash flow verification) |
| `/analyze-annual` | Annual strategic review (full-year financial review + competitive position reassessment + signal accuracy audit) |
| `/analyze-portfolio-weekly` | Portfolio batch weekly tracking (industry-grouped, shared news search) |
| `/beautify-report` | Generate styled HTML report with visual enhancements |

#### MCP Servers (2 servers, 25+ tools)

**finance-data** (East Money primary source, auto-fallback):
- `get_historical_data` — Daily K-line (250+ days)
- `get_financial_indicators` — Key financial metrics (同花顺)
- `get_financial_history` — Multi-period financial time series (up to 12 quarters)
- `get_valuation` — PE/PB/market cap
- `get_shareholders` — Top 10 shareholders + shareholder count trend
- `get_lhb_details` — Dragon-tiger board details
- `get_fund_flow` — Capital flow (main force/large/medium/retail)
- `get_margin_data` — Margin trading balance
- `get_hsgt_holdings` — Northbound (沪深港通) holdings
- `get_chip_distribution` — Chip cost distribution
- `get_profit_statement` — Complete income statement (East Money, 15+ line items, single-quarter values)
- `get_balance_sheet` — Complete balance sheet (18+ line items, point-in-time values)
- `get_cashflow_statement` — Complete cash flow statement (12+ line items)

**tech-analysis** (based on `ta` library):
- `compute_ma` / `compute_macd` / `compute_rsi` / `compute_kdj` / `compute_bollinger` / `compute_atr` / `compute_volume` / `detect_patterns` / `support_resistance` / `technical_score`

#### Analysis Cycles (6-track system)

| Cycle | Fundamental | Chip-Flow | Technical | Sentiment |
|-------|:--:|:--:|:--:|:--:|
| Initial Coverage | Deep (5-step) | Deep (5-step) | Deep (5 timeframe) | Deep (3-dimension) |
| Weekly | Marginal monitor | Quick scan | Daily + 60min | Temperature update |
| Monthly | 4-week trend synthesis | Trend summary | Weekly/monthly + signal audit | 4-week temperature curve |
| Quarterly | 3-statement linkage | Quick scan | Quick mode | Quick mode |
| Annual | Strategic review | Full-year review | Yearly audit | Yearly cycle |

#### Knowledge Base
- Growth logic analysis methodology handbook (40+ quantitative indicators)
- 6 analyst workflow design documents
- Product manual (HTML, 10 sections)
- User manual (Chinese, v0.1.0)

#### Tooling
- `install.py` — One-click installation (skills → `~/.claude/skills/`, commands → `~/.claude/commands/`, MCP config generation with auto Python path detection, cross-platform)
- `md-to-html.py` — Markdown-to-HTML with automatic visual enhancement (score badges, chain-tree diagrams, flow-step cards, highlight boxes)
- `self-test.py` — 4-gate automated verification (MCP server liveness → skill files → data connectivity → tool coverage)
- `workspace-template/` — Ready-to-use user workspace with blank portfolio templates

---

## [0.2.0] — 2026-06-23

### Added

-

### Changed

-

### Fixed

-

---

[0.4.0]: https://github.com/jules385/ai-investment-agent/releases/tag/v0.4.0
[0.3.0]: https://github.com/jules385/ai-investment-agent/releases/tag/v0.3.0
[0.2.0]: https://github.com/jules385/ai-investment-agent/releases/tag/v0.2.0
[0.1.0]: https://github.com/jules385/ai-investment-agent/releases/tag/v0.1.0
