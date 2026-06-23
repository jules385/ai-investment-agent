# v0.2.0 开发计划：HTML 前端 + 研究员工作区

> Claude 设计架构 → Codex 逐检查点执行 → Claude 审查

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
│   │   ├─ 1.2.1 快捷按钮行（/analyze-initial /analyze-weekly /beautify-report /help）
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
│   │
│   ├─ 2.1 行业知识库 ──────────────────────────────────────
│   │   ├─ 2.1.1 行业总览（行业列表 + 覆盖标的数 + 最近更新）
│   │   │   ├─ 2.1.1.1 行业卡片网格（每个行业一张卡片）
│   │   │   ├─ 2.1.1.2 覆盖进度条（已覆盖/未覆盖标的数）
│   │   │   └─ 2.1.1.3 最近更新时间和来源报告
│   │   │
│   │   ├─ 2.1.2 行业详情页
│   │   │   ├─ 2.1.2.1 产业链图谱（树形图，上游/中游/下游各≥3子环节）
│   │   │   │   └─ 每个子环节：名称 / 代表公司 / 毛利率 / 壁垒 / 国产化率
│   │   │   ├─ 2.1.2.2 市场空间面板（TAM/SAM/SOM 卡片 + CAGR 趋势图）
│   │   │   ├─ 2.1.2.3 行业财务基准（可比公司核心指标对比表）
│   │   │   └─ 2.1.2.4 政策与催化剂时间线
│   │   │
│   │   └─ 2.1.3 知识搜索
│   │       ├─ 2.1.3.1 全文搜索（搜索行业/公司/指标名）
│   │       ├─ 2.1.3.2 产业链定位搜索（"谁做XX环节"）
│   │       └─ 2.1.3.3 搜索结果高亮 + 来源跳转
│   │
│   ├─ 2.2 投资逻辑看板 ──────────────────────────────────
│   │   ├─ 2.2.1 标的概览
│   │   │   ├─ 2.2.1.1 标的下拉选择器（搜索/筛选）
│   │   │   ├─ 2.2.1.2 标的摘要卡片（代码/名称/行业/评级/覆盖日期）
│   │   │   └─ 2.2.1.3 最近五次研究记录时间线
│   │   │
│   │   ├─ 2.2.2 多空逻辑面板
│   │   │   ├─ 2.2.2.1 多方逻辑卡片组（绿色边框）
│   │   │   │   └─ 每张卡片：逻辑陈述 + 证据链 + 验证状态标签
│   │   │   ├─ 2.2.2.2 空方逻辑卡片组（红色边框）
│   │   │   │   └─ 每张卡片：风险陈述 + 触发条件 + 严重程度
│   │   │   └─ 2.2.2.3 逻辑演变历史（从初次覆盖到最近一次的分析结论变化）
│   │   │
│   │   ├─ 2.2.3 四维信号仪表盘
│   │   │   ├─ 2.2.3.1 雷达图（基本面/筹码面/技术面/情绪面四维评分）
│   │   │   ├─ 2.2.3.2 信号方向指示器（看多/中性/看空 + 强度）
│   │   │   └─ 2.2.3.3 信号历史变化（最近 4-8 次分析的评分趋势）
│   │   │
│   │   └─ 2.2.4 决策记录
│   │       ├─ 2.2.4.1 白名单评级历史（核心→卫星→观察 的变动记录）
│   │       ├─ 2.2.4.2 操作建议汇总（每次分析的操作建议一览）
│   │       └─ 2.2.4.3 待处理事项清单（跟踪指标触警 + 缺口数据 + 需复查项）
│   │
│   └─ 2.3 边际变化追踪 ──────────────────────────────────
│       ├─ 2.3.1 跟踪指标仪表盘
│       │   ├─ 2.3.1.1 指标卡片网格（按类别分组：行业/公司/竞争/技术/估值）
│       │   │   └─ 每张卡片：指标名 / 最新值 / 阈值 / 状态灯 / 趋势箭头
│       │   ├─ 2.3.1.2 阈值触警高亮（🔴 触发 / ⚠️ 接近 / ✅ 正常）
│       │   └─ 2.3.1.3 指标详情弹窗（历史数据迷你图 + 触发条件说明）
│       │
│       ├─ 2.3.2 事件时间线
│       │   ├─ 2.3.2.1 时间线列表（按日期倒序，🟠🔴🟡 事件分级）
│       │   │   └─ 每条：日期 / 事件摘要 / 影响等级 / 来源报告
│       │   ├─ 2.3.2.2 事件筛选（按等级 / 按类别 / 按时间范围）
│       │   └─ 2.3.2.3 事件详情弹窗（完整影响评估 + 触发指标）
│       │
│       └─ 2.3.3 调研追踪
│           ├─ 2.3.3.1 待调研问题清单（从缺口清单提取）
│           ├─ 2.3.3.2 调研记录（日期 / 对象 / 内容 / 结论）
│           └─ 2.3.3.3 下次跟踪提醒（根据跟踪周期自动计算）

├─ 3. 数据服务层 ──────────────────────────────────────────
│   ├─ 3.1 研报解析器
│   │   ├─ 3.1.1 Markdown 结构解析（识别章节/表格/YAML块）
│   │   ├─ 3.1.2 产业链表格提取 → 行业知识库
│   │   ├─ 3.1.3 投资逻辑提取（因果链/假设/信号）→ 投资看板
│   │   ├─ 3.1.4 跟踪指标表提取 → 边际追踪
│   │   └─ 3.1.5 事件提取（周度/月度报告中的 🟠🔴 事件）→ 事件时间线
│   │
│   ├─ 3.2 Claude API 代理
│   │   ├─ 3.2.1 Anthropic API 封装（Messages API + SSE 流式）
│   │   ├─ 3.2.2 System Prompt 构建（自动加载 Skills/Commands/MCP 工具列表）
│   │   └─ 3.2.3 会话管理（多会话 / 历史持久化 / 上下文窗口管理）
│   │
│   └─ 3.3 数据存储
│       ├─ 3.3.1 知识库存储（JSON 文件，按行业分目录）
│       ├─ 3.3.2 看板存储（JSON 文件，按标的存储多空逻辑+信号历史）
│       ├─ 3.3.3 追踪存储（JSON 文件，按标的分指标+事件）
│       └─ 3.3.4 会话存储（JSON 文件，对话历史）
│
└─ 4. 全局 ────────────────────────────────────────────────
    ├─ 4.1 导航系统（顶部固定导航栏 + 侧栏面包屑）
    ├─ 4.2 暗色主题（复用项目 CSS 变量，支持亮色切换）
    ├─ 4.3 响应式布局（桌面端三栏 / 平板两栏 / 手机单栏）
    └─ 4.4 数据刷新（手动刷新按钮 + 自动检测新报告）
```

---

## 二、技术架构

```
浏览器 (web/index.html)
    │
    ├─→ web/api/server.py (Flask, :8765)
    │       ├─ /api/chat          → Anthropic Messages API
    │       ├─ /api/parse-all     → 解析所有研报
    │       ├─ /api/knowledge/{industry}
    │       ├─ /api/theses/{symbol}
    │       ├─ /api/tracking/{symbol}
    │       └─ /api/sessions      → 会话管理
    │
    ├─→ Anthropic API (云端) / DeepSeek API
    │
    └─→ 本地文件系统
            ├─ reports/stocks/          ← 研报源（Markdown）
            ├─ reports/knowledge/        ← 解析后的知识库 (JSON)
            ├─ reports/theses/           ← 解析后的投资逻辑 (JSON)
            └─ reports/tracking/         ← 解析后的跟踪数据 (JSON)
```

**技术选型**：
- 前端：纯 HTML + CSS + Vanilla JS（零框架依赖）
- 后端：Python Flask（轻量，复用项目现有依赖）
- 图表：CSS 手绘（树形图、仪表盘、时间线），不引入 Chart.js
- Markdown 渲染：marked.js（CDN 加载，单个 JS 文件）
- 数据存储：JSON 文件（用户本地，不上传）

---

## 三、检查点

### 检查点 1：项目脚手架 + 后端 API 骨架

- [ ] 创建 `web/` 目录：`index.html`, `css/style.css`, `js/app.js`, `js/chat.js`, `js/workspace.js`, `api/server.py`, `api/parser.py`
- [ ] `web/index.html`：基础 HTML 骨架 + 暗色主题 CSS + 顶部导航（投研对话 | 研究员工作区）+ 两个 Tab 面板
- [ ] `web/css/style.css`：复用项目 CSS 变量，定义消息气泡、卡片、表格、按钮、标签、状态灯等基础样式
- [ ] `web/api/server.py`：Flask 应用（端口 8765），CORS 允许，`/api/health` 健康检查端点
- [ ] `web/api/server.py`：`/api/chat` 端点（POST），接收 `{message, history}`，调用 Anthropic/DeepSeek API 返回响应
- [ ] `web/api/server.py`：启动时自动加载 `skills/analysts/` 下所有 SKILL.md 构建 system prompt
- [ ] `requirements.txt` 新增 `flask`, `flask-cors`
- [ ] `python web/api/server.py` 可启动，`curl localhost:8765/api/health` 返回 200

---

### 检查点 2：投研对话 — 聊天界面

- [ ] `web/js/chat.js`：消息列表渲染（用户/AI 气泡、Markdown 转 HTML、代码高亮、表格样式）
- [ ] `web/js/chat.js`：输入框 + 发送按钮 + Enter 发送 + Shift+Enter 换行
- [ ] `web/js/chat.js`：流式 SSE 响应（逐字渲染 + 光标闪烁动画）
- [ ] `web/js/chat.js`：MCP 工具调用折叠面板（工具名/状态图标/耗时/展开查看详情）
- [ ] `web/js/app.js`：Subagent 进度条（4 个分析师并行进度模拟）
- [ ] 快捷命令按钮行：`/analyze-initial`, `/analyze-weekly`, `/analyze-quarterly`, `/beautify-report`, `/help`
- [ ] `web/css/style.css`：聊天界面全部样式
- [ ] `web/api/server.py`：`/api/chat` 改为 SSE 流式响应 + 新增 `/api/models` 端点

---

### 检查点 3：数据解析器

- [ ] `web/api/parser.py`：`ReportParser` 主类 — 接收文件路径，返回结构化 JSON
- [ ] `web/api/parser.py`：`extract_industry_chain()` — 解析 §1.1 产业链拆分（树形结构）
- [ ] `web/api/parser.py`：`extract_financial_table()` — 解析 §3 财务指标表（时间序列）
- [ ] `web/api/parser.py`：`extract_tam_cagr()` — 解析 §1.3 TAM/CAGR 数据
- [ ] `web/api/parser.py`：`extract_investment_thesis()` — 解析 §5 核心结论 + 因果链
- [ ] `web/api/parser.py`：`extract_signal_yaml()` — 解析 YAML 信号块
- [ ] `web/api/parser.py`：`extract_tracking_indicators()` — 解析 §5.5 跟踪指标清单
- [ ] `web/api/parser.py`：`extract_events()` — 从周度/月度报告中提取 🟠🔴 事件
- [ ] `web/api/server.py`：`/api/parse-all` 端点，遍历 `reports/stocks/` 全部返回
- [ ] `web/api/server.py`：`/api/parse/{symbol}` 端点，单标的解析

---

### 检查点 4：研究员工作区 — 行业知识库

- [ ] `web/js/workspace.js`：知识库 Tab 的 JS 逻辑
- [ ] `web/js/workspace.js`：左侧行业列表（从解析数据自动分组）
- [ ] `web/js/workspace.js`：右侧详情面板（产业链树形图 + TAM 卡片 + 财务基准表）
- [ ] `web/js/workspace.js`：行业卡片网格视图（概览模式）
- [ ] `web/js/workspace.js`：全文搜索 + 产业链定位搜索
- [ ] `web/css/style.css`：行业卡片、产业链树、数据卡片、搜索框样式
- [ ] `web/api/server.py`：`/api/knowledge/{industry}` 端点

---

### 检查点 5：研究员工作区 — 投资逻辑看板 + 边际变化追踪

- [ ] `web/js/workspace.js`：标的下拉选择器（搜索/筛选）
- [ ] `web/js/workspace.js`：多空逻辑面板（绿色多方卡片 + 红色空方卡片 + 验证状态标签）
- [ ] `web/js/workspace.js`：四维信号仪表盘（雷达图 + 信号方向 + 历史趋势）
- [ ] `web/js/workspace.js`：跟踪指标卡片网格（状态灯 + 趋势箭头 + 阈值触警高亮）
- [ ] `web/js/workspace.js`：事件时间线（🟠🔴 分级 + 筛选 + 详情弹窗）
- [ ] `web/js/workspace.js`：决策记录 + 待处理事项清单
- [ ] `web/css/style.css`：仪表盘、指标卡片、时间线、状态灯、弹窗样式
- [ ] `web/api/server.py`：`/api/theses/{symbol}`, `/api/tracking/{symbol}`, `/api/decisions/{symbol}` 端点

---

### 检查点 6：集成 + 测试 + 文档

- [ ] 端到端测试：`python web/api/server.py` → 打开 `web/index.html` → 全部 Tab 可用
- [ ] 使用已研报（002463/002119/601869/300502/002202/002414）验证解析器完整性
- [ ] 处理解析异常：空目录返回空数组，格式不兼容返回 warning 字段
- [ ] `docs/使用手册.md` 新增"Web 前端使用"章节
- [ ] `README.md` 新增 Web 前端启动说明
- [ ] `python tools/self-test.py` 新增 Web API 存活检查
- [ ] `.codex-claude/state.json` 更新为 phase: "completed"
