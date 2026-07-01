from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALLOWED_DESTINATIONS = {"industry", "stock", "skip"}
ALLOWED_ACTIONS = {"copy", "skip"}
ALLOWED_UPDATE_MODES = {"create_baseline", "append_update", "replace_summary", "update_table", "source_only", "skip"}
ALLOWED_IMPACT_LEVELS = {"major", "minor", "none"}
ALLOWED_UPDATE_POLICIES = {"merge_into_logic", "decision_log_only", "industry_update", "source_only", "skip"}
FULL_DOCUMENT = "__FULL_DOCUMENT__"


@dataclass(frozen=True)
class ArchiveSection:
    source_file: str
    heading: str
    destination: str
    knowledge_type: str
    action: str
    reason: str = ""
    target_file: str = ""
    target_section: str = ""
    update_mode: str = "append_update"
    impact_level: str = "minor"
    logic_change: bool = False
    update_policy: str = "decision_log_only"
    effective_date: str = ""


def collect_markdown_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(p for p in path.rglob("*.md") if p.is_file())
    return [path]


def extract_headings(text: str) -> list[str]:
    headings: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+)", line)
        if match:
            headings.append(match.group(1).strip())
    return headings


def build_plan_template(md_files: list[Path], stock_key: str = "", industry: str = "", base_path: Path | None = None) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    common_base = base_path if base_path and base_path.is_dir() else None
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8", errors="ignore")
        source_file = md_file.name
        if common_base:
            source_file = md_file.relative_to(common_base).as_posix()
        headings = extract_headings(text) or [FULL_DOCUMENT]
        for heading in headings:
            sections.append({
                "source_file": source_file,
                "heading": heading,
                "destination": "",
                "knowledge_type": "",
                "action": "",
                "target_file": "",
                "target_section": "",
                "update_mode": "",
                "impact_level": "",
                "logic_change": False,
                "update_policy": "",
                "effective_date": "",
                "reason": ""
            })

    return {
        "version": 1,
        "stock_key": stock_key,
        "industry": industry,
        "instructions": {
            "destination": {
                "industry": "产业链、市场空间、行业格局、政策、行业比较等可复用于同行业标的的内容",
                "stock": "公司逻辑、财务、估值、技术、筹码、情绪、风险、催化剂、投资决策、跟踪指标",
                "skip": "目录、免责声明、作者信息、附录、YAML、QA全文、MCP调用清单、流程痕迹、噪声"
            },
            "action": {
                "copy": "完整搬运原文区块",
                "skip": "不进入知识库正文"
            },
            "update_policy": {
                "merge_into_logic": "重大个股逻辑变化，更新四个子分析面或投资决策正文",
                "decision_log_only": "例行跟踪或数据更新，只在投资决策记录结论并指向原文",
                "industry_update": "重大行业知识变化，更新行业知识库正文",
                "source_only": "只进入来源索引",
                "skip": "跳过"
            },
            "discipline": "Obsidian保存当前可迭代知识，不按报告来源堆叠。Codex只填写分类计划，不改写正文；Python按计划搬运或记录。"
        },
        "sections": sections,
    }


def _sections_from_legacy_files(files: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for source_file, mapping in files.items():
        for heading, destination in mapping.items():
            sections.append({
                "source_file": source_file,
                "heading": heading,
                "destination": destination,
                "knowledge_type": "",
                "action": "skip" if destination == "skip" else "copy",
                "update_policy": "skip" if destination == "skip" else "merge_into_logic",
                "reason": "",
            })
    return sections


def load_plan(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "sections" not in data and "files" in data:
        data = {
            "version": 1,
            "stock_key": data.get("stock_key", ""),
            "industry": data.get("industry", ""),
            "sections": _sections_from_legacy_files(data["files"]),
        }
    validate_plan(data)
    return data


def validate_plan(data: dict[str, Any]) -> None:
    sections = data.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("archive plan must contain a non-empty 'sections' list")

    for i, section in enumerate(sections, 1):
        if not isinstance(section, dict):
            raise ValueError(f"section #{i} must be an object")
        for key in ("source_file", "heading", "destination", "action"):
            if not section.get(key):
                raise ValueError(f"section #{i} missing required field: {key}")
        destination = section["destination"]
        action = section["action"]
        if destination not in ALLOWED_DESTINATIONS:
            raise ValueError(f"section #{i} invalid destination: {destination!r}")
        if action not in ALLOWED_ACTIONS:
            raise ValueError(f"section #{i} invalid action: {action!r}")
        update_mode = section.get("update_mode") or ("skip" if action == "skip" else "append_update")
        section["update_mode"] = update_mode
        if update_mode not in ALLOWED_UPDATE_MODES:
            raise ValueError(f"section #{i} invalid update_mode: {update_mode!r}")
        source_file = section.get("source_file", "")
        is_initial = source_file.startswith("01-初次覆盖/")
        impact_level = section.get("impact_level") or ("none" if action == "skip" else ("major" if is_initial else "minor"))
        section["impact_level"] = impact_level
        if impact_level not in ALLOWED_IMPACT_LEVELS:
            raise ValueError(f"section #{i} invalid impact_level: {impact_level!r}")
        if action == "skip":
            default_policy = "skip"
        elif is_initial and destination == "industry":
            default_policy = "industry_update"
        elif is_initial:
            default_policy = "merge_into_logic"
        else:
            default_policy = "decision_log_only"
        update_policy = section.get("update_policy") or default_policy
        section["update_policy"] = update_policy
        if update_policy not in ALLOWED_UPDATE_POLICIES:
            raise ValueError(f"section #{i} invalid update_policy: {update_policy!r}")
        section["logic_change"] = bool(section.get("logic_change", is_initial and action != "skip"))
        if destination == "skip" and action != "skip":
            raise ValueError(f"section #{i}: destination=skip requires action=skip")
        if action == "skip" and destination != "skip":
            raise ValueError(f"section #{i}: action=skip requires destination=skip")
        if update_policy == "skip" and action != "skip":
            raise ValueError(f"section #{i}: update_policy=skip requires action=skip")
        if destination != "skip" and update_policy not in {"source_only", "decision_log_only"} and not section.get("target_file"):
            raise ValueError(f"section #{i} missing target_file")


def sections_by_file(data: dict[str, Any]) -> dict[str, list[ArchiveSection]]:
    result: dict[str, list[ArchiveSection]] = {}
    for raw in data["sections"]:
        section = ArchiveSection(
            source_file=raw["source_file"],
            heading=raw["heading"],
            destination=raw["destination"],
            knowledge_type=raw.get("knowledge_type", "") or raw["destination"],
            action=raw["action"],
            reason=raw.get("reason", ""),
            target_file=raw.get("target_file", ""),
            target_section=raw.get("target_section", ""),
            update_mode=raw.get("update_mode", "append_update"),
            impact_level=raw.get("impact_level", "minor"),
            logic_change=bool(raw.get("logic_change", False)),
            update_policy=raw.get("update_policy", "decision_log_only"),
            effective_date=raw.get("effective_date", ""),
        )
        result.setdefault(section.source_file, []).append(section)
    return result
