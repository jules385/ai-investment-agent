# 实施任务: 检查点 3: AI 数据解析器 + 工作区自动填充

## 📋 任务描述

🔴 **不使用规则解析。使用 AI（Claude API）提取结构化数据。** `parser.py` 不做正则匹配——它调用 Anthropic API，把研报全文发给 Claude，用 prompt 让 AI 提取结构化 JSON。这样无论报告是什么格式、哪个分析师写的、新旧版本，都能自适应处理。

## 🔨 具体任务

### 3a. AI 解析器核心

`web/api/parser.py`：只有一个函数 `ai_extract(report_text, extraction_type)`。调用 Anthropic API（复用 `ANTHROPIC_API_KEY` 环境变量），把研报全文和提取指令发给 Claude，返回结构化 JSON。

**三种提取类型 + Prompt 设计**：

**类型 1: `industry_knowledge`** — 提取行业知识库数据
```
Prompt: "从以下研报中提取行业知识库数据，返回 JSON：
{
  industry: 行业名称,
  chain: [{name, tier: '上游'|'中游'|'下游', companies, gross_margin, barriers}],
  tam_cagr: {market_size, cagr, forecast_year},
  financial_benchmarks: {可比公司: {revenue, net_profit, gross_margin, pe}}
}
只提取明确写到的数据，不要编造。"
```

**类型 2: `investment_thesis`** — 提取投资逻辑
```
Prompt: "从以下研报中提取投资逻辑，返回 JSON：
{
  bull_theses: [{statement, evidence, status: '强化'|'维持'|'弱化'|'推翻'}],
  bear_theses: [{statement, trigger_condition, severity: '高'|'中'|'低'}],
  signals: {fundamental: {direction, strength, score}, chip_flow: {}, technical: {}, sentiment: {}},
  key_assumptions: [{assumption, verification_status}]
}
"
```

**类型 3: `tracking_data`** — 提取跟踪指标和事件
```
Prompt: "从以下研报中提取跟踪数据和事件，返回 JSON：
{
  indicators: [{name, category, frequency, latest_value, threshold, status: 'normal'|'warning'|'triggered'}],
  events: [{date, description, severity: 'critical'|'major'|'minor', source_report}],
  decisions: [{date, action, rating, rationale}]
}
"
```

### 3b. 批量解析入口

`web/api/server.py`：`/api/parse-all` 实现。遍历 `reports/stocks/`：
- 对每个标的，找最新初次覆盖报告和所有跟踪报告
- 对初次覆盖报告调 `ai_extract(text, 'industry_knowledge')` + `ai_extract(text, 'investment_thesis')`
- 对跟踪报告调 `ai_extract(text, 'tracking_data')`
- 所有结果合并写入 `reports/workspace-data.json`

### 3c. 工作区前端渲染

`web/js/workspace.js`：基础渲染（从 workspace-data 读取数据）：
- 2.1.1 行业卡片网格（按行业分组，显示覆盖标的数）
- 2.2.1 标的下拉选择器（列出所有已解析标的）
- 2.3.1 跟踪指标卡片网格（状态灯 🟢🟡🔴 + 阈值高亮）
- 2.3.2 事件时间线（🟠🔴 分级 + 日期 + 描述）

### 3d. 容错

- API Key 未配置 → 返回错误提示，不崩溃
- Claude API 调用失败 → 返回 `{error: "...", extracted: {}}`，不崩溃
- 某标的无研报 → 跳过，不崩溃
- Claude 返回的 JSON 解析失败 → 重试一次，仍失败则保存原始文本

## ✅ 验收标准

- `POST /api/parse-all` 返回 `stocks_parsed >= 1`
- 工作区 Tab 显示行业卡片（至少显示"半导体/电子"）
- 选择"002463-沪电股份"后可见多空逻辑和跟踪指标
- 尚无研报的标的不崩溃
- AI 提取失败时有降级提示，不白屏

## ⚠️ 不修改的文件

- `web/js/chat.js` `web/css/style.css`（工作区样式可新增）
- `skills/` `commands/` `mcp-servers/` `tools/` `knowledge/` `docs/`

## ⚠️ 不要修改的文件

- `skills/analysts/` 下的任何 SKILL.md
- `commands/` 下的任何命令文件
- `mcp-servers/` 下的任何 Python 文件
- `tools/` 下的任何文件（除了 `self-test.py` 在检查点5可改）
- `knowledge/` `docs/` `workspace-template/` 下的任何文件

---

## 📚 项目上下文

A股AI投研系统 v0.2.0 — 基于多智能体架构的二级市场投资研究平台。v0.1.0 已完成并发布。v0.2.0 新增 HTML 前端界面。

### 技术栈

Python 3.10+, Flask（v0.2.0新增）, MCP 协议, AKShare, ta, pandas

### 已有项目结构（只读）

```
ai-investment-agent/
├── skills/analysts/     ← 8 个 AI 角色 Skill（Markdown + YAML）
├── commands/            ← 8 条斜杠命令（Markdown）
├── mcp-servers/         ← 2 个 MCP Server（Python, stdio）
│   ├── finance-data/    ← 15 个工具
│   └── tech-analysis/   ← 10 个工具
├── tools/               ← md-to-html.py, self-test.py
├── knowledge/           ← 方法论手册
├── docs/                ← 使用手册 + 产品手册
├── workspace-template/  ← 用户工作区模板
├── reports/             ← 用户数据（不进入 Git）
├── requirements.txt     ← Python 依赖
├── install.py           ← 一键安装脚本
└── .codex-claude/       ← 开发协作配置
```

### v0.2.0 新增范围

只创建 `web/` 目录，只修改 `requirements.txt`。不动任何已有文件。

## 📐 代码规范

- 前端：纯 HTML + CSS + Vanilla JS，零框架。marked.js CDN 加载
- 后端：Python Flask，端口 8765，CORS 允许
- CSS：复用项目暗色主题变量
- 所有路径使用 `pathlib.Path`

## 🔄 Git 规范

- 格式: `feat: <描述>` / `fix: <描述>`
- 每个功能完成后做一次 commit

---

---

## 📋 全部检查点概览（供参考，当前只执行检查点 1）

### 检查点 1: 项目脚手架 + 后端 API 骨架
- **目标**: 创建 `web/` 目录结构和 Flask 后端的最小可运行版本
- **验证**: `python web/api/server.py` 无报错, `curl /api/health` → 200

### 检查点 2: 投研对话 — 聊天界面
- **目标**: 实现 Claude 对话界面，SSE 流式响应，MCP 工具调用展示
- **验证**: 输入消息有回复, 流式逐字显示

### 检查点 3: 数据解析器 + 工作区自动填充
- **目标**: 解析 Markdown 研报，提取结构化数据填充工作区
- **验证**: parse-all 返回 stocks_parsed >= 1, 工作区 Tab 显示行业卡片

### 检查点 4: 研究员工作区 — 完整交互
- **目标**: 工作区三个子模块（知识库/看板/追踪）全部可交互
- **验证**: 点击行业→详情, 选标的→多空卡片, 指标触发阈值显示🔴

### 检查点 5: 集成测试 + 文档更新
- **目标**: 端到端验证，文档完整
- **验证**: 全流程无阻塞, 已有研报正确解析, 旧格式不崩溃

---

## 📡 API 契约

```
POST /api/chat           → SSE 流式对话
POST /api/parse-all      → 解析全部研报 → workspace-data.json
GET  /api/workspace      → 读取 workspace-data.json
POST /api/research-note  → 提交调研记录 → AI解析 → 更新 workspace-data.json
GET  /api/health         → 健康检查
```

## 🗂️ 工作目录

项目根目录: `C:\Users\jules\Projects\ai-investment-agent`
所有文件路径相对于此目录。Git 操作也在此目录下执行。

---

**开始实施吧！做完后请 Claude 来审查你的工作。**
