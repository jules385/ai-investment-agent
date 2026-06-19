# Contributing to AI 投研系统

Thanks for your interest in contributing! This project is a Claude Code-based multi-agent investment research system for Chinese A-shares. Here's how you can help.

## Ways to Contribute

### 🧠 Add a New Analyst Role

1. Create a new `skills/analysts/analyst-<name>/SKILL.md` with:
   - YAML frontmatter (`name`, `description`, `trigger` keywords)
   - Role definition (what the agent does, what MCP tools it uses)
   - Mode definitions (deep vs. quick scan)
   - Standardized YAML signal output block
2. Add a workflow design doc in `knowledge/workflows/`
3. Update the chief analyst skill if the new role should be part of the parallel fan-out
4. Run `python install.py` to install the new skill

### 📊 Add a New MCP Tool or Data Source

1. Find the relevant MCP server in `mcp-servers/`
2. Add a new `@mcp.tool()` decorated function following the existing patterns:
   - Use the `_throttle()` decorator for East Money sources
   - Use `_safe()` for NaN handling
   - Return `dict` type with descriptive keys
3. Test with a real stock symbol
4. Update the relevant analyst skill if the new tool changes the data acquisition flow

### 🔧 Improve Existing Analysts

- **Methodology improvements**: Add to `knowledge/` or update existing workflow docs
- **Prompt engineering**: Edit the `SKILL.md` files — clearer instructions, better examples, tighter constraints
- **Bug fixes**: If an analyst consistently produces wrong outputs in a certain scenario, open an issue first to discuss

### 🌐 Add English Translations

The core audience is Chinese-speaking, but English translations of docs and skill descriptions are welcome. Place them alongside the Chinese originals with `.en.md` suffix.

## Development Setup

```bash
# Clone and install
git clone https://github.com/jules385/ai-investment-agent.git
cd ai-investment-agent
pip install -r requirements.txt

# Install skills/commands to local Claude Code
python install.py

# Test with a stock
# In Claude Code: /analyze-initial 002414
```

## Pull Request Guidelines

1. **Keep PRs focused** — one feature or fix per PR
2. **Test with real data** — run the changed analyst against at least one real stock symbol
3. **Update docs** — if you change behavior, update the relevant `docs/` or `knowledge/` files
4. **No user data** — never commit real stock reports, whitelist entries, or API keys
5. **Check `.gitignore`** — make sure your changes don't introduce files that should be excluded

## Project Structure

```
ai-investment-agent/
├── skills/analysts/     ← AI agent role definitions (SKILL.md each)
├── commands/            ← Claude Code slash commands
├── mcp-servers/         ← Python MCP data services
├── knowledge/           ← Methodology handbooks + workflow designs
├── tools/               ← Utility scripts
├── docs/                ← User documentation
├── workspace-template/  ← User workspace starter kit
└── install.py           ← One-click installer
```

## Questions?

Open a [GitHub Discussion](https://github.com/jules385/ai-investment-agent/discussions) for questions about architecture, design decisions, or feature ideas before submitting a PR.
