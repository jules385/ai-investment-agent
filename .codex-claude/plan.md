# v0.2.0 开发计划：HTML 前端 + 研究员工作区

> Claude 设计架构 → Claude 动态生成 codex-prompt.md（嵌入当前检查点任务）→ Codex 执行 → Claude 审查 → 通过则重新生成下一检查点的 codex-prompt.md / 不通过则打回 → 循环直到全部完成
>
> 🔴 **关键机制**：`codex-prompt.md` 不是静态文件。Claude 在每个检查点开始时重新生成它，把当前检查点的任务清单嵌入文件顶部。Codex 每次读取最新的 `codex-prompt.md` 执行。
>
> 🔴 **启动指令**（用户只需执行一次）：
> 将以下内容发送给 Codex：
> "请持续监控 .codex-claude/state.json。当 checkpoint_status 不为 completed 时，读取 .codex-claude/codex-prompt.md 执行当前检查点任务。完成后更新 state.json 为 pending_review。当 state.json 显示审查通过后，等待 Claude 更新 codex-prompt.md 为下一个检查点，然后继续执行。"

---

## 一、功能架构（三级）

```
A股AI投研系统 v0.2.0
│
├─ 1. 投研对话 ──────────────────────────────────────────────
│   ├─ 1.1 对话窗口
│   │   ├─ 1.1.1 消息列表（用户/AI 气泡 + Markdown 渲染）
│   │   ├─ 1.1.2 消息输入（输入框 + 发送按钮 + Enter 快捷键）
│   │   ├─ 1.1.3 流式响应（SSE 逐字展示 + 光标闪烁动画）
│   │   └─ 1.1.4 消息操作（复制 / 重新生成 / 停止生成）
│   │
│   ├─ 1.2 命令面板
│   │   ├─ 1.2.1 快捷按钮行（/analyze-initial /analyze-weekly /analyze-quarterly /beautify-report /help）
│   │   ├─ 1.2.2 命令自动补全（输入 / 弹出下拉候选）
│   │   └─ 1.2.3 命令历史（↑↓ 浏览历史命令）
│   │
│   ├─ 1.3 工具调用展示
│   │   ├─ 1.3.1 MCP 调用折叠卡片（工具名 + 耗时 + 展开/折叠）
│   │   ├─ 1.3.2 工具调用状态图标（✅ 成功 / ❌ 失败 / ⏳ 进行中）
│   │   └─ 1.3.3 子 Agent 进度追踪（4 个分析师并行进度条）
│   │
│   └─ 1.4 报告管理
│       ├─ 1.4.1 报告列表侧栏（按标的/日期排序）
│       ├─ 1.4.2 报告预览（Markdown 渲染 + 折叠章节）
│       └─ 1.4.3 一键导出（HTML 报告生成按钮）
│
├─ 2. 研究员工作区 ──────────────────────────────────────────
│   │  🔴 核心设计：工作区由 AI 自动填充。用户在功能1中展开
│   │  投研并产出报告后，系统自动解析报告内容 → 更新工作区。
│   │  不是让用户手动录入——是 AI 读报告、AI 填数据。
│   │
│   ├─ 2.1 行业知识库
│   │   ├─ 2.1.1 行业卡片网格（每个行业一张卡：名称 / 覆盖标的 / 最近更新）
│   │   └─ 2.1.2 行业详情页（产业链 + 市场空间 + 财务基准 + 政策时间线）
│   │       └─ 内容直接取决于研报解析结果，不预置固定模板
│   │
│   ├─ 2.2 投资逻辑看板
│   │   ├─ 2.2.1 标的概览（下拉选择器 + 摘要卡片 + 研究历史时间线）
│   │   ├─ 2.2.2 多空逻辑面板（🟢多方 / 🔴空方 卡片 + 验证状态标签）
│   │   ├─ 2.2.3 四维信号仪表盘（方向/强度/评分 + 历史变化）
│   │   └─ 2.2.4 决策记录（评级历史 + 操作建议汇总 + 待处理事项）
│   │
│   └─ 2.3 边际变化追踪
│       ├─ 2.3.1 跟踪指标仪表盘（卡片网格 + 🟢✅🔴状态灯 + 阈值高亮）
│       ├─ 2.3.2 事件时间线（🟠🔴🟡分级 + 筛选 + 详情弹窗）
│       └─ 2.3.3 调研追踪
│           ├─ 文字输入框：用户输入调研记录
│           └─ AI 自动分析 → 更新 2.3.1（指标）和 2.3.2（事件时间线）
│
├─ 3. 数据服务层 ──────────────────────────────────────────
│   ├─ 3.1 研报解析器
│   │   ├─ 3.1.1 入口：`POST /api/parse-all` → 遍历 `reports/stocks/` 全部研报
│   │   ├─ 3.1.2 输出：统一的 `workspace-data.json`（按行业/标的/指标三级索引）
│   │   ├─ 3.1.3 触发时机：每次投研对话产出新报告后自动调用
│   │   └─ 3.1.4 提取内容：产业链表格 / 财务指标表 / 投资逻辑 / 跟踪指标 / 事件
│   │
│   ├─ 3.2 Claude API 代理
│   │   ├─ 3.2.1 `POST /api/chat` — SSE 流式对话
│   │   ├─ 3.2.2 System Prompt 构建（启动时加载全部 SKILL.md）
│   │   └─ 3.2.3 会话管理（`GET/POST /api/sessions`）
│   │
│   └─ 3.3 调研记录处理器
│       ├─ 3.3.1 `POST /api/research-note` — 接收文字调研记录
│       ├─ 3.3.2 AI 解析 → 提取关键指标变动 + 事件
│       └─ 3.3.3 自动合并到 `workspace-data.json` 的 tracking 部分
│
└─ 4. 全局 ────────────────────────────────────────────────
    ├─ 4.1 顶部固定导航（投研对话 | 研究员工作区）
    ├─ 4.2 暗色主题（复用项目 CSS 变量）
    └─ 4.3 响应式布局（桌面三栏 / 平板两栏 / 手机单栏）
```

---

## 二、技术架构

```
浏览器 (web/index.html)
    │
    ├─ GET  → 静态文件 (HTML/CSS/JS)
    │
    ├─ POST /api/chat           → SSE 流式对话
    ├─ POST /api/parse-all      → 解析全部研报 → workspace-data.json
    ├─ GET  /api/workspace      → 读取 workspace-data.json（前端渲染工作区）
    ├─ POST /api/research-note  → 提交调研记录 → AI解析 → 更新 workspace-data.json
    ├─ GET  /api/sessions       → 会话列表
    └─ GET  /api/health         → 健康检查
            │
            ├─→ Anthropic/DeepSeek API (云端)
            └─→ 本地文件系统 (reports/ + workspace-data.json)
```

**关键文件**：

| 文件 | 作用 |
|------|------|
| `web/index.html` | 单页入口 |
| `web/css/style.css` | 全部样式（复用项目 CSS 变量） |
| `web/js/app.js` | 全局逻辑（导航、Tab切换、数据加载） |
| `web/js/chat.js` | 投研对话（消息/流式/命令/MCP展示） |
| `web/js/workspace.js` | 研究员工作区（知识库/看板/追踪） |
| `web/api/server.py` | Flask 后端（全部 API 端点） |
| `web/api/parser.py` | 研报解析器（Markdown → JSON） |
| `reports/workspace-data.json` | 工作区数据（解析器生成，前端读取） |

**技术选型**：
- 前端：纯 HTML + CSS + Vanilla JS（零框架依赖）
- 后端：Python Flask（轻量，复用项目现有依赖）
- Markdown 渲染：marked.js（CDN 加载）
- 数据存储：单个 `workspace-data.json` 文件（解析器写入，前端读取）
- 不引入额外的数据库、图表库或前端框架

---

## 三、API 契约（Codex 必须严格实现）

### 3.1 `POST /api/chat`

```
Request:  { "message": "string", "session_id": "string|null" }
Response: SSE stream
  event: token       data: {"content": "..."}
  event: tool_call   data: {"tool": "...", "args": {...}, "status": "..."}
  event: done        data: {"session_id": "...", "report_path": "..."}
```

### 3.2 `POST /api/parse-all`

```
Request:  无参数
Response: { "status": "ok", "stocks_parsed": N, "industries": ["..."] }
副作用:  写入 reports/workspace-data.json
```

### 3.3 `GET /api/workspace`

```
Response: workspace-data.json 的完整内容
{
  "industries": {
    "半导体/电子": {
      "stocks": ["002463", "002119"],
      "chain": {...},        // 产业链数据
      "tam_cagr": {...},     // 市场空间
      "financials": {...}    // 财务基准
    }
  },
  "theses": {
    "002463": {
      "bull": [...],         // 多方逻辑卡片
      "bear": [...],         // 空方逻辑卡片
      "signals": {...},      // 四维信号
      "decisions": [...]     // 决策记录
    }
  },
  "tracking": {
    "002463": {
      "indicators": [...],   // 跟踪指标
      "events": [...],       // 事件时间线
      "notes": [...]         // 调研记录
    }
  }
}
```

### 3.4 `POST /api/research-note`

```
Request:  { "symbol": "002463", "note": "调研记录文字..." }
Response: { "status": "ok", "indicators_updated": N, "events_added": N }
副作用:  更新 workspace-data.json 的 tracking.{symbol} 部分
```

---

## 四、检查点

### 检查点 1：项目脚手架 + 后端 API 骨架

**目标**：`python web/api/server.py` 可启动，所有 API 端点返回 200。

**文件清单**：

| 文件 | 内容 |
|------|------|
| `web/index.html` | HTML 骨架：顶部导航栏（投研对话 \| 研究员工作区）+ 两个 `<div id="tab-*">` 面板 |
| `web/css/style.css` | 暗色主题基础样式：CSS 变量、导航栏、按钮、输入框、卡片、标签、状态灯（🟢🔴🟡） |
| `web/js/app.js` | Tab 切换逻辑 + `fetch('/api/workspace')` 数据加载 |
| `web/js/chat.js` | 空模块，占位函数 `sendMessage()`, `renderMessage()`, `renderToolCall()` |
| `web/js/workspace.js` | 空模块，占位函数 `renderKnowledgeBase()`, `renderTheses()`, `renderTracking()` |
| `web/api/server.py` | Flask app (port 8765), CORS, 端点: `/api/health`, `/api/chat`(stub), `/api/parse-all`(stub), `/api/workspace`(stub), `/api/research-note`(stub) |
| `web/api/parser.py` | 空模块，占位函数 `parse_all_reports()`, `parse_single_report()` |
| `requirements.txt` | 新增 `flask`, `flask-cors` |

**验收**：
1. `python web/api/server.py` 无报错启动
2. `curl localhost:8765/api/health` → `{"status":"ok"}`
3. `curl localhost:8765/api/workspace` → `{"industries":{},"theses":{},"tracking":{}}`
4. 浏览器打开 `web/index.html`，可见暗色主题的两个 Tab，点击可切换

---

### 检查点 2：投研对话 — 完整聊天界面

**目标**：在功能1中可与 Claude 对话，看到流式回复和 MCP 工具调用。

**文件清单**：

| 文件 | 新增/修改 |
|------|---------|
| `web/js/chat.js` | 完整实现：消息列表渲染（用户右/Claude左）+ Markdown 渲染（marked.js CDN）+ 输入框+发送+Enter + SSE 流式接收 + MCP 调用折叠面板 |
| `web/css/style.css` | 新增：消息气泡样式（.msg-user / .msg-claude）、代码块、表格、MCP 折叠面板、loading 动画、流式光标 |
| `web/api/server.py` | `/api/chat` 完整实现：调用 Anthropic Messages API，SSE 流式返回，启动时加载 skills/analysts/ 构建 system prompt |
| `web/index.html` | 新增快捷命令按钮行、marked.js CDN 引用 |

**验收**：
1. 输入"你好"，Claude 流式回复可见
2. 输入"对 002414 高德红外进行初次覆盖"，触发分析（如 MCP 配置正确）
3. 命令按钮点击后自动填入输入框
4. MCP 工具调用展示为折叠卡片

---

### 检查点 3：数据解析器 + 工作区自动填充

**目标**：对话产出报告后，系统自动解析并更新工作区。打开工作区 Tab 可见数据。

**文件清单**：

| 文件 | 新增/修改 |
|------|---------|
| `web/api/parser.py` | 完整实现：解析 Markdown 研报的 §1.1 产业链拆分、§1.3 TAM/CAGR、§3 财务指标表、§5 投资逻辑、YAML 信号块、§5.5 跟踪指标清单、周度/月度报告中的 🟠🔴 事件 |
| `web/api/server.py` | `/api/parse-all` 实现：遍历 `reports/stocks/` → 调用 parser → 写入 `reports/workspace-data.json`；`/api/workspace` 实现：返回 JSON 文件内容 |
| `web/api/server.py` | `/api/chat` 增强：对话完成后自动调用 parse-all（如果检测到新报告文件） |
| `web/js/workspace.js` | 基础渲染：行业卡片网格（2.1.1）、标的下拉（2.2.1）、指标卡片（2.3.1）、事件列表（2.3.2） |
| `web/css/style.css` | 新增：行业卡片、产业链文本树、指标卡片、事件时间线样式 |

**验收**：
1. 手动触发 `POST /api/parse-all` → 返回 `stocks_parsed >= 1`
2. 打开工作区 Tab，行业卡片网格可见（至少显示"半导体/电子"）
3. 选择"002463-沪电股份"，指标卡片显示 12 个跟踪指标及状态灯
4. 事件时间线显示最近报告中的 🟠🔴 事件
5. 对应尚无研报的标的不崩溃，显示"暂无数据"

---

### 检查点 4：研究员工作区 — 完整交互

**目标**：工作区三个子模块全部可交互，数据来自 `workspace-data.json`。

**文件清单**：

| 文件 | 新增/修改 |
|------|---------|
| `web/js/workspace.js` | 完整实现：2.1 行业知识库（点击行业→详情页→产业链文本树+TAM卡片+财务表）+ 2.2 投资逻辑看板（选标的→多空逻辑卡片+验证状态标签+四维信号仪表盘+决策记录）+ 2.3 边际变化追踪（指标卡片网格+状态灯+事件时间线+调研输入框→POST /api/research-note） |
| `web/css/style.css` | 新增：产业链文本树、TAM卡片、多空逻辑卡片（绿底/红底）、信号仪表盘、调研输入框样式 |
| `web/api/server.py` | `/api/research-note` 完整实现：接收文字→用 Claude 解析→提取指标变动+事件→合并到 workspace-data.json |

**验收**：
1. 点击行业卡片 → 进入详情页，显示产业链文本树和 TAM 数据
2. 选择标的 → 多空逻辑卡片正确显示绿色/红色边框
3. 四维信号仪表盘显示方向/强度/评分
4. 跟踪指标中触发阈值的显示 🔴 状态灯
5. 在调研框输入文字 → 提交 → 对应指标的数值或事件被更新

---

### 检查点 5：集成 + 测试 + 文档

**目标**：端到端可用，文档更新。

**文件清单**：

| 文件 | 新增/修改 |
|------|---------|
| `web/api/server.py` | 错误处理：API 不可用时的降级提示、文件缺失时的空返回、超时处理 |
| `web/js/app.js` | 全局错误处理：网络断开提示、API 错误 toast、数据加载中 loading 状态 |
| `docs/使用手册.md` | 新增"Web 前端使用"章节：启动步骤、界面说明、工作区功能介绍 |
| `README.md` | 新增 Web 前端快速启动（`python web/api/server.py` → 浏览器打开 `web/index.html`） |
| `python tools/self-test.py` | 新增 Web API 存活检查（`curl localhost:8765/api/health`） |

**验收**：
1. 完整流程：启动 server → 打开前端 → 对话 → 生成报告 → 工作区自动更新
2. 使用已有研报（002463/002119/601869/300502）验证解析器：所有标的的产业链/财务/指标/事件均正确提取
3. 旧格式报告（缺章节/旧版结构）不崩溃，返回 warning
4. `python tools/self-test.py` 通过（含 Web API 检查）
5. 文档更新完整，新用户可按手册启动前端
