---
name: archive-research
description: 将外部研报、会议纪要或本项目分析结果入库到 Obsidian 知识库
---

# /archive-research - 研究成果入库

## 用法

```text
/archive-research [文件路径]
/archive-research [直接粘贴文本]
```

## 执行要求

调用 `analyst-archive`，按非标准化研究成果统一处理：

1. 读取输入内容，可以是文件、目录或粘贴文本。
2. 运行 `tools/archive-to-vault.py --emit-plan` 导出分类计划。
3. Codex 填写每个章节的入库目标：行业知识库、个股四面、投资决策、跳过。
4. 明确影响程度、是否改变原有逻辑、目标文件、目标章节和更新策略。
5. 运行 `tools/archive-to-vault.py --plan` 执行入库。
6. Python 自动复制 reports 下 Markdown 原文到 `原始报告/`，这一步不需要 AI 判断。
7. 运行 `--validate` 复核入库结果。

## 入库原则

- 不存在“标准化研报”特例，全部按非标准化处理。
- 初次覆盖建立四面逻辑基线。
- 后续跟踪默认只进入投资决策日志；只有重大逻辑变化才更新四面或行业知识库。
- 不在正文反复输出“原文摘录”、来源 callout 或分类理由。

## 示例

```text
/archive-research reports/stocks/002463-沪电股份
```
