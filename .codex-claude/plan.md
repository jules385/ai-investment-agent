# v0.2.0 开发计划

> Claude 负责规划检查点。Codex 负责逐个执行。
> 每个检查点完成后，Claude 审查 → 通过后进入下一个。

## 项目上下文

A股AI投研系统 — 基于 Claude Code 多智能体架构的二级市场投资研究平台。
8 个 AI 角色、5 个分析周期、2 个 MCP Server、7 条斜杠命令。

技术栈：Python 3.10+, MCP 协议, AKShare, ta 技术分析库, Markdown

目录结构：
- `skills/analysts/` — 8 个 AI 角色 Skill（纯 Markdown + YAML frontmatter）
- `commands/` — 8 条斜杠命令（Markdown）
- `mcp-servers/` — 2 个 MCP Server（Python, stdio 通信）
- `tools/` — 辅助脚本（Python）
- `knowledge/` — 方法论手册（Markdown）
- `docs/` — 使用手册 + 产品手册 + Codex适配指南
- `workspace-template/` — 用户工作区模板
- `.codex-claude/` — Claude-Codex 协作配置

---

## 检查点清单

> 由 Claude 在规划阶段填写。每个检查点须包含：目标、任务清单、验证标准。

### 检查点 1：[待定义]

- **目标**：
- **任务清单**：
- **验证标准**：

---

*此文件由 Claude 在规划阶段填写。Codex 执行时读取此文件获取当前检查点任务。*
