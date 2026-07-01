#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import py_compile
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_DIR / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
MCP_JSON = REPO_DIR / ".mcp.json"
SKILLS_DIR = REPO_DIR / "skills" / "analysts"
COMMANDS_DIR = REPO_DIR / "commands"

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

CORE_MCPS = ["finance-data", "tech-analysis"]
NEWS_MCPS = ["official-announcement", "macro-policy", "market-news", "industry-data"]
EXPECTED_SKILLS = {
    "analyst-chief",
    "analyst-fundamental",
    "analyst-chip-flow",
    "analyst-technical",
    "analyst-sentiment",
    "analyst-data-qa",
    "analyst-beautifier",
    "analyst-portfolio-manager",
    "analyst-archive",
    "analyst-daily",
}
EXPECTED_COMMANDS = [
    "analyze-initial",
    "analyze-weekly",
    "analyze-monthly",
    "analyze-quarterly",
    "analyze-annual",
    "analyze-portfolio-weekly",
    "analyze-daily",
    "archive-research",
    "beautify-report",
    "help",
]
CORE_TOOLS = [
    "archive-to-vault.py",
    "archive_schema.py",
    "archive_formatter.py",
    "archive_indexer.py",
    "archive_router.py",
    "archive_writer.py",
    "archive_validator.py",
    "daily_window.py",
    "daily_mcp_check.py",
    "daily_collect.py",
    "daily_score.py",
    "daily_report.py",
    "daily_to_vault.py",
    "sync-to-vault.py",
    "update-workspace.py",
    "md-to-html.py",
]


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    suffix = f" - {detail}" if detail else ""
    print(f"  {status} {label}{suffix}")
    return condition


def warn(label: str, detail: str = "") -> None:
    suffix = f" - {detail}" if detail else ""
    print(f"  {WARN} {label}{suffix}")


def load_mcp_config() -> dict:
    if not MCP_JSON.exists():
        return {}
    return json.loads(MCP_JSON.read_text(encoding="utf-8"))


def server_script(config: dict) -> Path | None:
    for arg in config.get("args", []):
        if isinstance(arg, str) and arg.endswith(".py"):
            path = Path(arg)
            return path if path.is_absolute() else REPO_DIR / path
    return None


def gate_mcp_config() -> bool:
    header("Gate 1: MCP 本地配置")
    ok = check("MCP 配置文件存在", MCP_JSON.exists(), str(MCP_JSON))
    config = load_mcp_config()
    servers = config.get("mcpServers", {})

    for name in CORE_MCPS + NEWS_MCPS:
        srv = servers.get(name)
        if not isinstance(srv, dict):
            ok = check(f"{name} 已配置", False, "未在 .mcp.json 中找到") and ok
            continue
        if srv.get("disabled"):
            ok = check(f"{name} 未禁用", False, "当前被 disabled") and ok
        else:
            check(f"{name} 已启用", True)
        command = Path(srv.get("command", ""))
        ok = check(f"{name} Python 命令存在", command.exists(), str(command)) and ok
        script = server_script(srv)
        if not script:
            ok = check(f"{name} server.py", False, "args 中未找到 Python 脚本") and ok
            continue
        ok = check(f"{name} server.py 存在", script.exists(), str(script)) and ok
        if script.exists():
            try:
                py_compile.compile(str(script), doraise=True)
                check(f"{name} server.py 语法", True)
            except py_compile.PyCompileError as exc:
                ok = check(f"{name} server.py 语法", False, str(exc)[:160]) and ok

    return ok


def gate_skills_and_commands() -> bool:
    header("Gate 2: Skills 与命令入口")
    ok = True
    existing_skills = {
        path.name for path in SKILLS_DIR.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    } if SKILLS_DIR.exists() else set()

    for name in sorted(EXPECTED_SKILLS):
        ok = check(f"Skill: {name}", name in existing_skills) and ok

    for name in sorted(existing_skills):
        content = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")
        if name == "analyst-daily":
            if "MCP 调用方式" not in content or "四轮采集" not in content:
                warn("analyst-daily 流程说明", "建议包含 MCP 调用方式和四轮采集")
        elif name not in {"analyst-beautifier", "analyst-chief", "analyst-portfolio-manager"}:
            if "数据源优先级" not in content and "MCP" not in content:
                warn(f"{name} 数据源规则", "建议明确 MCP / Web / 本地数据优先级")
        if "Subagent" not in content and name.startswith("analyst-"):
            warn(f"{name} 角色指令", "建议明确是否作为独立 Subagent 执行")

    for name in EXPECTED_COMMANDS:
        ok = check(f"Command: {name}", (COMMANDS_DIR / f"{name}.md").exists()) and ok

    return ok


def gate_python_tools() -> bool:
    header("Gate 3: Python 工具语法")
    ok = True
    for name in CORE_TOOLS:
        path = REPO_DIR / "tools" / name
        if not path.exists():
            ok = check(f"tools/{name}", False, "文件不存在") and ok
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            check(f"tools/{name}", True)
        except py_compile.PyCompileError as exc:
            ok = check(f"tools/{name}", False, str(exc)[:160]) and ok

    for path in [REPO_DIR / "web" / "api" / "parser.py", REPO_DIR / "web" / "api" / "report_parser.py"]:
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
                check(path.relative_to(REPO_DIR).as_posix(), True)
            except py_compile.PyCompileError as exc:
                ok = check(path.relative_to(REPO_DIR).as_posix(), False, str(exc)[:160]) and ok
        else:
            warn(path.relative_to(REPO_DIR).as_posix(), "不存在，旧解析兼容路径不可用")
    return ok


def gate_daily_local() -> bool:
    header("Gate 4: 日报本地链路")
    ok = True
    try:
        from daily_window import daily_window, parse_date
        window = daily_window(parse_date("2026-07-01"))
        ok = check(
            "日报时间窗口",
            window["window_start"] == "2026-06-30 00:00:00"
            and window["window_end"] == "2026-07-01 23:59:59",
            f"{window['window_start']} ~ {window['window_end']}",
        ) and ok
    except Exception as exc:
        ok = check("日报时间窗口", False, str(exc)[:160]) and ok

    try:
        from daily_mcp_check import check_mcp_config
        status = check_mcp_config()
        ok = check("新闻 MCP 本地体检", bool(status.get("all_scripts_ok"))) and ok
    except Exception as exc:
        ok = check("新闻 MCP 本地体检", False, str(exc)[:160]) and ok
    return ok


def gate_vault_health() -> bool:
    header("Gate 5: Vault 健康检查")
    ok = True
    sample_paths = [
        REPO_DIR / "obsidian-vault" / "个股逻辑" / "002463-沪电股份" / "_index.md",
        REPO_DIR / "obsidian-vault" / "个股逻辑" / "002463-沪电股份" / "基本面.md",
        REPO_DIR / "obsidian-vault" / "个股逻辑" / "002463-沪电股份" / "投资决策.md",
        REPO_DIR / "obsidian-vault" / "跟踪面板" / "002463-沪电股份.md",
        REPO_DIR / "obsidian-vault" / "行业知识库" / "AI服务器PCB.md",
    ]
    for path in sample_paths:
        if not path.exists():
            warn(path.relative_to(REPO_DIR).as_posix(), "回归样本不存在")
            continue
        text = path.read_text(encoding="utf-8")
        has_marker = "<!-- /ai-content -->" in text
        no_deprecated = "原文摘录：" not in text and "[!quote] 来源" not in text and "???" not in text
        ok = check(path.relative_to(REPO_DIR).as_posix(), has_marker and no_deprecated) and ok

    legacy_hits = []
    vault = REPO_DIR / "obsidian-vault"
    if vault.exists():
        for path in vault.rglob("*.md"):
            text = path.read_text(encoding="utf-8", errors="replace")
            if "原文摘录：" in text or "[!quote] 来源" in text or "???" in text:
                legacy_hits.append(path.relative_to(REPO_DIR).as_posix())
    if legacy_hits:
        warn("Vault 历史遗留内容", f"{len(legacy_hits)} 个文件仍含废弃来源包装或乱码标记")
    else:
        check("Vault 无废弃来源包装", True)
    return ok


def gate_online_connectivity() -> bool:
    header("Optional Gate: 在线数据连通")
    ok = True
    try:
        import akshare as ak
        df = ak.stock_zh_a_hist(symbol="002202", period="daily", start_date="20260101", end_date="20260617", adjust="qfq")
        ok = check("AKShare 行情连通", df is not None and not df.empty) and ok
    except Exception as exc:
        ok = check("AKShare 行情连通", False, str(exc)[:160]) and ok

    try:
        import akshare as ak
        fin = ak.stock_financial_abstract_ths(symbol="002202", indicator="按报告期")
        ok = check("同花顺财务连通", fin is not None and not fin.empty) and ok
    except Exception as exc:
        ok = check("同花顺财务连通", False, str(exc)[:160]) and ok
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="A股AI投研系统本地自测。默认不做联网数据连通。")
    parser.add_argument("--online", action="store_true", help="同时测试 AkShare / 东方财富 / 同花顺等在线数据源。")
    args = parser.parse_args()

    print("=" * 60)
    print("  A股AI投研系统 - 本地自测")
    print("=" * 60)
    print(f"  Repo: {REPO_DIR}")
    print(f"  MCP Config: {MCP_JSON}")

    results = {
        "MCP 本地配置": gate_mcp_config(),
        "Skills 与命令入口": gate_skills_and_commands(),
        "Python 工具语法": gate_python_tools(),
        "日报本地链路": gate_daily_local(),
        "Vault 健康检查": gate_vault_health(),
    }
    if args.online:
        results["在线数据连通"] = gate_online_connectivity()

    header("自测结果")
    passed = sum(1 for value in results.values() if value)
    total = len(results)
    for name, value in results.items():
        print(f"  {PASS if value else FAIL} {name}")
    print(f"\n  通过: {passed}/{total}")
    if not args.online:
        print("  注：默认自测不检查外部网络数据源；需要时运行 `python tools/self-test.py --online`。")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
