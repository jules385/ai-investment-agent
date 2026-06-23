# 测试任务: v0.2.0 前端验收测试

服务器已在 `http://127.0.0.1:8765` 运行（DeepSeek API 已配置）。

## 🔄 执行流程（每次一个测试，逐项进行）

🔴 **每次只执行 state.json 中标记为 `pending` 的那一个测试用例。执行完后立即更新 state.json 为 `pending_review`，等待 Claude 审查。Claude 审查通过后，state.json 会自动推进到下一个测试。Claude 审查不通过时，会给出修复指令——你修复后重新执行同一个测试，再次提交。**

**不要**一次性执行全部测试。一项一项来。

---

## 测试用例清单

### 测试 A1：健康检查
- 操作：`curl http://127.0.0.1:8765/api/health`
- 预期：返回 `{"status":"ok"}`，HTTP 200
- 报告格式：实际响应内容 + 状态码 + PASS/FAIL

### 测试 A2：模型列表
- 操作：`curl http://127.0.0.1:8765/api/models`
- 预期：返回包含模型名的数组，HTTP 200
- 报告格式：实际响应内容 + PASS/FAIL

### 测试 A3：工作区空数据
- 操作：`curl http://127.0.0.1:8765/api/workspace`
- 预期：返回 `{"industries":{},"theses":{},"tracking":{}}` 或非空数据结构，HTTP 200
- 报告格式：实际响应内容 + PASS/FAIL

### 测试 B1：投研对话 — 基础消息
- 操作：`curl -X POST http://127.0.0.1:8765/api/chat -H "Content-Type: application/json" -d '{"message":"你好，请简单介绍一下你自己"}'`
- 预期：返回流式或非流式 AI 回复，HTTP 200。回复内容应包含与"AI投研助手"相关的介绍
- 报告格式：回复内容摘要 + 是否获得有效回复 + PASS/FAIL

### 测试 B2：投研对话 — 命令按钮
- 操作：在前端页面点击快捷命令按钮 `/analyze-initial` 和 `/help`
- 预期：输入框被自动填入对应命令
- 报告格式：描述按钮行为 + PASS/FAIL（需说明你是如何验证的）

### 测试 C1：AI 数据解析
- 操作：`curl -X POST http://127.0.0.1:8765/api/parse-all`
- 预期：返回 JSON，`stocks_parsed` >= 1，HTTP 200
- 报告格式：`stocks_parsed` 值 + 解析出的行业名称 + PASS/FAIL

### 测试 D1：工作区 — 行业知识库数据
- 操作：`curl http://127.0.0.1:8765/api/workspace`
- 预期：`industries` 字段非空，包含行业名称和对应的产业链/TAM/财务数据
- 报告格式：`industries` 包含的行业列表 + 每个行业的数据完整性 + PASS/FAIL

### 测试 D2：工作区 — 投资逻辑数据
- 操作：同上，检查 `theses` 字段
- 预期：`theses` 包含至少一个标的（如 002463）的多空逻辑、信号、关键假设
- 报告格式：`theses` 包含的标的列表 + 每个标的的 bull_theses/bear_theses/signals 是否填充 + PASS/FAIL

### 测试 D3：工作区 — 跟踪指标数据
- 操作：同上，检查 `tracking` 字段
- 预期：`tracking` 包含至少一个标的的 indicators、events
- 报告格式：`tracking` 包含的标的列表 + indicators 数量 + PASS/FAIL

### 测试 E1：调研记录提交
- 操作：`curl -X POST http://127.0.0.1:8765/api/research-note -H "Content-Type: application/json" -d '{"symbol":"002463","note":"6月24日调研：公司AI板出货量继续增长，毛利率维持在35%以上，产能利用率95%"}'`
- 预期：返回 HTTP 200，响应中包含更新后的 indicators 和 events
- 报告格式：响应内容 + indicators/events 是否有变化 + PASS/FAIL

### 测试 E2：前端页面加载
- 操作：用浏览器或 HTTP 请求打开 `web/index.html`
- 预期：页面可正常加载，包含两个 Tab（投研对话 | 研究员工作区）
- 报告格式：页面是否可访问 + Tab 是否存在 + PASS/FAIL

---

## 📋 每次执行后的操作

1. 将当前测试的执行结果追加写入 `.codex-claude/reviews/test-report.md`（追加模式，不要覆盖之前的记录）
2. 更新 `.codex-claude/state.json`：
   - `checkpoint_status: "pending_review"`
   - 将本次测试用例的执行记录追加到 `history`
3. 输出："测试 [X] 已执行。结果已写入 test-report.md。请 Claude 审查。"

---

**开始执行 state.json 中标记为 pending 的第一个测试用例。**
