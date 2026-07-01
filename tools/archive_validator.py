from __future__ import annotations

from pathlib import Path

from archive_formatter import AI_CONTENT_END


def validate_note(path: Path) -> list[str]:
    issues: list[str] = []
    if not path.exists():
        return [f"missing: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    if AI_CONTENT_END not in text:
        issues.append("missing ai-content marker")
    if "\ufffd" in text:
        issues.append("contains replacement character �")
    if "???" in text:
        issues.append("contains suspicious ??? sequence")
    if "原文摘录：" in text:
        issues.append("contains deprecated 原文摘录 wrapper")
    if "[!quote] 来源" in text:
        issues.append("contains repeated source callout wrapper")
    question_ratio = text.count("?") / max(1, len(text))
    if text.count("?") >= 20 and question_ratio > 0.01:
        issues.append("contains unusually many question marks")
    return issues
