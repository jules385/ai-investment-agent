#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import py_compile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
EXPECTED_NEWS_MCPS = [
    "official-announcement",
    "macro-policy",
    "market-news",
    "industry-data",
]


def _server_script(config: dict) -> Path | None:
    args = config.get("args") or []
    for arg in args:
        if isinstance(arg, str) and arg.endswith(".py"):
            path = Path(arg)
            return path if path.is_absolute() else BASE / path
    return None


def check_mcp_config() -> dict:
    config_path = BASE / ".mcp.json"
    result = {
        "config_path": str(config_path.relative_to(BASE)),
        "expected_news_mcps": EXPECTED_NEWS_MCPS,
        "servers": {},
        "all_configured": False,
        "all_scripts_ok": False,
        "session_exposure": "unknown",
        "session_exposure_note": (
            "Python can validate local MCP configuration, but Codex tool exposure must be checked "
            "inside the active session with tool discovery. If news MCP tools are absent, use web fallback."
        ),
    }
    if not config_path.exists():
        result["error"] = ".mcp.json not found"
        return result

    data = json.loads(config_path.read_text(encoding="utf-8"))
    servers = data.get("mcpServers", {})
    for name in EXPECTED_NEWS_MCPS:
        config = servers.get(name)
        item = {
            "configured": bool(config),
            "disabled": bool(config.get("disabled")) if isinstance(config, dict) else None,
            "command_exists": False,
            "script_exists": False,
            "script_compiles": False,
            "script_path": "",
            "notes": [],
        }
        if not isinstance(config, dict):
            item["notes"].append("missing from .mcp.json")
            result["servers"][name] = item
            continue

        command = Path(config.get("command", ""))
        item["command_exists"] = command.exists()
        if not item["command_exists"]:
            item["notes"].append("command path does not exist")

        script = _server_script(config)
        if script:
            item["script_path"] = str(script.relative_to(BASE)) if script.is_relative_to(BASE) else str(script)
            item["script_exists"] = script.exists()
            if item["script_exists"]:
                try:
                    py_compile.compile(str(script), doraise=True)
                    item["script_compiles"] = True
                except py_compile.PyCompileError as exc:
                    item["notes"].append(str(exc)[:300])
            else:
                item["notes"].append("server script does not exist")
        else:
            item["notes"].append("no python server script found in args")
        result["servers"][name] = item

    result["all_configured"] = all(result["servers"][name]["configured"] for name in EXPECTED_NEWS_MCPS)
    result["all_scripts_ok"] = all(
        result["servers"][name]["command_exists"]
        and result["servers"][name]["script_exists"]
        and result["servers"][name]["script_compiles"]
        and not result["servers"][name]["disabled"]
        for name in EXPECTED_NEWS_MCPS
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local daily-news MCP configuration.")
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    args = parser.parse_args()
    result = check_mcp_config()
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        out = Path(args.output)
        if not out.is_absolute():
            out = BASE / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {out.relative_to(BASE)}")
    else:
        print(text)
    return 0 if result.get("all_scripts_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
