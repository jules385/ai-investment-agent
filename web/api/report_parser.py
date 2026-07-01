"""
Report parsing orchestration — no Flask dependency.
Called by tools/update-workspace.py.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from web.api.parser import ai_extract, extract_section


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def empty_workspace() -> dict:
    return {"industries": {}, "theses": {}, "tracking": {}, "stocks": {}}


def read_report_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def stock_identity(stock_dir: Path) -> tuple[str, str, str]:
    match = re.match(r"(?P<code>\d{6})-(?P<name>.+)", stock_dir.name)
    if not match:
        return stock_dir.name, stock_dir.name, stock_dir.name
    return stock_dir.name, match.group("code"), match.group("name")


def latest_file(files: list[Path]) -> Path | None:
    if not files:
        return None
    return sorted(files, key=lambda p: (p.stat().st_mtime, p.name))[-1]


def initial_report_text(stock_dir: Path) -> tuple[str, list[str]]:
    initial_dirs = [p for p in stock_dir.iterdir() if p.is_dir() and p.name.startswith("01-")]
    if not initial_dirs:
        return "", []
    report_files = sorted(initial_dirs[0].glob("*.md"))
    chief = latest_file([p for p in report_files if not p.name.startswith("子报告")])
    fundamental = latest_file([p for p in report_files if "基本面" in p.name])
    selected = [p for p in (chief, fundamental) if p]
    if not selected:
        selected = [latest_file(report_files)] if latest_file(report_files) else []
    return "\n\n".join(read_report_text(p) for p in selected), [str(p) for p in selected]


def tracking_report_text(stock_dir: Path) -> tuple[str, list[str]]:
    selected = []
    for folder in sorted(p for p in stock_dir.iterdir() if p.is_dir()):
        if not folder.name.startswith(("02-", "03-", "04-")):
            continue
        selected.extend(sorted(folder.glob("*.md")))
    return "\n\n".join(read_report_text(p) for p in selected), [str(p) for p in selected]


def load_subreports(stock_dir: Path) -> dict[str, str]:
    initial_dirs = [p for p in stock_dir.iterdir() if p.is_dir() and p.name.startswith("01-")]
    if not initial_dirs:
        return {}
    result: dict[str, str] = {}
    for f in sorted(initial_dirs[0].glob("*.md")):
        n = f.name
        if "基本面" in n:
            result["fundamental"] = read_report_text(f)
        elif "筹码" in n:
            result["chip"] = read_report_text(f)
        elif "技术" in n:
            result["technical"] = read_report_text(f)
        elif "情绪" in n:
            result["sentiment"] = read_report_text(f)
        elif not n.startswith("子报告"):
            result["chief"] = read_report_text(f)
    return result


def extract_conclusions(subreports: dict[str, str]) -> str:
    parts = []
    label = {"chip": "筹码面", "technical": "技术面", "sentiment": "情绪面"}
    for key in ("chip", "technical", "sentiment"):
        text = subreports.get(key, "")
        if not text:
            continue
        section = (
            extract_section(text, "综合结论", "综合技术面结论", "综合策略建议", "结论")
            or text[-2000:]
        )
        parts.append(f"[{label[key]}分析师结论]\n{section}")
    return "\n\n".join(parts)


def extraction_payload(result: dict) -> dict:
    return result.get("extracted") if isinstance(result, dict) and isinstance(result.get("extracted"), dict) else {}


# ---------------------------------------------------------------------------
# main parse function
# ---------------------------------------------------------------------------

def parse_all_reports_with_ai(reports_dir: Path) -> dict:
    workspace = empty_workspace()
    workspace["generated_at"] = datetime.now().isoformat(timespec="seconds")
    workspace["ai_extraction"] = True
    workspace["errors"] = []

    if not reports_dir.exists():
        workspace["errors"].append(f"Reports directory does not exist: {reports_dir}")
        return workspace

    for stock_dir in sorted(p for p in reports_dir.iterdir() if p.is_dir()):
        if not list(stock_dir.rglob("*.md")):
            continue

        stock_key, code, name = stock_identity(stock_dir)
        subreports = load_subreports(stock_dir)
        _, initial_sources = initial_report_text(stock_dir)
        tracking_text, tracking_sources = tracking_report_text(stock_dir)

        fundamental = subreports.get("fundamental", "")
        chief = subreports.get("chief", "")

        industry_source = fundamental or chief
        industry_result = ai_extract(industry_source, "industry_knowledge") if industry_source else {
            "error": "No report text found.", "extracted": {}}

        conclusions = extract_conclusions(subreports)
        thesis_source = "\n\n".join(filter(None, [chief, conclusions]))[:80000] or fundamental[:40000]
        thesis_result = ai_extract(thesis_source, "investment_thesis") if thesis_source else {
            "error": "No report text found.", "extracted": {}}

        step55 = extract_section(fundamental, "跟踪指标清单", "5.5") if fundamental else ""
        indicators_source = step55 or fundamental[:20000]
        indicators_result = ai_extract(indicators_source, "tracking_data") if indicators_source else {
            "error": "No tracking section.", "extracted": {"indicators": [], "events": [], "decisions": []}}

        events_result = ai_extract(tracking_text, "tracking_data") if tracking_text else {
            "error": "No tracking report.", "extracted": {"indicators": [], "events": [], "decisions": []}}

        ind_data = extraction_payload(indicators_result)
        evt_data = extraction_payload(events_result)
        tracking_result = {
            "error": indicators_result.get("error") or events_result.get("error"),
            "extracted": {
                "indicators": ind_data.get("indicators") or evt_data.get("indicators") or [],
                "events": evt_data.get("events") or ind_data.get("events") or [],
                "decisions": evt_data.get("decisions") or ind_data.get("decisions") or [],
            },
        }

        industry_data = extraction_payload(industry_result)
        thesis_data = extraction_payload(thesis_result)
        tracking_data = extraction_payload(tracking_result)
        industry_name = industry_data.get("industry") or "未分类"

        workspace["stocks"][stock_key] = {
            "code": code, "name": name, "stock": stock_key,
            "industry": industry_name,
            "source_files": initial_sources + tracking_sources,
        }
        workspace["theses"][stock_key] = thesis_data
        workspace["tracking"][stock_key] = tracking_data

        grouped = workspace["industries"].setdefault(industry_name, {
            "name": industry_name, "stocks": [],
            "chain": industry_data.get("chain", []),
            "tam_cagr": industry_data.get("tam_cagr", {}),
            "financial_benchmarks": industry_data.get("financial_benchmarks", {}),
        })
        grouped["stocks"].append({"stock": stock_key, "code": code, "name": name})
        if not grouped.get("chain") and industry_data.get("chain"):
            grouped["chain"] = industry_data["chain"]

        for etype, eresult in (("industry", industry_result), ("thesis", thesis_result), ("tracking", tracking_result)):
            if eresult.get("error"):
                workspace["errors"].append({"stock": stock_key, "type": etype, "error": eresult["error"]})

    workspace["stocks_parsed"] = len(workspace["stocks"])
    return workspace
