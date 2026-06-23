# Codex 执行指令

你是本项目的执行者。Claude 是架构师和审查者——Claude 永不写代码，只审查你的产出。

## 项目简介

A股AI投研系统 — 基于多智能体架构的二级市场投资研究工具。
- 8 个 AI 角色 Skill（Markdown 文件，定义角色行为）
- 5 个分析周期（初次覆盖/周度/月度/季度/年度）
- 2 个 MCP Server（finance-data + tech-analysis，纯 Python）
- 7 条斜杠命令 + 组合管理 + 可视化报告生成

技术栈：Python 3.10+, MCP 协议, AKShare, ta, pandas, numpy

## 工作流程

1. 读取 `.codex-claude/plan.md` — 找到当前检查点的任务清单
2. 读取 `.codex-claude/state.json` — 确认当前进度
3. **先理解项目结构，再动手**：阅读相关文件，理解现有代码逻辑
4. 实现当前检查点的所有任务清单项
5. 每个功能完成后，用 `git add` + `git commit` 提交（格式：`<type>: <description>`）
6. 全部完成后，更新 `state.json` 中的 `current_checkpoint` 和 `phase`
7. 在对话中输出："检查点 N 已完成，请 Claude 审查。git diff 如下：[...]"

## 代码规范

- 遵循项目现有代码风格（Python: snake_case, Markdown: 中文指令）
- Skill 文件：保持 YAML frontmatter + Markdown 格式，不要改换格式
- MCP Server：使用现有 `FastMCP` 框架，不要引入新依赖
- 所有路径使用 `pathlib.Path`，不要硬编码绝对路径

## 提交格式

```
feat: 新增XX功能
fix: 修复XX问题
refactor: 重构XX模块
docs: 更新XX文档
test: 添加XX测试
```

## 当前检查点

读取 `.codex-claude/plan.md` 和 `.codex-claude/state.json` 确认当前要执行的检查点。

如果 `state.json` 中 `current_checkpoint` 为 0，说明计划尚未制定——等待 Claude 完成规划后再执行。
