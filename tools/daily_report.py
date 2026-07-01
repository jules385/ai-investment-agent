#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

SECTION_NAMES = {
    "macro": "宏观",
    "industry": "行业",
    "stock": "个股",
}

VERIFICATION_NAMES = {
    "official": "官方源",
    "verified": "多源验证",
    "single_source": "单源待复核",
    "unverified": "待核实",
    "rumor": "传闻剔除",
}


def item_line(item: dict) -> str:
    related = "、".join(item.get("related_stocks") or item.get("related_industries") or ["-"])
    direction = item.get("impact_hint") or "待判断"
    reasoning = item.get("ai_reasoning") or item.get("summary") or "待补充影响链。"
    verification = VERIFICATION_NAMES.get(item.get("verification_status", ""), item.get("verification_status") or "-")
    time_note = item.get("time_note") or item.get("published_at_confidence", "")
    source_line = (
        f"{item.get('source_name', '-')}, {item.get('published_at', '-')}, "
        f"{verification}, 时间置信度：{item.get('published_at_confidence', 'medium')}"
    )
    return (
        f"- **{item['title']}**（{source_line}, "
        f"{item.get('importance_level', '-')}/{item.get('importance_score', '-')})\n"
        f"  - 相关对象：{related}\n"
        f"  - 影响方向：{direction}\n"
        f"  - 新闻影响链：{reasoning}\n"
        f"  - 时间说明：{time_note or '来源发布时间已标准化'}\n"
    )


def table_row(item: dict) -> str:
    related = "、".join(item.get("related_stocks") or item.get("related_industries") or ["-"])
    action = item.get("follow_up") or "观察"
    return (
        f"| {item.get('importance_level', '-')} | {SECTION_NAMES.get(item.get('section'), item.get('section'))} | "
        f"{item.get('title', '')} | {item.get('impact_hint') or '待判断'} | {related} | {action} |\n"
    )


def source_link(item: dict) -> str:
    url = item.get("url", "")
    if not url:
        return item.get("source_name", "-")
    return f"[{item.get('source_name', '-')}]({url})"


def coverage_lines(data: dict) -> list[str]:
    coverage = data.get("coverage", {})
    round_counts = coverage.get("round_counts", {})
    mcp_status = data.get("mcp_status", {})
    exposure = mcp_status.get("session_exposure", "unknown")
    lines = [
        "",
        "## 信息覆盖度与运行日志",
        "",
        f"- 工作流版本：{data.get('workflow_version', 'daily-v0.1')}",
        f"- 新闻 MCP 本地配置：{'正常' if mcp_status.get('all_scripts_ok') else '需检查'}",
        f"- 当前会话 MCP 暴露状态：{exposure}",
        f"- 证据总数：{coverage.get('total_items', len(data.get('items', [])))}",
    ]
    if round_counts:
        readable = "；".join(f"{key}: {value}" for key, value in round_counts.items())
        lines.append(f"- 采集轮次覆盖：{readable}")
    rejected = coverage.get("rejected_items", [])
    if rejected:
        lines.append(f"- 窗口外剔除：{len(rejected)} 条")
    note = mcp_status.get("session_exposure_note", "")
    if note:
        lines.append(f"- 说明：{note}")
    return lines


def generate_report(scoring_path: Path) -> Path:
    data = json.loads(scoring_path.read_text(encoding="utf-8"))
    items = data.get("items", [])
    top = items[:5]
    lines = [
        f"# A股投研日报 {data['date']}",
        "",
        f"分析区间：{data['window_start']} ~ {data['window_end']}（{data['timezone']}）",
        "",
        "## 今日最重要的 5 条信息",
        "",
        "| 重要性 | 板块 | 事件 | 影响方向 | 相关对象 | 动作 |",
        "|------|------|------|------|------|------|",
    ]
    lines.extend(table_row(item).rstrip() for item in top)
    if not top:
        lines.append("| - | - | 本窗口暂无结构化证据 | - | - | 补充 MCP / web 证据 |")

    for section, name in SECTION_NAMES.items():
        lines.extend(["", f"## {name}", ""])
        section_items = [item for item in items if item.get("section") == section]
        if section_items:
            for item in section_items:
                lines.append(item_line(item).rstrip())
        else:
            lines.append("- 暂无入选信息。")

    followups = [item for item in items if item.get("follow_up")]
    lines.extend(["", "## 今日关注清单", ""])
    if items:
        for item in top:
            lines.append(f"- {item.get('title')}：{item.get('follow_up') or '观察后续验证。'}")
    else:
        lines.append("- 补充可信 MCP / 官方 / 新闻证据后再形成关注清单。")

    lines.extend(["", "## 触发的跟踪任务", ""])
    if followups:
        for item in followups:
            lines.append(f"- {item.get('follow_up')}（来源：{item.get('source_name')}）")
    else:
        lines.append("- 暂无。")

    unverified = [item for item in items if item.get("source_tier") in {"C", "D"} and not item.get("verified_by")]
    unverified.extend(
        item for item in items
        if item.get("verification_status") in {"single_source", "unverified"}
        and item not in unverified
    )
    lines.extend(["", "## 待核实信息", ""])
    if unverified:
        for item in unverified:
            reason = item.get("verification_note") or "需要更高等级来源或第二来源确认。"
            lines.append(f"- {item.get('title')}（{source_link(item)}）：{reason}")
    else:
        lines.append("- 暂无。")

    lines.extend(coverage_lines(data))

    lines.extend(["", "## 风险提示", "", "- 本日报仅供新闻整理和研究跟踪，不构成投资建议。未验证信息不得作为交易依据。"])

    out_path = scoring_path.parent / "日报.md"
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate daily Markdown report from scoring.json.")
    parser.add_argument("scoring", help="Path to scoring.json")
    args = parser.parse_args()
    path = Path(args.scoring)
    if not path.is_absolute():
        path = BASE / path
    out = generate_report(path)
    print(f"wrote {out.relative_to(BASE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
