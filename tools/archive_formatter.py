from __future__ import annotations

import re
from pathlib import Path
from typing import Any

AI_CONTENT_END = "<!-- /ai-content -->"

NOTE_RE = re.compile(r"(综合评分|综合得分|判断|结论|综合来看|综合评估|总分|综合打分|评级|投资决策|建议评级)")
RISK_HEADING_RE = re.compile(r"风险")
CATALYST_HEADING_RE = re.compile(r"催化|触发")
GAP_HEADING_RE = re.compile(r"缺口|待补")


def yaml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(f'"{str(item)}"' for item in value) + "]"
    return f'"{str(value).replace(chr(34), chr(92) + chr(34))}"'


def frontmatter(fields: dict[str, Any]) -> str:
    lines = ["---"]
    lines.extend(f"{key}: {yaml_value(value)}" for key, value in fields.items())
    lines.extend(["---", ""])
    return "\n".join(lines)


def format_markdown(ai_part: str) -> str:
    result: list[str] = []
    in_code = False
    section_kind = ""

    for line in ai_part.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            result.append(line)
            continue
        if in_code or not stripped:
            result.append(line)
            continue

        if stripped.startswith("#"):
            heading_text = stripped.lstrip("#").strip()
            if RISK_HEADING_RE.search(heading_text):
                section_kind = "risk"
            elif CATALYST_HEADING_RE.search(heading_text):
                section_kind = "catalyst"
            elif GAP_HEADING_RE.search(heading_text):
                section_kind = "gap"
            else:
                section_kind = ""
            result.append(line)
            continue

        if stripped.startswith(("|", ">")):
            result.append(line)
            continue

        if section_kind == "risk" and re.match(r"^[-*]\s+", stripped):
            result.append(f"> [!warning] {stripped[2:].strip()}")
            continue
        if section_kind == "catalyst" and re.match(r"^[-*]\s+", stripped):
            result.append(f"> [!tip] {stripped[2:].strip()}")
            continue
        if section_kind == "gap" and re.match(r"^[-*]\s+", stripped):
            result.append(f"> [!failure] {stripped[2:].strip()}")
            continue
        if NOTE_RE.search(stripped) and not re.match(r"^[-*]\s+", stripped):
            result.append(f"> [!note] {stripped}")
            continue

        result.append(line)

    return "\n".join(result).strip()


def preserve_user_part(existing: str) -> str:
    if AI_CONTENT_END not in existing:
        return ""
    return existing.split(AI_CONTENT_END, 1)[1].strip()


def write_ai_note(path: Path, ai_content: str, *, format_content: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    user_part = preserve_user_part(path.read_text(encoding="utf-8")) if path.exists() else ""
    body = format_markdown(ai_content) if format_content else ai_content.strip()
    content = body.rstrip() + f"\n\n{AI_CONTENT_END}\n"
    if user_part:
        content += "\n" + user_part + "\n"
    path.write_text(content, encoding="utf-8")


def append_before_marker(path: Path, block: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if block.strip() in existing:
            return
        if AI_CONTENT_END in existing:
            updated = existing.replace(AI_CONTENT_END, block.rstrip() + f"\n\n{AI_CONTENT_END}")
            path.write_text(updated, encoding="utf-8")
            return
        path.write_text(existing.rstrip() + "\n\n" + block.rstrip() + "\n", encoding="utf-8")
    else:
        path.write_text(block.rstrip() + f"\n\n{AI_CONTENT_END}\n", encoding="utf-8")
