# 实施任务: 检查点 1: 项目脚手架 + 后端 API 骨架

## 📋 任务描述

创建 `web/` 目录结构和 Flask 后端 API 的最小可运行版本。

## 🔨 具体任务

1. 创建 `web/` 目录：`index.html`, `css/style.css`, `js/app.js`, `js/chat.js`, `js/workspace.js`, `api/server.py`, `api/parser.py`
2. `web/index.html`：HTML 骨架 + 暗色主题 CSS + 顶部导航（投研对话 | 研究员工作区）+ 两个 Tab 面板
3. `web/css/style.css`：复用项目 CSS 变量（`--bg:#0f1117` / `--card:#1a1d28` / `--bor:#2a2d3a` / `--tx:#c9d1d9` / `--hl:#f0f6fc` / `--bl:#58a6ff` / `--gn:#3fb950` / `--rd:#f85149` / `--yl:#d2991d`），定义消息气泡、卡片、表格、按钮、标签、状态灯基础样式
4. `web/api/server.py`：Flask 应用（端口 8765），CORS 允许，端点: `/api/health`, `/api/chat`(stub), `/api/parse-all`(stub), `/api/workspace`(stub), `/api/research-note`(stub)
5. `web/api/server.py`：`/api/chat` stub 接收 `{message, history}` 返回 mock 响应
6. `web/api/parser.py`：空模块，占位函数 `parse_all_reports()`, `parse_single_report()`
7. `web/js/app.js`：Tab 切换逻辑 + `fetch('/api/workspace')` 数据加载
8. `web/js/chat.js`：空模块，占位函数 `sendMessage()`, `renderMessage()`
9. `web/js/workspace.js`：空模块，占位函数 `renderKnowledgeBase()`, `renderTheses()`, `renderTracking()`
10. `requirements.txt` 新增 `flask`, `flask-cors`

## ✅ 验收标准

- `python web/api/server.py` 无报错启动
- `curl localhost:8765/api/health` → `{"status":"ok"}`
- `curl localhost:8765/api/workspace` → `{"industries":{},"theses":{},"tracking":{}}`
- 浏览器打开 `web/index.html`，可见暗色主题的两个 Tab，点击可切换

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
