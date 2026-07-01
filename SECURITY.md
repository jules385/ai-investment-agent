# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest | Yes |

## Reporting a Vulnerability

Please do not open a public issue for security vulnerabilities.

Use GitHub Security Advisories on the repository Security tab, or contact the maintainer via the GitHub profile email.

Please include:

- A clear description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fixes, if available

## Sensitive Local Files

This project is designed for local Codex + MCP + Obsidian usage. Do not commit:

- `.env`
- `.mcp.json`
- `.codex/`
- API keys, tokens, cookies, or private credentials
- personal Obsidian vault content under `obsidian-vault/`
- real reports under `reports/stocks/`
- generated daily reports under `reports/daily/`
- portfolio files such as `持仓组合.md`, `白名单组合.md`, `黑名单组合.md`
- archive plans that may contain private research notes

Use `.mcp.json.template` for public MCP configuration examples.

## Financial Data Disclaimer

The system uses public or third-party financial data sources. Data may be delayed, incomplete, unavailable, or incorrect. Users should independently verify data before making any investment decision.
