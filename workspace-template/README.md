# 投资研究工作区

这是 A股AI投研系统 的用户工作区。所有研究产出物和用户配置存放在此。

## 目录结构

```
workspace/
├── reports/
│   ├── 持仓组合.md           ← 当前持仓（持股数+平均成本，用户手动维护）
│   ├── 白名单组合.md          ← 覆盖标的及评级（用户手动维护）
│   ├── 黑名单组合.md          ← 排除标的（用户手动维护）
│   └── stocks/             ← 按标的归档（研究产出，自动生成）
│       └── [代码]-[名称]/
│           ├── 01-初次覆盖/
│           ├── 02-周度跟踪/
│           ├── 03-月度跟踪/
│           ├── 04-季度跟踪/
│           ├── 05-半年跟踪/
│           ├── 06-年度跟踪/
│           └── data/        ← 财务数据 CSV
├── tools/
│   └── md-to-html.py       ← 报告美化工具
└── .claude/
    └── settings.json        ← Claude Code 配置 (含API Key，勿提交Git)
```

## 使用方式

1. 复制此模板到你的工作目录
2. 配置 `.claude/settings.json`（参考 `.claude/settings.json.template`）
3. 在 `reports/白名单组合.md` 中添加覆盖标的
4. 在 `reports/持仓组合.md` 中记录实际持仓
5. 使用 `/analyze-initial [代码] [名称]` 开始初次覆盖
6. 完成后使用 `/beautify-report [代码]-[名称]` 生成 HTML 报告
