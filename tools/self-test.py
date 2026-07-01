#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import py_compile
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_DIR / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

LOCAL_MCP_JSON = REPO_DIR / ".mcp.json"
TEMPLATE_MCP_JSON = REPO_DIR / ".mcp.json.template"
SKILLS_DIR = REPO_DIR / "skills" / "analysts"
COMMANDS_DIR = REPO_DIR / "commands"

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

REQUIRED_IMPORTS = {
    "akshare": "akshare",
    "ta": "ta",
    "mcp": "mcp",
    "fastmcp": "fastmcp",
    "pandas": "pandas",
    "numpy": "numpy",
    "markdown": "markdown",
}

ACTIVE_MCPS = [
    "finance-data",
    "tech-analysis",
    "official-announcement",
    "macro-policy",
    "market-news",
    "industry-data",
]

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

ACTIVE_TOOLS = [
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


def read_mcp_config() -> tuple[Path | None, dict, bool]:
    if LOCAL_MCP_JSON.exists():
        return LOCAL_MCP_JSON, json.loads(LOCAL_MCP_JSON.read_text(encoding="utf-8")), False
    if TEMPLATE_MCP_JSON.exists():
        return TEMPLATE_MCP_JSON, json.loads(TEMPLATE_MCP_JSON.read_text(encoding="utf-8")), True
    return None, {}, False


def normalize_template_path(value: str) -> str:
    return value.replace("{{REPO_PATH}}", str(REPO_DIR)).replace("\\", "/")


def server_script(config: dict) -> Path | None:
    for arg in config.get("args", []):
        if isinstance(arg, str) and arg.endswith(".py"):
            arg = normalize_template_path(arg)
            path = Path(arg)
            return path if path.is_absolute() else REPO_DIR / path
    return None


def import_file(path: Path, module_name: str) -> None:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot create import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


def gate_dependencies() -> bool:
    header("Gate 1: Python 依赖")
    ok = True
    for label, module_name in REQUIRED_IMPORTS.items():
        try:
            importlib.import_module(module_name)
            check(label, True)
        except Exception as exc:
            ok = check(label, False, f"{type(exc).__name__}: {exc}") and ok
    return ok


def gate_mcp_config() -> bool:
    header("Gate 2: MCP 配置与服务器入口")
    ok = True
    config_path, config, using_template = read_mcp_config()
    ok = check("MCP 配置文件存在", config_path is not None, str(config_path or LOCAL_MCP_JSON)) and ok
    if not config_path:
        return False
    if using_template:
        warn(".mcp.json 未创建", "当前按 .mcp.json.template 检查；真实使用前需复制并替换 Python/项目路径")

    servers = config.get("mcpServers", {})
    for name in ACTIVE_MCPS:
        srv = servers.get(name)
        if not isinstance(srv, dict):
            ok = check(f"{name} 已配置", False, "mcpServers 中缺失") and ok
            continue
        ok = check(f"{name} 未禁用", not srv.get("disabled", False)) and ok

        command = str(srv.get("command", ""))
        if using_template and "{{PYTHON_PATH}}" in command:
            check(f"{name} Python 命令", True, "template placeholder")
        else:
            ok = check(f"{name} Python 命令存在", Path(command).exists(), command) and ok

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
                ok = check(f"{name} server.py 语法", False, str(exc)[:180]) and ok
            try:
                import_file(script, f"selftest_{name.replace('-', '_')}")
                check(f"{name} server.py 顶层导入", True)
            except Exception as exc:
                ok = check(f"{name} server.py 顶层导入", False, f"{type(exc).__name__}: {exc}") and ok
    return ok


def gate_skills_and_commands() -> bool:
    header("Gate 3: Skills 与命令入口")
    ok = True
    existing_skills = (
        {path.name for path in SKILLS_DIR.iterdir() if path.is_dir() and (path / "SKILL.md").exists()}
        if SKILLS_DIR.exists()
        else set()
    )

    for name in sorted(EXPECTED_SKILLS):
        ok = check(f"Skill: {name}", name in existing_skills) and ok

    for name in EXPECTED_COMMANDS:
        ok = check(f"Command: {name}", (COMMANDS_DIR / f"{name}.md").exists()) and ok
    return ok


def gate_python_tools() -> bool:
    header("Gate 4: Python 工具")
    ok = True
    for name in ACTIVE_TOOLS:
        path = TOOLS_DIR / name
        if not path.exists():
            ok = check(f"tools/{name}", False, "文件不存在") and ok
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            check(f"tools/{name} 语法", True)
        except py_compile.PyCompileError as exc:
            ok = check(f"tools/{name} 语法", False, str(exc)[:180]) and ok

    for name in ACTIVE_TOOLS:
        path = TOOLS_DIR / name
        if path.exists() and name.replace(".py", "") not in {"archive-to-vault", "md-to-html"}:
            module_name = name[:-3].replace("-", "_")
            try:
                import_file(path, f"selftest_tool_{module_name}")
                check(f"tools/{name} 顶层导入", True)
            except Exception as exc:
                ok = check(f"tools/{name} 顶层导入", False, f"{type(exc).__name__}: {exc}") and ok
    return ok


def gate_daily_local() -> bool:
    header("Gate 5: 日报本地链路")
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
        ok = check("日报时间窗口", False, f"{type(exc).__name__}: {exc}") and ok

    try:
        from daily_mcp_check import check_mcp_config

        status = check_mcp_config()
        ok = check("新闻 MCP 本地体检", bool(status.get("all_scripts_ok"))) and ok
    except Exception as exc:
        ok = check("新闻 MCP 本地体检", False, f"{type(exc).__name__}: {exc}") and ok
    return ok


def gate_vault_template() -> bool:
    header("Gate 6: Vault 模板结构")
    ok = True
    vault = REPO_DIR / "obsidian-vault"
    ok = check("obsidian-vault 目录存在", vault.exists(), str(vault)) and ok
    if not vault.exists():
        return False
    for name in ["行业知识库", "个股逻辑", "组合管理", "跟踪面板", "日报"]:
        path = vault / name
        if path.exists():
            check(f"Vault 子目录: {name}", True)
        else:
            warn(f"Vault 子目录: {name}", "首次入库或日报入库时会自动创建")
    return ok


def gate_online_connectivity() -> bool:
    header("Optional Gate: 在线数据连通")
    ok = True
    try:
        import akshare as ak

        df = ak.stock_zh_a_hist(
            symbol="002463",
            period="daily",
            start_date="20260601",
            end_date="20260630",
            adjust="qfq",
        )
        ok = check("AKShare A股行情", df is not None and not df.empty) and ok
    except Exception as exc:
        ok = check("AKShare A股行情", False, f"{type(exc).__name__}: {exc}") and ok
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="A股AI投研系统本地自测")
    parser.add_argument("--online", action="store_true", help="同时测试外部在线数据源连通性")
    args = parser.parse_args()

    print("=" * 60)
    print("  A股AI投研系统 - 本地自测")
    print("=" * 60)
    print(f"  Repo: {REPO_DIR}")
    print(f"  MCP Config: {LOCAL_MCP_JSON if LOCAL_MCP_JSON.exists() else TEMPLATE_MCP_JSON}")

    results = {
        "Python 依赖": gate_dependencies(),
        "MCP 配置与服务器入口": gate_mcp_config(),
        "Skills 与命令入口": gate_skills_and_commands(),
        "Python 工具": gate_python_tools(),
        "日报本地链路": gate_daily_local(),
        "Vault 模板结构": gate_vault_template(),
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
        print("  注：默认自测不访问外部行情/新闻源；需要时运行 `python tools/self-test.py --online`。")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
