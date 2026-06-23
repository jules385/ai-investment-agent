# Codex 执行指令

你是本项目的执行者。Claude 是架构师和审查者——Claude 永不写代码，只审查你的产出。

## 项目简介

A股AI投研系统 v0.2.0 — 基于多智能体架构的二级市场投资研究平台。
v0.1.0 已完成并发布在 GitHub（jules385/ai-investment-agent）。
v0.2.0 的任务是**在此基础上新增 HTML 前端界面**，不修改已有系统。

技术栈：Python 3.10+, MCP 协议, AKShare, ta, pandas, numpy, Flask（v0.2.0新增）

## 工作流程（批量执行模式）

> 🔴 `auto_advance: true` — 你从检查点 1 一直跑到检查点 5，中途不停止。全部完成后 Claude 一次性审查。

**执行步骤**：

1. 读取 `.codex-claude/plan.md` → 获取全部 5 个检查点
2. 读取 `.codex-claude/state.json` → 确认从检查点 1 开始
3. 从检查点 1 开始，**依次执行全部 5 个检查点**：
   - 每个检查点完成后 → `git add` + `git commit`（格式：`feat(checkpoint-N): 描述`）
   - 更新 `state.json` 中的 `current_checkpoint` → 立即开始下一个检查点
   - **不要**在检查点之间等待 Claude 审查
4. 全部 5 个检查点完成后：
   - 更新 `state.json`：`phase: "pending_review"`
   - 输出："全部 5 个检查点已完成。git log 如下：[...]。请 Claude 审查。"

---

## 已存在文件清单（v0.1.0 — 不要修改，除非检查点明确要求）

### 根目录（11个文件）

| 文件 | 作用 | v0.2.0 能否改 |
|------|------|:--:|
| `README.md` | 项目首页文档 | ❌ 检查点5可改 |
| `LICENSE` | MIT 协议 | ❌ |
| `CHANGELOG.md` | 版本更新日志 | ❌ |
| `CODE_OF_CONDUCT.md` | 行为准则 | ❌ |
| `CONTRIBUTING.md` | 贡献指南 | ❌ |
| `SECURITY.md` | 安全政策 | ❌ |
| `VERSION` | 版本号 `0.2.0` | ❌ |
| `.gitignore` | Git 排除规则 | ❌ |
| `requirements.txt` | Python 依赖 | ✅ 检查点1新增 flask |
| `install.py` | 一键安装脚本 | ❌ |
| `.mcp.json.template` | MCP 配置模板 | ❌ |

### `skills/analysts/` — 8 个 AI 角色 Skill（Markdown + YAML frontmatter）

| 文件 | 角色 | v0.2.0 能否改 |
|------|------|:--:|
| `analyst-chief/SKILL.md` | 总分析师（编排器）— 6 周期执行流程 | ❌ |
| `analyst-fundamental/SKILL.md` | 基本面分析师 — 4 种模式（深度/季度三表联动/月度趋势提炼/周度边际监控） | ❌ |
| `analyst-chip-flow/SKILL.md` | 筹码面分析师 — 3 种模式（深度/月度趋势汇总/周度快速扫描） | ❌ |
| `analyst-technical/SKILL.md` | 技术面分析师 — 3 种模式（深度/月度趋势确认/周度日线+60分钟） | ❌ |
| `analyst-sentiment/SKILL.md` | 情绪面分析师 — 3 种模式（深度/月度温度曲线/周度速览） | ❌ |
| `analyst-data-qa/SKILL.md` | 数据分析师 — QA 通行证 YAML 输出 | ❌ |
| `analyst-beautifier/SKILL.md` | AI 美化师 — Markdown→HTML + 可视化增强 | ❌ |
| `analyst-portfolio-manager/SKILL.md` | 组合管理员 — 三个组合文件的研究记录维护 | ❌ |

**这些是系统的核心**。v0.2.0 的前端通过 `web/api/server.py` 读取它们构建 system prompt，但不修改内容。

### `commands/` — 8 条斜杠命令（Markdown）

| 文件 | v0.2.0 能否改 |
|------|:--:|
| `analyze-initial.md`, `analyze-weekly.md`, `analyze-monthly.md`, `analyze-quarterly.md`, `analyze-annual.md`, `analyze-portfolio-weekly.md`, `beautify-report.md`, `help.md` | ❌ |

### `mcp-servers/` — 2 个 MCP Server（Python, stdio 通信）

| 文件 | 工具数 | v0.2.0 能否改 |
|------|:--:|:--:|
| `finance-data/server.py` | 15 个工具（财务/估值/股东/资金流/龙虎榜/融资融券/北向/筹码/三张完整报表） | ❌ |
| `tech-analysis/server.py` | 10 个工具（MA/MACD/RSI/KDJ/布林/ATR/量价/形态/支撑阻力/评分） | ❌ |

**这些是系统的数据管道**。v0.2.0 的前端通过 Claude API 间接使用 MCP 工具（Claude 自己调用），不直接调用 MCP Server。

### `tools/` — 2 个辅助脚本

| 文件 | 作用 | v0.2.0 能否改 |
|------|------|:--:|
| `md-to-html.py` | Markdown→HTML 报告生成器 + 可视化增强 | ❌ |
| `self-test.py` | 5 关自动化环境验证 | ✅ 检查点5新增 Web API 检查 |

### `knowledge/` — 知识库（纯文档，不参与执行）

| 文件 | v0.2.0 能否改 |
|------|:--:|
| `增长逻辑分析方法手册.md` + `workflows/` 下 6 个方法论文档 | ❌ |

### `docs/` — 文档

| 文件 | v0.2.0 能否改 |
|------|:--:|
| `使用手册.md` | ✅ 检查点5新增 Web 章节 |
| `产品手册.html` | ❌ |
| `CODEX适配指南.md` | ❌ |

### `workspace-template/` — 用户工作区模板

| 内容 | v0.2.0 能否改 |
|------|:--:|
| `reports/持仓组合.md`, `白名单组合.md`, `黑名单组合.md` + `tools/md-to-html.py` | ❌ |

### `reports/` — 用户数据（不进入 Git，仅在本地磁盘）

| 目录 | 内容 |
|------|------|
| `reports/stocks/002463-沪电股份/` ~ `300857-协创数据/` | 8 个标的的完整研报（初次覆盖 + 子报告） |
| `reports/stocks/002463-沪电股份/04-季度跟踪/` | 季度跟踪报告 |
| `reports/stocks/002463-沪电股份/02-周度跟踪/` | 周度跟踪报告（5 标的） |

**v0.2.0 的数据解析器会读取这些研报**，从中提取产业链/财务/指标/事件数据填充工作区。

### `.codex-claude/` — 开发协作配置（v0.2.0 新增）

| 文件 | v0.2.0 能否改 |
|------|:--:|
| `config.yaml`, `plan.md`, `codex-prompt.md`, `review-prompt.md`, `state.json` | ❌（Claude 管理） |

---

## v0.2.0 新增范围

**只需要创建 `web/` 目录下的文件**，以及修改以下已有文件：

| 文件 | 修改内容 | 检查点 |
|------|---------|:--:|
| `requirements.txt` | 新增 `flask`, `flask-cors` | 1 |
| `docs/使用手册.md` | 新增 Web 前端章节 | 5 |
| `README.md` | 新增 Web 启动说明 | 5 |
| `tools/self-test.py` | 新增 Web API 检查 | 5 |

**不要修改上述以外的任何已有文件。**

---

## 代码规范

- 前端：纯 HTML + CSS + Vanilla JS，零框架依赖。marked.js 通过 CDN 加载
- 后端：Python Flask，端口 8765
- CSS：复用项目暗色主题 CSS 变量（`--bg:#0f1117` / `--card:#1a1d28` / `--bor:#2a2d3a` / `--tx:#c9d1d9` / `--hl:#f0f6fc` / `--bl:#58a6ff` / `--gn:#3fb950` / `--rd:#f85149` / `--yl:#d2991d`）
- 数据存储：单个 JSON 文件 `reports/workspace-data.json`，不要引入数据库
- 所有 Python 文件使用 `pathlib.Path`，不要硬编码绝对路径

---

## API 配置指南

### API Key 来源（优先级从高到低）

1. 环境变量 `ANTHROPIC_API_KEY` 或 `DEEPSEEK_API_KEY`
2. `~/.claude/settings.json` → `env.ANTHROPIC_AUTH_TOKEN`
3. 项目根目录 `.env` 文件（不会被 Git 追踪）

Codex 在 `server.py` 中按此顺序查找。找不到时 → 返回 401 + 友好提示"请配置 API Key"。

### System Prompt 构建

`server.py` 启动时执行一次：

```
system_prompt = ""
for each skill in skills/analysts/*/SKILL.md:
    读取 YAML frontmatter → 提取 name + description
    读取正文 → 提取角色指令
    system_prompt += f"## {name}\n{role_instruction}\n\n"
system_prompt += "你是 A股AI投研系统 的 AI 助手。你可以使用 MCP 工具获取实时数据。"
```

不要加载 `knowledge/` 目录下的文件——那些是方法论参考，不是角色指令。

### MCP 工具发现

前端不直接调用 MCP Server。前端通过 `/api/chat` 发送消息，Claude API 自己根据 system prompt 和用户消息决定调用哪些 MCP 工具。Codex 不需要在代码中列出 MCP 工具清单——Claude 会自己从 `.mcp.json` 中发现它们。

---

## 数据解析器：Markdown 章节识别规则

`web/api/parser.py` 解析 `reports/stocks/` 下的研报时，使用以下模式匹配章节：

| 目标内容 | Markdown 章节特征 | 解析方式 |
|---------|-----------------|---------|
| 产业链拆分 | `### 1.1 产业链拆分` + 行首有 `├──` `└──` `│` 的树形块 | 按行解析树形结构 → JSON |
| 市场空间 | `#### 1.3 市场空间` 或含 `TAM`/`SAM`/`CAGR` 的表格 | 提取表格行 → JSON 数组 |
| 财务指标 | `## 三、财务` 或 `### 3.1` 下的 5年×N列表格 | 提取表头+数据行 → 时间序列 JSON |
| 投资逻辑 | `## 五、结论` 或 `### 5.` 下的因果链段落 + `signal:` YAML 块 | 提取文本 + 解析 YAML |
| 跟踪指标 | `### 5.5 跟踪指标清单` 或 `跟踪指标` 表格 | 提取表格，识别每行的阈值列 |
| 事件 | 周度/月度报告中 `### 本周事件` 或 `| 🔴` `| 🟠` 开头的表格行 | 提取日期/等级/描述 |

**容错规则**：
- 找不到某章节 → 返回空数组 `[]`，不崩溃
- 表格列数变化（不同报告格式不同）→ 用表头行匹配，不用硬编码列索引
- YAML 块解析失败 → 返回 `{raw: "原始文本", parsed: false}`
- 旧格式报告（v0.1.0 之前的初次覆盖报告可能缺 §5.5）→ 标注 `format: "legacy"`，尽可能提取能提取的

---

## 空状态和错误处理

每个前端组件必须处理以下状态：

| 状态 | 触发条件 | 展示 |
|------|---------|------|
| **加载中** | 正在 fetch API | 骨架屏或 loading spinner |
| **空数据** | API 返回空数组/空对象 | 友好的空状态提示："暂无数据，完成初次覆盖后自动填充" |
| **API 错误** | 网络断开/500/401 | Toast 通知 + 不崩溃 + 保留上次成功加载的数据 |
| **解析失败** | parser 返回 error 字段 | 在对应卡片上显示 ⚠️ 图标 + 悬浮提示错误原因 |

**特别处理**：
- `workspace-data.json` 不存在时 → 返回初始空结构 `{"industries":{},"theses":{},"tracking":{}}`
- `reports/stocks/` 下无任何研报时 → `/api/parse-all` 返回 `stocks_parsed: 0, message: "未找到研报文件"`
- 用户未配置 API Key 时 → `/api/chat` 返回 401 + `{"error": "请配置 API Key（设置环境变量或编辑 ~/.claude/settings.json）"}`

---

## 批量审查失败后的重试流程

当 Claude 批量审查全部 5 个检查点后给出审查报告：

1. 阅读 `.codex-claude/reviews/` 下最新的审查报告
2. 关注每个检查点的 `urgent` 数组——按检查点分组，逐项修复
3. 只修复未通过（`passed: false`）的检查点，不要重做已通过的
4. 修复后 `git add` + `git commit`（格式：`fix: 修复审查问题 — [检查点N] [问题简述]`）
5. 更新 `state.json` 中的 `pending_issues` 为 0
6. 再次输出："全部修复完成。请 Claude 重新审查。"

每轮审查最多 5 轮（`config.yaml` 中 `max_review_rounds: 5`）。5 轮仍不通过 → 暂停。

---

## 提交格式

```
feat: 新增XX功能
fix: 修复XX问题
refactor: 重构XX模块
docs: 更新XX文档
test: 添加XX测试
```
