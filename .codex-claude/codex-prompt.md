# 实施任务: 检查点 3: 数据解析器 + 工作区自动填充

## 📋 任务描述

实现 Markdown 研报解析器，从 `reports/stocks/` 下已有的研报中提取结构化数据，自动填充工作区。基于检查点 2 已完成的聊天界面和检查点 1 的 `parser.py` 骨架。

## 🔨 具体任务

1. `web/api/parser.py`：完整实现 `parse_all_reports(reports_dir)`。遍历 `reports/stocks/` 下所有 `*-初次覆盖/` 目录，读取 `子报告-基本面分析师-*.md` 和 Chief 报告，提取以下内容：

2. `web/api/parser.py`：`extract_industry_chain(text)` — 检测 `### 1.1 产业链拆分` 章节，解析 `├──` `└──` `│` 树形结构。每行提取子环节名称、代表公司、毛利率、壁垒。输出 JSON 数组

3. `web/api/parser.py`：`extract_financials(text)` — 检测 `## 三、财务` 或 `### 3.` 下的表格。提取最近 5 年营收/净利/毛利率/净利率/ROE 数据。输出时间序列 JSON

4. `web/api/parser.py`：`extract_investment_thesis(text)` — 检测 `## 五、结论` 或核心投资故事段落。提取多方逻辑和空方逻辑。检测 YAML 信号块（`signal:` `direction:`）。输出 JSON

5. `web/api/parser.py`：`extract_tracking_indicators(text)` — 检测 `跟踪指标` 或 `### 5.5` 表格。提取每个指标的名称、频率、阈值。输出 JSON 数组

6. `web/api/parser.py`：`extract_events(text)` — 从周度/月度报告（`02-周度跟踪/` `03-月度跟踪/`）中提取 `| 🔴` `| 🟠` 开头的表格行。输出 JSON 数组

7. `web/api/server.py`：`/api/parse-all` 完整实现。调用 parser，将结果写入 `reports/workspace-data.json`，返回解析统计

8. `web/api/server.py`：`/api/workspace` 改为读取并返回 `reports/workspace-data.json` 的内容（如果文件不存在则返回空结构）

9. `web/js/workspace.js`：基础渲染。2.1.1 行业卡片网格（从 workspace-data 动态生成）。2.2.1 标的下拉选择器。2.3.1 跟踪指标卡片（显示状态灯）

10. 容错：找不到某章节 → 返回空数组。表格格式不一致 → 按表头匹配不硬编码列索引。YAML 解析失败 → 返回 `{raw: "原文", parsed: false}`。旧格式报告 → 标注 `format: "legacy"`

## ✅ 验收标准

- `POST /api/parse-all` 返回 `stocks_parsed >= 1`
- 工作区 Tab 显示行业卡片（至少"半导体/电子"）
- 选择"002463-沪电股份"后，指标卡片显示跟踪指标及状态灯
- 尚无研报的标的不崩溃，显示"暂无数据"
- 旧格式报告不崩溃

## ⚠️ 不修改的文件

- `web/js/chat.js` `web/css/style.css`（除非新增工作区样式）
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
