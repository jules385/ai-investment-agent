#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import io
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
elif hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from archive_indexer import ArchiveSummary
from archive_router import default_target_file, default_target_section, tracking_file
from archive_schema import FULL_DOCUMENT, ArchiveSection, build_plan_template, collect_markdown_files, load_plan
from archive_validator import validate_note
from archive_writer import append_decision_log, append_tracking_task, append_update, copy_raw_reports, ensure_baseline_files, replace_summary

VAULT = BASE / "obsidian-vault"
SOURCE_INDEX_DIR = VAULT / "原始资料索引"
TODAY = date.today().isoformat()


def detect_stock_key(path: Path) -> str:
    for part in path.parts:
        if re.match(r"^\d{6}-.+", part):
            return part
    return ""


def extract_section(text: str, heading: str) -> str:
    if heading == FULL_DOCUMENT:
        return text.strip()

    lines = text.splitlines()
    inside = False
    start_level = 0
    collected: list[str] = []

    for line in lines:
        match = re.match(r"^(#{1,6})\s+(.+)", line)
        if match:
            level = len(match.group(1))
            current_heading = match.group(2).strip()
            if not inside and current_heading == heading:
                inside = True
                start_level = level
                collected.append(line)
                continue
            if inside and level <= start_level:
                break
        if inside:
            collected.append(line)

    return "\n".join(collected).strip()


def normalize_headings(content: str, base_level: int = 3) -> str:
    levels = []
    for line in content.splitlines():
        match = re.match(r"^(#{1,6})\s+", line)
        if match:
            levels.append(len(match.group(1)))
    if not levels:
        return content

    shift = base_level - min(levels)
    result = []
    for line in content.splitlines():
        match = re.match(r"^(#{1,6})(\s+.+)", line)
        if match:
            new_level = max(1, min(6, len(match.group(1)) + shift))
            result.append("#" * new_level + match.group(2))
        else:
            result.append(line)
    return "\n".join(result).strip()


def strip_redundant_first_heading(content: str, target_section: str) -> str:
    lines = content.splitlines()
    if not lines:
        return content
    first = lines[0].strip()
    match = re.match(r"^#{1,6}\s+(.+)", first)
    if not match:
        return content
    first_heading = match.group(1).strip()
    if first_heading == target_section or first_heading in target_section or target_section in first_heading:
        return "\n".join(lines[1:]).strip()
    return content


def build_block(section: ArchiveSection, content: str, target_section: str) -> str:
    body = normalize_headings(content, base_level=3)
    body = strip_redundant_first_heading(body, target_section)
    if section.update_mode == "create_baseline":
        return body.strip() + "\n"
    date_text = section.effective_date or TODAY
    return f"> [!info] 更新日期：{date_text}\n\n{body.strip()}\n"


def update_source_index(source_path: Path, stock_key: str, industry: str, summary: ArchiveSummary) -> None:
    SOURCE_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index_path = SOURCE_INDEX_DIR / "sources.md"
    row = (
        f"| {TODAY} | `{source_path.as_posix()}` | {stock_key} | {industry} | "
        f"{summary.industry_sections} | {summary.stock_sections} | {summary.skipped_sections} |\n"
    )
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
        if row.strip() in text:
            return
        index_path.write_text(text.rstrip() + "\n" + row, encoding="utf-8")
    else:
        index_path.write_text(
            "# 原始资料索引\n\n"
            "| 日期 | 来源 | 标的 | 行业 | 行业章节 | 个股章节 | 跳过章节 |\n"
            "|------|------|------|------|:--:|:--:|:--:|\n"
            + row,
            encoding="utf-8",
        )


def default_update_mode(source_file: str) -> str:
    if source_file.startswith("01-初次覆盖/"):
        return "create_baseline"
    if any(source_file.startswith(prefix) for prefix in ("02-周度跟踪/", "03-月度跟踪/", "04-季度跟踪/", "06-年度跟踪/")):
        return "append_update"
    return "append_update"


def default_update_policy(source_file: str, destination: str) -> str:
    if destination == "skip":
        return "skip"
    if source_file.startswith("01-初次覆盖/"):
        return "industry_update" if destination == "industry" else "merge_into_logic"
    return "decision_log_only"


def default_impact_level(source_file: str, destination: str) -> str:
    if destination == "skip":
        return "none"
    if source_file.startswith("01-初次覆盖/"):
        return "major"
    return "minor"


def report_type_from_source(source_file: str) -> str:
    if source_file.startswith("02-周度跟踪/"):
        return "周度跟踪"
    if source_file.startswith("03-月度跟踪/"):
        return "月度跟踪"
    if source_file.startswith("04-季度跟踪/"):
        return "季度跟踪"
    if source_file.startswith("06-年度跟踪/"):
        return "年度跟踪"
    if source_file.startswith("01-初次覆盖/"):
        return "初次覆盖"
    return "研究资料"


def execute_archive(target: Path, stock_key: str, industry: str, plan_path: Path, overwrite: bool = False) -> list[Path]:
    md_files = {}
    for p in collect_markdown_files(target):
        key = p.relative_to(target).as_posix() if target.is_dir() else p.name
        md_files[key] = p
    plan = load_plan(plan_path)
    stock_key = stock_key or plan.get("stock_key") or detect_stock_key(target)
    industry = industry or plan.get("industry") or "未分类"
    if not stock_key:
        raise ValueError("stock_key is required, e.g. 600879-航天电子")

    ensure_baseline_files(VAULT, stock_key, industry, overwrite=overwrite)
    # Raw report archival is deterministic: copy every source Markdown file verbatim.
    raw_report_paths = copy_raw_reports(VAULT, target, stock_key, overwrite=True)

    summary = ArchiveSummary()
    touched: set[Path] = set(raw_report_paths)
    decision_logged_sources: set[str] = set()

    for raw in plan["sections"]:
        section = ArchiveSection(
            source_file=raw["source_file"],
            heading=raw["heading"],
            destination=raw["destination"],
            knowledge_type=raw.get("knowledge_type", "") or raw["destination"],
            action=raw["action"],
            reason=raw.get("reason", ""),
            target_file=raw.get("target_file", ""),
            target_section=raw.get("target_section", ""),
            update_mode=raw.get("update_mode") or "append_update",
            impact_level=raw.get("impact_level") or default_impact_level(raw["source_file"], raw["destination"]),
            logic_change=bool(raw.get("logic_change", False)),
            update_policy=raw.get("update_policy") or default_update_policy(raw["source_file"], raw["destination"]),
            effective_date=raw.get("effective_date", ""),
        )
        summary.sources.add(section.source_file)
        if section.knowledge_type:
            summary.knowledge_types.add(section.knowledge_type)
        if section.action == "skip":
            summary.skipped_sections += 1
            continue

        source_file = md_files.get(section.source_file)
        if not source_file:
            raise FileNotFoundError(f"source file in plan not found: {section.source_file}")
        text = source_file.read_text(encoding="utf-8", errors="ignore")
        content = extract_section(text, section.heading)
        if not content:
            print(f"  [warn] empty section: {section.source_file} / {section.heading}")
            continue

        target_file = section.target_file or default_target_file(stock_key, industry, section.destination, section.source_file, section.heading)
        target_section = section.target_section or default_target_section(section.heading, section.knowledge_type)

        if section.update_policy == "source_only" or section.update_mode == "source_only":
            summary.copied_sections.append(section)
            continue
        if section.update_policy == "decision_log_only":
            if section.source_file not in decision_logged_sources:
                conclusion = f"{report_type_from_source(section.source_file)}：未标记为重大逻辑变化，分析过程见原文。"
                path = append_decision_log(
                    VAULT,
                    stock_key,
                    section.source_file,
                    source_file.relative_to(BASE),
                    conclusion,
                    logic_change=section.logic_change,
                    effective_date=section.effective_date or TODAY,
                )
                touched.add(path)
                decision_logged_sources.add(section.source_file)
            summary.copied_sections.append(section)
            if section.destination == "industry":
                summary.industry_sections += 1
            elif section.destination == "stock":
                summary.stock_sections += 1
            continue

        block = build_block(section, content, target_section)
        if section.update_mode == "replace_summary":
            path = replace_summary(VAULT, target_file, target_section, block)
        else:
            path = append_update(VAULT, target_file, target_section, block)

        if section.destination == "industry":
            summary.industry_sections += 1
        elif section.destination == "stock":
            summary.stock_sections += 1
        touched.add(path)
        summary.copied_sections.append(section)

    append_tracking_task(VAULT, stock_key, f"复核本次入库的 {summary.stock_sections} 个个股章节与 {summary.industry_sections} 个行业章节")
    touched.add(VAULT / tracking_file(stock_key))

    update_source_index(target.relative_to(BASE) if target.is_relative_to(BASE) else target, stock_key, industry, summary)

    print(
        f"✅ Archive complete: {summary.industry_sections} industry sections, "
        f"{summary.stock_sections} stock sections, {summary.skipped_sections} skipped"
    )
    for path in sorted(touched):
        print(f"   {path.relative_to(BASE)}")
    return sorted(touched)


def emit_plan(target: Path, stock_key: str, industry: str, out_path: Path) -> None:
    md_files = collect_markdown_files(target)
    if not md_files:
        raise FileNotFoundError(f"no markdown files found: {target}")
    stock_key = stock_key or detect_stock_key(target)
    plan = build_plan_template(md_files, stock_key, industry, base_path=target)
    for section in plan["sections"]:
        source_file = section["source_file"]
        heading = section["heading"]
        # Leave classification blank for Codex, but provide routing defaults.
        section["target_file"] = default_target_file(stock_key, industry, "stock", source_file, heading)
        section["target_section"] = default_target_section(heading, "")
        section["update_mode"] = default_update_mode(source_file)
        section["impact_level"] = default_impact_level(source_file, "stock")
        section["logic_change"] = source_file.startswith("01-初次覆盖/")
        section["update_policy"] = default_update_policy(source_file, "stock")
        section["effective_date"] = TODAY
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(__import__("json").dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote archive plan template: {out_path.relative_to(BASE)}")


def validate(paths: list[str]) -> int:
    status = 0
    for item in paths:
        path = Path(item)
        if not path.is_absolute():
            path = BASE / path
        issues = validate_note(path)
        if issues:
            status = 1
            print(f"[FAIL] {path.relative_to(BASE)}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"[PASS] {path.relative_to(BASE)}")
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive non-standard research outputs to Obsidian.")
    parser.add_argument("path", nargs="?", help="Report file/directory, or note path when --validate is used")
    parser.add_argument("stock_key", nargs="?", default="", help="Stock key, e.g. 600879-航天电子")
    parser.add_argument("industry", nargs="?", default="", help="Industry note name")
    parser.add_argument("--emit-plan", "--emit-classification-plan", dest="emit_plan", default="")
    parser.add_argument("--plan", "--classification-plan", dest="plan", default="")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing AI-managed vault note content")
    parser.add_argument("--validate", nargs="*", default=None, help="Validate vault note(s)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.validate is not None:
        targets = args.validate or ([args.path] if args.path else [])
        if not targets:
            raise SystemExit("--validate requires at least one note path")
        return validate(targets)

    if not args.path:
        raise SystemExit("path is required")
    target = Path(args.path)
    if not target.is_absolute():
        target = BASE / target

    if args.emit_plan:
        out_path = Path(args.emit_plan)
        if not out_path.is_absolute():
            out_path = BASE / out_path
        emit_plan(target, args.stock_key, args.industry, out_path)
        return 0

    if not args.plan:
        raise SystemExit("A Codex-filled archive plan is required. Use --emit-plan first, then run with --plan.")
    plan_path = Path(args.plan)
    if not plan_path.is_absolute():
        plan_path = BASE / plan_path
    execute_archive(target, args.stock_key, args.industry, plan_path, overwrite=args.overwrite)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
