#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from daily_mcp_check import check_mcp_config
from daily_window import daily_window, parse_date

BASE = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Shanghai")

REQUIRED_FIELDS = {
    "section",
    "source_type",
    "source_name",
    "source_tier",
    "published_at",
    "title",
}

COLLECTION_ROUNDS = [
    {
        "id": "macro-policy",
        "section": "macro",
        "purpose": "央行、统计局、财政部、发改委、工信部等宏观政策和官方数据",
        "preferred_mcp": "macro-policy",
        "fallback": "official sites / authority media web search",
    },
    {
        "id": "market-news",
        "section": "macro|industry",
        "purpose": "权威财经媒体的重要市场新闻与跨行业事件",
        "preferred_mcp": "market-news",
        "fallback": "authority media web search",
    },
    {
        "id": "industry-data",
        "section": "industry",
        "purpose": "行业政策、产业链供需、订单、价格、库存和监管事件",
        "preferred_mcp": "industry-data",
        "fallback": "industry authority / media web search",
    },
    {
        "id": "official-announcement",
        "section": "stock",
        "purpose": "交易所、巨潮资讯、证监会、上市公司公告",
        "preferred_mcp": "official-announcement",
        "fallback": "exchange / cninfo / company IR web search",
    },
]


def parse_time(value: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=TZ)
        except ValueError:
            pass
    raise ValueError(f"invalid published_at: {value!r}")


def in_window(item: dict, start: datetime, end: datetime) -> bool:
    published = parse_time(item["published_at"])
    return start <= published <= end


def normalize_item(item: dict, idx: int, date: str) -> dict:
    missing = sorted(field for field in REQUIRED_FIELDS if not item.get(field))
    if missing:
        raise ValueError(f"evidence item #{idx} missing fields: {', '.join(missing)}")
    normalized = {
        "id": item.get("id") or f"daily-{date.replace('-', '')}-{idx:03d}",
        "section": item["section"],
        "source_type": item["source_type"],
        "source_name": item["source_name"],
        "source_tier": item["source_tier"],
        "published_at": item["published_at"],
        "title": item["title"],
        "summary": item.get("summary", ""),
        "url": item.get("url", ""),
        "raw_text_path": item.get("raw_text_path", ""),
        "related_industries": item.get("related_industries", []),
        "related_stocks": item.get("related_stocks", []),
        "verified_by": item.get("verified_by", []),
        "published_at_confidence": item.get("published_at_confidence", "medium"),
        "time_note": item.get("time_note", ""),
        "collection_round": item.get("collection_round", ""),
        "verification_status": item.get("verification_status", ""),
        "verification_note": item.get("verification_note", ""),
        "knowledge_action": item.get("knowledge_action", "daily_only"),
        "impact_hint": item.get("impact_hint", ""),
        "ai_importance": item.get("ai_importance", ""),
        "ai_reasoning": item.get("ai_reasoning", ""),
        "follow_up": item.get("follow_up", ""),
    }
    if normalized["section"] not in {"macro", "industry", "stock"}:
        raise ValueError(f"evidence item #{idx} invalid section: {normalized['section']!r}")
    if normalized["source_tier"] not in {"A", "B", "C", "D"}:
        raise ValueError(f"evidence item #{idx} invalid source_tier: {normalized['source_tier']!r}")
    if normalized["published_at_confidence"] not in {"high", "medium", "low"}:
        raise ValueError(
            f"evidence item #{idx} invalid published_at_confidence: "
            f"{normalized['published_at_confidence']!r}"
        )
    if not normalized["verification_status"]:
        normalized["verification_status"] = "verified" if normalized["verified_by"] else "single_source"
    return normalized


def load_items(path: Path | None) -> list[dict]:
    if not path:
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("items", [])
    if not isinstance(data, list):
        raise ValueError("input evidence must be a list or an object with items")
    return data


def copy_raw_inputs(raw_dir: Path | None, output_raw_dir: Path) -> list[str]:
    if not raw_dir or not raw_dir.exists():
        return []
    copied: list[str] = []
    for src in sorted(p for p in raw_dir.rglob("*") if p.is_file()):
        rel = src.relative_to(raw_dir)
        dst = output_raw_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst.relative_to(BASE).as_posix())
    return copied


def build_evidence(
    date: str,
    input_path: Path | None,
    raw_dir: Path | None,
    exposure_status: str,
    exposure_note: str,
) -> Path:
    window = daily_window(parse_date(date))
    start = parse_time(window["window_start"])
    end = parse_time(window["window_end"])
    output_dir = BASE / "reports" / "daily" / window["date"]
    raw_output_dir = output_dir / "原始资料"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_output_dir.mkdir(parents=True, exist_ok=True)

    raw_paths = copy_raw_inputs(raw_dir, raw_output_dir)
    mcp_status = check_mcp_config()
    mcp_status["session_exposure"] = exposure_status
    if exposure_note:
        mcp_status["session_exposure_note"] = exposure_note

    items = []
    rejected = []
    for idx, item in enumerate(load_items(input_path), 1):
        normalized = normalize_item(item, idx, window["date"])
        if in_window(normalized, start, end):
            items.append(normalized)
        else:
            rejected.append({
                "title": normalized.get("title", ""),
                "published_at": normalized.get("published_at", ""),
                "reason": "outside_daily_window",
            })

    round_counts = {round_info["id"]: 0 for round_info in COLLECTION_ROUNDS}
    round_counts["uncategorized"] = 0
    for item in items:
        collection_round = item.get("collection_round") or "uncategorized"
        round_counts[collection_round] = round_counts.get(collection_round, 0) + 1

    payload = {
        **window,
        "workflow_version": "daily-v0.2",
        "collection_rounds": COLLECTION_ROUNDS,
        "coverage": {
            "round_counts": round_counts,
            "total_items": len(items),
            "rejected_items": rejected,
            "raw_files_count": len(raw_paths),
        },
        "mcp_status": mcp_status,
        "items": items,
        "raw_files": raw_paths,
    }
    out_path = output_dir / "evidence.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build daily evidence.json from MCP/web/manual evidence.")
    parser.add_argument("--date", default="", help="Report date in YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--input", default="", help="Optional JSON evidence list.")
    parser.add_argument("--raw-dir", default="", help="Optional raw source files to copy into reports/daily.")
    parser.add_argument(
        "--exposure-status",
        choices=["exposed", "not_exposed", "partial", "unknown"],
        default="unknown",
        help="Whether news MCP tools are exposed in the active Codex session.",
    )
    parser.add_argument("--exposure-note", default="", help="Short note about MCP exposure or fallback.")
    args = parser.parse_args()
    input_path = Path(args.input) if args.input else None
    raw_dir = Path(args.raw_dir) if args.raw_dir else None
    if input_path and not input_path.is_absolute():
        input_path = BASE / input_path
    if raw_dir and not raw_dir.is_absolute():
        raw_dir = BASE / raw_dir
    out = build_evidence(args.date or None, input_path, raw_dir, args.exposure_status, args.exposure_note)
    print(f"wrote {out.relative_to(BASE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
