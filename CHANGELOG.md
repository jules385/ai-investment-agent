# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.0.0] — 2026-06-17

### Added

#### AI Agent Skills (7 roles)
- `analyst-fundamental` — Industry analysis, growth logic (supply/demand/competition), financial cross-validation, valuation, whitelist decision matrix
- `analyst-chip-flow` — Shareholder structure, capital flow, northbound/margin trading, dragon-tiger board, chip distribution, fund alignment
- `analyst-technical` — Multi-timeframe trend positioning, MACD/RSI/KDJ/Bollinger/ATR/volume/patterns, buy/sell signals, price anchors
- `analyst-sentiment` — Market sentiment + stock public opinion + retail behavior monitoring → sentiment thermometer (0-100)
- `analyst-chief` — Parallel subagent orchestration, contradiction detection, regime-adaptive weighting, final investment decision
- `analyst-data-qa` — Post-report data quality check, autonomous data gap filling, revision loop routing
- `analyst-beautifier` — Markdown-to-HTML report generation with dark theme

#### Slash Commands (5)
- `/analyze-initial` — Initial coverage (full four-dimensional deep analysis)
- `/analyze-weekly` — Weekly tracking (quick scan mode)
- `/analyze-monthly` — Monthly tracking
- `/analyze-quarterly` — Quarterly tracking (full deep analysis + financial focus)
- `/beautify-report` — Generate HTML report

#### MCP Servers (2)
- `finance-data` — Fundamental data service (7 tools): historical K-line, financial indicators, valuation, shareholders, dragon-tiger board, fund flow, margin data. East Money primary source with auto-fallback.
- `tech-analysis` — Technical analysis service (10 tools): MA, MACD, RSI, KDJ, Bollinger Bands, ATR, volume analysis, pattern detection, support/resistance, technical scoring. Based on `ta` library.

#### Knowledge Base
- Growth logic analysis methodology handbook (40+ quantitative indicators across supply/demand/competition)
- 6 analyst workflow design documents with detailed step-by-step processes

#### Tooling
- `install.py` — One-click installation (skills, commands, MCP config generation)
- `md-to-html.py` — Markdown report to styled HTML converter
- `workspace-template/` — Ready-to-use user workspace with blank templates

#### Documentation
- User manual (`使用手册.md`) — Complete system guide
- Project introduction page (`AI投研系统介绍书.html`)

---

[0.0.0]: https://github.com/jules385/ai-investment-agent/releases/tag/v0.0.0
