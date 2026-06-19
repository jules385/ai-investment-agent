# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest | ✅ |

## Reporting a Vulnerability

If you discover a security vulnerability, please **DO NOT** open a public issue.

Instead, please report it privately via one of these channels:

1. **GitHub Security Advisories**: Use the "Report a vulnerability" button on the [Security tab](https://github.com/jules385/ai-investment-agent/security)
2. **Email**: Send details to [jules385@users.noreply.github.com]

Please include:
- A detailed description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (if available)

We will respond within 48 hours and work toward a resolution within 30 days.

## Security Considerations

This project connects to financial data APIs and stores API keys locally. Users should:

1. Never commit `.claude/settings.json` or `.mcp.json` to version control (these are in `.gitignore`)
2. Keep their API keys secure and rotate them periodically
3. Review the [`.gitignore`](.gitignore) file to understand which files are excluded from version control
