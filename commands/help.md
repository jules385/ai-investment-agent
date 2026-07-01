# /help - A股AI投研系统命令速查

| 命令 | 用途 | 示例 |
|------|------|------|
| `/analyze-initial 代码 名称` | 初次覆盖，生成四面深度研报 | `/analyze-initial 002463 沪电股份` |
| `/analyze-weekly 代码 名称` | 单股周度跟踪；未指定时可按组合批量跟踪 | `/analyze-weekly 002463 沪电股份` |
| `/analyze-monthly 代码 名称` | 月度趋势确认 | `/analyze-monthly 002463 沪电股份` |
| `/analyze-quarterly 代码 名称` | 季度财报跟踪与三表验证 | `/analyze-quarterly 002463 沪电股份` |
| `/analyze-annual 代码 名称` | 年度战略复盘 | `/analyze-annual 002463 沪电股份` |
| `/analyze-portfolio-weekly` | 白名单/持仓组合批量周度跟踪 | `/analyze-portfolio-weekly` |
| `/analyze-daily` | 生成 A 股投研日报 | `/analyze-daily` |
| `/archive-research 路径或文本` | 将研究成果入库 Obsidian | `/archive-research reports/stocks/002463-沪电股份` |
| `/beautify-report 代码-名称` | 生成 HTML 阅读版报告 | `/beautify-report 002463-沪电股份` |
| `/help` | 显示命令速查 | `/help` |

常用本地工具：

```bash
python tools/self-test.py
python tools/archive-to-vault.py <报告路径> <代码-名称> <行业名>
python tools/daily_mcp_check.py
```
