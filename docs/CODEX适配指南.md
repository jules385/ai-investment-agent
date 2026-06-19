# Codex 适配指南

本文档供 OpenAI Codex CLI 阅读和执行。目标：将本项目的 Claude Code 专属入口层适配为 Codex 原生格式，底层全部复用。

---

## 一、你可以直接复用的（无需任何改动）

以下目录和文件与 Claude Code 无关，直接可用：

```
mcp-servers/           ← 2 个 MCP Server（纯 Python + MCP 协议）
tools/                 ← md-to-html.py, self-test.py（独立脚本）
knowledge/             ← 方法论手册 + 工作流设计文档
docs/                  ← 产品手册 + 使用手册
workspace-template/    ← 用户工作区模板
requirements.txt       ← Python 依赖
```

**关键**：MCP 是开放标准协议，Codex 原生支持。你只需要让 Codex 读取本项目根目录下的 `.mcp.json`，两个 MCP Server 就能正常工作。

---

## 二、你需要重写的（Claude Code 专属部分）

以下文件使用 Claude Code 的 Skill/Command/Agent 机制，Codex 不支持，需要你自行重写：

### 2.1 `skills/analysts/` → Codex Agent 定义

Claude Code 的 Skill 文件使用 YAML frontmatter + Markdown 指令。你需要将每个 Skill 改写为 Codex 的 Agent 定义格式。

**你需要读取并理解以下 8 个 SKILL.md 的角色指令，然后为每个角色创建对应的 Codex Agent**：

| Claude Code Skill | 角色 | 核心能力 |
|------|------|------|
| `analyst-chief/SKILL.md` | 总分析师（编排器） | 判断周期 → 并行启动4个分析师 → 强制QA → 合成报告。**禁止自己搜数据或调MCP** |
| `analyst-fundamental/SKILL.md` | 基本面分析师 | 4 种模式：深度（五步法）/ 季度（三表联动）/ 月度（趋势提炼）/ 周度（边际监控） |
| `analyst-chip-flow/SKILL.md` | 筹码面分析师 | 3 种模式：深度（五步法）/ 月度（趋势汇总）/ 周度（快速扫描） |
| `analyst-technical/SKILL.md` | 技术面分析师 | 3 种模式：深度（五周期）/ 月度（趋势确认）/ 周度（日线+60分钟） |
| `analyst-sentiment/SKILL.md` | 情绪面分析师 | 3 种模式：深度（五步）/ 月度（温度曲线）/ 周度（速览） |
| `analyst-data-qa/SKILL.md` | 数据分析师（QA） | 读取报告文件 → 逐条扫描观点 → MCP交叉验证 → 补充缺口 → 输出通行证YAML |
| `analyst-beautifier/SKILL.md` | AI美化师 | 运行 `python tools/md-to-html.py [代码]-[名称]` 生成 HTML 报告 |
| `analyst-portfolio-manager/SKILL.md` | 组合管理员 | 读取三个组合文件 → 追加研究记录 → 更新跟踪状态 |

**适配要点**：
- 每个 Skill 的 `trigger:` 字段是 Claude Code 的触发词机制，Codex 不需要——你改为 Codex 的指令匹配或 Agent 路由
- Skill 中所有对 MCP 工具的引用（如 `get_financial_indicators`）保持不变——MCP Server 是共用的
- Skill 中的 `🔴 强制` / `不可跳过` 等约束词保留，确保 Agent 行为一致

### 2.2 `commands/` → Codex 指令或 Slash Command

Claude Code 的命令文件是斜杠命令入口。你需要将其改写为 Codex 的指令格式：

| Claude Code Command | 功能 | 改写要点 |
|------|------|------|
| `analyze-initial.md` | 初次覆盖 | 指令内容就是一句话：加载总分析师 Agent，传参（标的代码+名称+周期=初次覆盖） |
| `analyze-weekly.md` | 周度跟踪 | 同上，周期=周度。支持两种调用：指定标的 / 遍历白名单组合 |
| `analyze-monthly.md` | 月度跟踪 | 同上，周期=月度 |
| `analyze-quarterly.md` | 季度跟踪 | 同上，周期=季度 |
| `analyze-annual.md` | 年度跟踪 | 同上，周期=年度 |
| `analyze-portfolio-weekly.md` | 组合批量周度跟踪 | 同上，周期=批量周度 |
| `beautify-report.md` | 生成 HTML | 硬编码指令：`python tools/md-to-html.py [代码]-[名称]` |
| `help.md` | 命令速查 | 纯展示文本，无需改写 |

**适配要点**：
- Claude Code 命令通过文件系统自动加载。Codex 的等效机制可能不同——你需要根据 Codex 的指令系统选择实现方式
- 所有命令的核心逻辑都一样：加载 @analyst-chief Agent，告诉它标的、名称、周期，然后让它自己编排

### 2.3 Chief Agent 的 `Agent()` 调用 → Codex Agent SDK

这是最关键的适配点。Claude Code 的 Chief Skill 使用 `Agent(subagent_type='claude', ...)` 工具来 spawn 子分析师。Codex 有自己等效的机制。你需要让 Chief Agent 能够：

1. **并行启动 4 个分析师 Agent**——这是性能关键。如果串行启动，一次初次覆盖将耗时 4 倍
2. **向每个 Agent 传递文件保存路径**——子分析师完成分析后自己写入磁盘
3. **等待所有 Agent 返回**——验证文件完整性后再进入 QA

---

## 三、MCP Server 连接

Codex 支持 MCP 协议。确保 `.mcp.json` 在项目根目录下（`install.py` 已自动生成）。

两个 MCP Server 需要以下 Python 包：

```bash
pip install -r requirements.txt
```

验证命令：

```bash
python tools/self-test.py
```

预期输出 5/5 全部通过。如果某个 MCP Server 启动失败，通常是 Python 包缺失或路径问题。

---

## 四、工作流执行链路

无论 Claude Code 还是 Codex，核心执行链路不变：

```
用户触发分析
    │
    ▼
总分析师 Agent 判断周期
    │
    ▼
并行启动 4 个分析师 Agent ──→ 各自调用 MCP + WebSearch ──→ 自行写入磁盘
    │
    ▼
总分析师验证文件 → 并行启动 4 个 QA Agent ──→ 各返回通行证
    │
    ▼
总分析师合成 → 写入 Markdown
    │
    ▼
用户说"美化" → beautifier 运行 md-to-html.py → HTML 报告
```

你只需要让这 9 个 Agent（1 Chief + 4 分析师 + 4 QA）按照上述链路协作。每个 Agent 的详细指令已经在对应的 SKILL.md 文件中，你翻译成 Codex Agent 格式即可。

---

## 五、目录结构（Codex 版建议）

```
ai-investment-agent/
├── mcp-servers/           ← 直接复用，不改
├── tools/                 ← 直接复用，不改
├── knowledge/             ← 直接复用，不改
├── docs/                  ← 直接复用，不改
├── workspace-template/    ← 直接复用，不改
├── requirements.txt       ← 直接复用，不改
├── .mcp.json              ← 直接复用，不改
│
├── codex-agents/          ← 新增：Codex 版 Agent 定义（替代 skills/analysts/）
│   ├── chief.md
│   ├── fundamental.md
│   ├── chip-flow.md
│   ├── technical.md
│   ├── sentiment.md
│   ├── data-qa.md
│   ├── beautifier.md
│   └── portfolio-manager.md
│
└── codex-commands/        ← 新增：Codex 版指令（替代 commands/）
    ├── analyze-initial.md
    ├── analyze-weekly.md
    ├── analyze-monthly.md
    ├── analyze-quarterly.md
    ├── analyze-annual.md
    ├── analyze-portfolio-weekly.md
    ├── beautify-report.md
    └── help.md
```

---

## 六、你不需要改的

- **MCP 工具名**：所有 Agent 指令中引用的 `get_financial_indicators`、`compute_ma` 等工具名保持不变
- **文件路径**：所有 `reports/stocks/[代码]-[名称]/...` 路径保持不变
- **分析流程**：初次覆盖 5 步法、季度 7 步三表联动、月度 4 周趋势提炼等逻辑全部不变
- **输出格式**：Markdown + HTML 双格式不变
- **QA 机制**：通行证 YAML 格式不变
- **升级/降级规则**：决策规则不变
