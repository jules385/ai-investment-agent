# Contributing to A股AI投研系统

Thanks for your interest in contributing. This project is developed and used in Codex, with MCP data tools and an Obsidian knowledge base.

## Development Setup

```bash
git clone https://github.com/jules385/ai-investment-agent.git
cd ai-investment-agent
pip install -r requirements.txt
python tools/self-test.py
```

Copy `.mcp.json.template` to `.mcp.json` and replace `{{PYTHON_PATH}}` / `{{REPO_PATH}}` with local paths.

## Ways to Contribute

### Improve Analyst Skills

1. Update the relevant `skills/analysts/<name>/SKILL.md`.
2. Keep instructions precise, testable, and compatible with `analyst-chief`.
3. Update `commands/` if the user-facing workflow changes.
4. Run `python tools/self-test.py`.

### Add or Improve MCP Servers

1. Add MCP tools under `mcp-servers/`.
2. Prefer official or reliable data sources.
3. Keep daily-news MCPs separate from market/technical MCPs.
4. Update `.mcp.json.template`.
5. Document fallback behavior when a tool is not exposed in the active Codex session.

### Improve Obsidian Archive Workflow

1. Keep archive logic local and deterministic where possible.
2. Do not require external LLM APIs for archive ingestion.
3. Preserve `<!-- /ai-content -->` user sections.
4. Do not copy full follow-up reports into stock logic unless a major logic change is identified.

## Pull Request Guidelines

1. Keep PRs focused.
2. Run `python tools/self-test.py`.
3. Use `python tools/self-test.py --online` only when checking third-party data connectivity.
4. Update `README.md`, `AGENTS.md`, `docs/使用手册.md`, or `docs/持续迭代开发文档.md` when behavior changes.
5. Never commit `.env`, `.mcp.json`, `.codex/`, personal Obsidian vault content, real portfolio files, or private research notes.

## Project Structure

```text
ai-investment-agent/
├── AGENTS.md
├── commands/
├── skills/analysts/
├── mcp-servers/
├── knowledge/
├── tools/
├── web/api/
├── reports/
├── obsidian-vault/
└── docs/
```
