# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.1] - 2026-07-01

### Fixed

- Removed the legacy workspace sync scripts so new users cannot accidentally write the deprecated single-file stock layout.
- Upgraded `tools/self-test.py` from syntax-only checks to real dependency imports, MCP config validation, MCP server top-level imports, command checks, tool imports, daily-window checks, and vault template checks.
- Added `akshare`, `ta`, `mcp`, `fastmcp`, and `markdown` to the default dependency gate so missing runtime packages are caught before users start a workflow.
- Clarified that the daily workflow is Codex + MCP/web evidence collection + Python persistence, not a standalone Python news crawler.
- Rewrote README, AGENTS, and the user manual around the current v0.4.1 workflow.
- Corrected documentation counts for 10 analyst Skills, 10 `finance-data` tools, and 10 `tech-analysis` tools.

### Changed

- Made `tools/archive-to-vault.py` the only stock research archive entry.

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

---

## [0.1.0] - 2026-06-19

### Added

- Initial open-source release of the Codex-based A-share research agent.
- Added multi-analyst Skills for chief orchestration, fundamentals, chip flow, technical analysis, sentiment, data QA, beautification, and portfolio notes.
- Added slash commands for initial coverage, weekly/monthly/quarterly/annual tracking, portfolio weekly tracking, and report beautification.
- Added local MCP servers for A-share finance data and technical indicators.
- Added basic research methodology documents and Markdown-to-HTML tooling.

---

[0.4.1]: https://github.com/jules385/ai-investment-agent/releases/tag/v0.4.1
[0.4.0]: https://github.com/jules385/ai-investment-agent/releases/tag/v0.4.0
[0.1.0]: https://github.com/jules385/ai-investment-agent/releases/tag/v0.1.0
