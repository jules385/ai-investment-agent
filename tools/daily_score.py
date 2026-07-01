#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Shanghai")

SOURCE_SCORE = {"A": 100, "B": 80, "C": 55, "D": 25}
SECTION_WEIGHT = {"macro": 80, "industry": 85, "stock": 90}
TIME_CONFIDENCE_SCORE = {"high": 100, "medium": 75, "low": 45}
VERIFICATION_BONUS = {
    "official": 100,
    "verified": 85,
    "single_source": 55,
    "unverified": 30,
    "rumor": 10,
}


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)


def score_item(item: dict, window_end: str) -> dict:
    source = SOURCE_SCORE.get(item.get("source_tier", "D"), 25)
    end = parse_time(window_end)
    published = parse_time(item["published_at"])
    hours_old = max(0.0, (end - published).total_seconds() / 3600)
    freshness = max(0, 100 - int(hours_old * 4))
    relation = min(100, 45 + 20 * len(item.get("related_stocks", [])) + 10 * len(item.get("related_industries", [])))
    verified = min(100, 40 + 30 * len(item.get("verified_by", [])))
    verification_status = item.get("verification_status") or ("verified" if item.get("verified_by") else "single_source")
    verified = max(verified, VERIFICATION_BONUS.get(verification_status, verified))
    time_confidence = TIME_CONFIDENCE_SCORE.get(item.get("published_at_confidence", "medium"), 75)
    scope = SECTION_WEIGHT.get(item.get("section"), 60)
    total = round(
        source * 0.25
        + freshness * 0.18
        + relation * 0.18
        + scope * 0.14
        + verified * 0.15
        + time_confidence * 0.10,
        1,
    )
    if total >= 85:
        level = "S"
    elif total >= 72:
        level = "A"
    elif total >= 58:
        level = "B"
    elif total >= 40:
        level = "C"
    else:
        level = "D"
    return {
        **item,
        "credibility_score": source,
        "freshness_score": freshness,
        "relation_score": relation,
        "verification_score": verified,
        "time_confidence_score": time_confidence,
        "importance_score": total,
        "importance_level": item.get("ai_importance") or level,
    }


def score_file(evidence_path: Path) -> Path:
    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    scored = [score_item(item, data["window_end"]) for item in data.get("items", [])]
    scored.sort(key=lambda item: item["importance_score"], reverse=True)
    output = {
        "date": data["date"],
        "window_start": data["window_start"],
        "window_end": data["window_end"],
        "timezone": data["timezone"],
        "workflow_version": data.get("workflow_version", "daily-v0.1"),
        "collection_rounds": data.get("collection_rounds", []),
        "coverage": data.get("coverage", {}),
        "mcp_status": data.get("mcp_status", {}),
        "items": scored,
    }
    out_path = evidence_path.parent / "scoring.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Score daily evidence items.")
    parser.add_argument("evidence", help="Path to evidence.json")
    args = parser.parse_args()
    path = Path(args.evidence)
    if not path.is_absolute():
        path = BASE / path
    out = score_file(path)
    print(f"wrote {out.relative_to(BASE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
