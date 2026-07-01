#!/usr/bin/env python3
"""
研报解析 + 同步 Obsidian vault，每次投研完成后运行。
Usage: python tools/update-workspace.py
"""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from web.api.report_parser import parse_all_reports_with_ai

data = parse_all_reports_with_ai(BASE / "reports" / "stocks")
out = BASE / "reports" / "workspace-data.json"
out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"解析完成：{data.get('stocks_parsed', 0)} 只股票，{len(data.get('industries', {}))} 个行业")

subprocess.run([sys.executable, str(BASE / "tools" / "sync-to-vault.py")], check=True)
