# 实施任务: 检查点 5: 集成测试 + 文档更新（最后一步）

## 📋 任务描述

端到端验证全部功能，完善错误处理，更新文档。

## 🔨 具体任务

1. 端到端验证：`python web/api/server.py` 启动 → 浏览器打开 `web/index.html` → 投研对话 Tab 发消息 → 工作区 Tab 点击行业卡片 → 选择标的 → 查看多空逻辑和跟踪指标
2. `web/api/server.py`：全局错误处理。API 不可用时返回友好降级提示。文件缺失时不崩溃
3. `web/js/app.js`：全局错误处理。网络断开提示 toast。API 错误 toast。数据加载中 loading 状态
4. `docs/使用手册.md`：新增"Web 前端使用"章节。启动步骤 + 界面说明 + 工作区功能介绍
5. `README.md`：新增 Web 前端快速启动（`python web/api/server.py` → 浏览器打开 `web/index.html`）
6. `tools/self-test.py`：新增 Web API 存活检查（`curl localhost:8765/api/health`）
7. 清理调试代码（如有 console.log）
8. `requirements.txt` 确认 `flask>=3.0.0` 和 `flask-cors>=4.0.0` 已添加

## ✅ 验收标准

- 全流程无阻塞：启动→打开→对话→解析→工作区
- 已有研报（002463 等）正确解析并显示
- 旧格式报告不崩溃
- 文档更新完整
- self-test.py 通过

## ⚠️ 注意

- 只修改上述文件，不动 `skills/` `commands/` `mcp-servers/` `parser.py`

## 📋 任务描述

基于检查点 3 已完成的 AI 解析器（`workspace-data.json` 已可由 `/api/parse-all` 生成），实现工作区三个子模块的完整交互：行业知识库详情页、投资逻辑看板（多空卡片+信号仪表盘）、边际变化追踪（指标卡片+事件时间线+调研输入）。

## 🔨 具体任务

### 4a. 行业知识库交互

`web/js/workspace.js`：
- 2.1.1 已有行业卡片网格 → 点击某个行业卡片 → 展开详情面板
- 详情面板显示：产业链文本树（`.chain-tree` 样式）、TAM/CAGR 数据卡片、可比公司财务基准表
- 从 `workspace-data.json` 的 `industries[industry]` 读取数据渲染

### 4b. 投资逻辑看板

`web/js/workspace.js`：
- 2.2.1 标的下拉选择器 → 选择标的 → 显示看板
- 2.2.2 多空逻辑面板：`.bull-card`（绿色左边框）+ `.bear-card`（红色左边框），每张卡片显示逻辑陈述 + 证据 + 验证状态标签
- 2.2.3 四维信号仪表盘：四个信号卡片（基本面/筹码面/技术面/情绪面），每个显示方向图标（🟢🔴🟡）+ 强度 + 评分
- 2.2.4 决策记录列表：日期 + 评级 + 操作建议

### 4c. 边际变化追踪

`web/js/workspace.js`：
- 2.3.1 跟踪指标卡片网格：每个指标一张卡，显示名称/最新值/阈值/状态灯（🟢正常 ⚠️接近 🔴触发）
- 2.3.2 事件时间线：按日期倒序，🔴🟠🟡 分级标签，点击展开详情
- 2.3.3 调研输入框：textarea + 提交按钮 → `POST /api/research-note` → 用 AI 解析调研记录 → 更新指标和事件

### 4d. 调研记录 AI 处理

`web/api/server.py`：`/api/research-note` 端点实现。接收 `{symbol, note}`，调用 Claude API 解析调研记录中的指标变化和事件，合并到 `workspace-data.json` 的 tracking 部分。

### 4e. 样式

`web/css/style.css`：新增工作区全部样式——行业卡片、产业链文本树、TAM 数据卡片、多空逻辑卡片（`.bull-card` / `.bear-card`）、信号仪表盘、指标卡片网格、事件时间线、调研输入框、状态灯动画。

## ✅ 验收标准

- 点击行业卡片 → 详情面板显示产业链+TAM+财务基准
- 选择标的 → 多空逻辑卡片正确显示绿色/红色边框
- 四维信号仪表盘显示方向/强度/评分
- 跟踪指标中触发阈值的显示 🔴 状态灯
- 在调研框输入文字 → 提交 → POST /api/research-note 返回成功
- 所有数据来自 `workspace-data.json`，无硬编码

## ⚠️ 不修改

- `web/api/parser.py` `web/js/chat.js` `skills/` `commands/` `mcp-servers/` `tools/` `knowledge/` `docs/`

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
