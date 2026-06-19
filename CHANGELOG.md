# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/jules385/ai-investment-agent/releases/tag/v0.1.0
