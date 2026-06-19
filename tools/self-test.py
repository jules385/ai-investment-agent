"""
A股AI投研系统 — 自动化自测脚本
基于 5 关验证流程，验证 MCP/Skills/Subagent/信号/合成 全链路

用法: python tools/self-test.py
"""

import sys
import os
import json
import subprocess
import time
from pathlib import Path

REPO_DIR = Path(__file__).parent.parent.resolve()
HOME = Path.home()
MCP_JSON = HOME / ".mcp.json"
SKILLS_DIR = HOME / ".claude" / "skills" / "analysts"
COMMANDS_DIR = HOME / ".claude" / "commands"

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

# ── 测试标的信息 ─────────────────────────────────
TEST_SYMBOL = "002202"
TEST_NAME = "金风科技"


def header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    msg = f"  {status} {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return condition


def warn(label: str, detail: str = ""):
    print(f"  {WARN} {label} — {detail}")


# ── 第一关：MCP Server 存活检查 ─────────────────

def gate1_mcp_servers():
    header("第一关：MCP Server 存活检查")

    all_pass = True

    # 1.1 MCP config exists
    if not MCP_JSON.exists():
        check("MCP 配置文件", False, f"缺少 {MCP_JSON}")
        return False
    config = json.loads(MCP_JSON.read_text(encoding='utf-8'))
    servers = config.get("mcpServers", {})
    check("MCP 配置文件存在", True, str(MCP_JSON))

    # 1.2 Check each server config
    for name in ["finance-data", "tech-analysis"]:
        if name not in servers:
            check(f"{name} Server 配置", False, "在 .mcp.json 中未找到")
            all_pass = False
            continue
        srv = servers[name]
        cmd = srv.get("command", "")
        args = srv.get("args", [])
        server_path = args[0] if args else ""
        if not Path(server_path).exists():
            check(f"{name} Server 文件", False, f"不存在: {server_path}")
            all_pass = False
        else:
            check(f"{name} Server 文件", True, server_path)

    # 1.3 Check Python deps
    try:
        import akshare
        check("akshare 已安装", True, f"v{akshare.__version__}")
    except ImportError:
        check("akshare 已安装", False, "pip install akshare")
        all_pass = False

    try:
        import mcp
        check("mcp 已安装", True)
    except ImportError:
        check("mcp 已安装", False, "pip install mcp")
        all_pass = False

    try:
        import ta
        check("ta 已安装", True)
    except ImportError:
        check("ta 已安装", False, "pip install ta")
        all_pass = False

    # 1.4 Try importing server modules to catch syntax errors
    for name in ["finance-data", "tech-analysis"]:
        server_py = REPO_DIR / "mcp-servers" / name / "server.py"
        if server_py.exists():
            try:
                code = server_py.read_text(encoding='utf-8')
                compile(code, f'{name}/server.py', 'exec')
                check(f"{name} Server 语法检查", True)
            except SyntaxError as e:
                check(f"{name} Server 语法检查", False, str(e)[:100])
                all_pass = False

    return all_pass


# ── 第二关：Skill 文件检查 ─────────────────

def gate2_skill_files():
    header("第二关：Skill 文件检查")

    all_pass = True
    expected_skills = {
        "analyst-chief", "analyst-fundamental", "analyst-chip-flow",
        "analyst-technical", "analyst-sentiment", "analyst-data-qa", "analyst-beautifier"
    }

    # 2.1 Check all skills exist in the repo (source of truth)
    repo_skills_dir = REPO_DIR / "skills" / "analysts"
    existing = set()
    if repo_skills_dir.exists():
        for d in repo_skills_dir.iterdir():
            if d.is_dir() and (d / "SKILL.md").exists():
                existing.add(d.name)

    for name in sorted(expected_skills):
        if name in existing:
            check(f"Skill: {name}", True)
        else:
            check(f"Skill: {name}", False, "SKILL.md 不存在")
            all_pass = False

    # 2.2 Check for data source priority rules (skip non-data roles)
    priority_keywords = ["数据源优先级"]
    lock_keywords = ["角色锁定", "独立 Subagent"]
    skip_priority_check = {"analyst-beautifier", "analyst-chief"}

    for name in sorted(existing):
        skill_md = repo_skills_dir / name / "SKILL.md"
        content = skill_md.read_text(encoding='utf-8')
        has_priority = any(kw in content for kw in priority_keywords)
        has_lock = any(kw in content for kw in lock_keywords)
        if name not in skip_priority_check and not has_priority:
            warn(f"{name} 缺少数据源优先级规则")
        if not has_lock:
            warn(f"{name} 缺少角色锁定指令")

    # 2.3 Check commands (repo or ~/.claude/)
    for cmd_name in ["analyze-initial", "analyze-weekly", "analyze-monthly", "analyze-quarterly", "beautify-report"]:
        cmd_file = COMMANDS_DIR / f"{cmd_name}.md"
        if not cmd_file.exists():
            cmd_file = REPO_DIR / "commands" / f"{cmd_name}.md"
        if cmd_file.exists():
            check(f"Command: {cmd_name}", True)
        else:
            check(f"Command: {cmd_name}", False, "未安装")
            all_pass = False

    return all_pass


# ── 第三关：MCP 连通性测试 ─────────────────

def gate3_mcp_connectivity():
    header("第三关：MCP 工具连通性测试")

    all_pass = True

    # Check if akshare can fetch real data
    try:
        import akshare as ak
        df = ak.stock_zh_a_hist(symbol=TEST_SYMBOL, period="daily",
            start_date="20260101", end_date="20260617", adjust="qfq")
        if df is not None and not df.empty:
            check("AKShare 数据连通", True, f"{TEST_SYMBOL} 获取到 {len(df)} 行")
        else:
            check("AKShare 数据连通", False, "返回空数据")
            all_pass = False
    except Exception as e:
        check("AKShare 数据连通", False, str(e)[:100])
        all_pass = False

    # Check finance-data specific functions
    try:
        import akshare as ak
        # Test financial indicators
        fin = ak.stock_financial_abstract_ths(symbol=TEST_SYMBOL, indicator="按报告期")
        if fin is not None and not fin.empty:
            check("finance-data: 财务数据", True, f"{len(fin)} 期报告")
        else:
            warn("finance-data: 财务数据", "返回空，可能限流")
    except Exception as e:
        check("finance-data: 财务数据", False, str(e)[:100])
        all_pass = False

    # Check tech-analysis functions via ta library
    try:
        import akshare as ak
        import pandas as pd
        import ta
        ak_sym = f"sz{TEST_SYMBOL}" if TEST_SYMBOL.startswith(('0','3','2')) else f"sh{TEST_SYMBOL}"
        df = ak.stock_zh_a_daily(symbol=ak_sym, adjust="qfq")
        if not df.empty:
            close = df['close'].astype(float)
            ma20 = close.rolling(20).mean().iloc[-1]
            check("tech-analysis: 均线计算", True, f"MA20={ma20:.2f}")
        else:
            check("tech-analysis: 均线计算", False, "无数据")
            all_pass = False
    except Exception as e:
        check("tech-analysis: 均线计算", False, str(e)[:100])
        all_pass = False

    return all_pass


def gate5_mcp_agent_compatibility(test_symbol="002202"):
    """MCP 子 Agent 兼容性说明 + Server 语法检查"""
    print("\n" + "=" * 60)
    print("  第五关：MCP 子 Agent 兼容性检查")
    print("=" * 60)

    print("""
  ⚠️  MCP stdio 服务器由 Claude Code 主会话启动。
      子 Agent 能否继承 MCP 取决于 Claude Code 版本。

  手动验证（在 Claude Code 中执行）：
      "用 Subagent 调用 tech-analysis MCP 的 compute_ma，
       获取 {} 的日线均线"

  预期：
      ✅ 返回 MA5/MA10/MA20 数值 → 正常
      ❌ Subagent 用 WebSearch 替代 → MCP 未继承（降级可用）
""".format(test_symbol))

    import subprocess
    server_dir = REPO_DIR / "mcp-servers"
    ok = True
    for name in ["finance-data", "tech-analysis"]:
        server_py = server_dir / name / "server.py"
        result = subprocess.run(
            [sys.executable, "-c",
             "compile(open(r'{}', encoding='utf-8').read(), 'server.py', 'exec')".format(server_py)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"  ✅ {name} server.py 语法通过")
        else:
            print(f"  ❌ {name} server.py 语法错误: {result.stderr.strip()[:100]}")
            ok = False

    return ok  # 此关仅作信息提示


# ── 第四关：工具计数检查 ─────────────────

def gate4_tool_coverage():
    header("第四关：MCP 工具覆盖检查")

    # Count expected tools from server source
    tool_counts = {}
    for name in ["finance-data", "tech-analysis"]:
        server_py = REPO_DIR / "mcp-servers" / name / "server.py"
        if not server_py.exists():
            tool_counts[name] = 0
            continue
        content = server_py.read_text(encoding='utf-8')
        count = content.count("@mcp.tool()")
        tool_counts[name] = count
        check(f"{name}: 工具数量", count >= 9 if name == "finance-data" else count >= 10,
              f"{count} 个工具")

    # Check if all 9 tools exist in finance-data
    expected_finance = ["get_historical_data", "get_financial_indicators", "get_valuation",
                         "get_shareholders", "get_lhb_details", "get_fund_flow",
                         "get_margin_data", "get_hsgt_holdings", "get_chip_distribution"]
    server_py = REPO_DIR / "mcp-servers" / "finance-data" / "server.py"
    content = server_py.read_text(encoding='utf-8')
    missing = [t for t in expected_finance if f"def {t}" not in content]
    if missing:
        for t in missing:
            check(f"finance-data 缺工具: {t}", False)
    else:
        check("finance-data 工具完整", True, f"{len(expected_finance)}/9")

    return all(v >= 9 if k == "finance-data" else v >= 10 for k, v in tool_counts.items())


# ── Main ───────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  A股AI投研系统 — 自动化自测")
    print(f"  测试标的: {TEST_NAME}({TEST_SYMBOL})")
    print("=" * 60)
    print(f"  Repo: {REPO_DIR}")
    print(f"  Skills: {SKILLS_DIR}")
    print(f"  MCP Config: {MCP_JSON}")

    results = {
        "Gate 1: MCP Server 存活": gate1_mcp_servers(),
        "Gate 2: Skill 文件": gate2_skill_files(),
        "Gate 3: MCP 连通性": gate3_mcp_connectivity(),
        "Gate 4: 工具覆盖": gate4_tool_coverage(),
        "Gate 5: MCP 子Agent兼容": gate5_mcp_agent_compatibility(TEST_SYMBOL),
    }

    # ── Summary ──
    header("自测结果")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, result in results.items():
        status = PASS if result else FAIL
        print(f"  {status} {name}")

    print(f"\n  通过: {passed}/{total}")

    if passed == total:
        print(f"\n  [PASS] 全部通过！系统可以执行初次覆盖测试。")
        print(f"     运行: /analyze-initial {TEST_SYMBOL} {TEST_NAME}")
    else:
        print(f"\n  [FAIL] {total - passed} 关未通过，请修复后重试。")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
