#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from archive_formatter import append_before_marker, write_ai_note

BASE = Path(__file__).resolve().parents[1]
VAULT = BASE / "obsidian-vault"


def report_date(report_path: Path) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", report_path.as_posix())
    if match:
        return match.group(1)
    return report_path.parent.name


def to_vault(report_path: Path) -> Path:
    text = report_path.read_text(encoding="utf-8")
    date = report_date(report_path)
    target = VAULT / "日报" / f"{date}.md"
    write_ai_note(target, text, format_content=False)
    return target


def resolve_stock_key(stock: str) -> str:
    if re.match(r"^\d{6}-.+", stock):
        return stock
    match = re.match(r"^(\d{6})", stock)
    if not match:
        return ""
    symbol = match.group(1)
    stock_root = VAULT / "个股逻辑"
    if not stock_root.exists():
        return ""
    for path in stock_root.iterdir():
        if path.is_dir() and path.name.startswith(symbol):
            return path.name
    return ""


def append_followups(scoring_path: Path | None, date: str) -> list[Path]:
    if not scoring_path or not scoring_path.exists():
        return []
    data = json.loads(scoring_path.read_text(encoding="utf-8"))
    touched: list[Path] = []
    for item in data.get("items", []):
        follow_up = item.get("follow_up", "").strip()
        if not follow_up:
            continue
        for stock in item.get("related_stocks", []):
            stock_key = resolve_stock_key(str(stock))
            if not stock_key:
                continue
            path = VAULT / "跟踪面板" / f"{stock_key}.md"
            if not path.exists():
                continue
            block = f"- [ ] {date} 日报触发：{follow_up}（{item.get('title', '未命名事件')}）\n"
            append_before_marker(path, "## 下次跟踪指引\n\n" + block if "## 下次跟踪指引" not in path.read_text(encoding="utf-8") else block)
            touched.append(path)
    return touched


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy daily report into Obsidian vault.")
    parser.add_argument("report", help="Path to reports/daily/YYYY-MM-DD/日报.md")
    parser.add_argument("--scoring", default="", help="Optional scoring.json for appending follow-up tasks.")
    args = parser.parse_args()
    path = Path(args.report)
    if not path.is_absolute():
        path = BASE / path
    scoring_path = Path(args.scoring) if args.scoring else path.parent / "scoring.json"
    if scoring_path and not scoring_path.is_absolute():
        scoring_path = BASE / scoring_path
    out = to_vault(path)
    touched = append_followups(scoring_path, report_date(path))
    print(f"wrote {out.relative_to(BASE)}")
    for item in touched:
        print(f"updated {item.relative_to(BASE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
