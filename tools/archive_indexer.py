from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from archive_schema import ArchiveSection

TODAY = date.today().isoformat()


@dataclass
class ArchiveSummary:
    stock_sections: int = 0
    industry_sections: int = 0
    skipped_sections: int = 0
    sources: set[str] = field(default_factory=set)
    knowledge_types: set[str] = field(default_factory=set)
    copied_sections: list[ArchiveSection] = field(default_factory=list)


def split_stock_key(stock_key: str) -> tuple[str, str]:
    match = re.match(r"^(\d{6})[-_ ]?(.*)", stock_key)
    if match:
        return match.group(1), match.group(2).strip()
    return stock_key, stock_key


def source_callout(source_file: str, source_path: Path, report_type: str = "") -> str:
    report_label = f"类型：{report_type}\n> " if report_type else ""
    return (
        "> [!quote] 来源\n"
        f"> 文件：`{source_path.as_posix()}`\n"
        f"> {report_label}入库日期：{TODAY}\n"
    )


def stock_index_card(stock_key: str, industry: str, summary: ArchiveSummary) -> str:
    symbol, name = split_stock_key(stock_key)
    types = "、".join(sorted(summary.knowledge_types)) or "暂无"
    sources = "、".join(sorted(summary.sources)) or "暂无"
    return f"""## Codex 索引卡片

> [!abstract] {name}（{symbol}）
> 行业：[[行业知识库/{industry}|{industry}]]
> 本次入库：个股章节 {summary.stock_sections} 个，跳过 {summary.skipped_sections} 个。

### 本次知识类型

{types}

### 来源文件

{sources}

### 核心假设追踪

| 假设 | 状态 | 最新证据 | 证伪条件 | 来源 |
|------|:--:|---------|---------|------|
| 待Codex从后续研究中维护 | ⚪ | | | |

### 跟踪指标

| 指标 | 当前值 | 阈值 | 状态 | 频率 | 来源 |
|------|-------|------|:--:|------|------|
| 待Codex从后续研究中维护 | | | ⚪ | | |

### 事件时间线

| 日期 | 类型 | 事件 | 影响方向 | 来源 |
|------|------|------|:--:|------|
| {TODAY} | 入库 | 新增研究成果入库 | ⚪ | {sources} |
"""


def industry_index_card(industry: str, stock_key: str, summary: ArchiveSummary) -> str:
    symbol, name = split_stock_key(stock_key)
    types = "、".join(sorted(summary.knowledge_types)) or "暂无"
    return f"""## Codex 行业卡片

> [!info] {industry}
> 关联标的：[[个股逻辑/{stock_key}|{name}]]
> 本次入库：行业章节 {summary.industry_sections} 个。

### 本次行业知识类型

{types}

### 相关标的

- [[个股逻辑/{stock_key}|{name}]]（{symbol}）
"""


def validate_note(path: Path) -> list[str]:
    issues: list[str] = []
    if not path.exists():
        return [f"missing: {path}"]
    text = path.read_text(encoding="utf-8")
    if "<!-- /ai-content -->" not in text:
        issues.append("missing ai-content marker")
    if "Codex 索引卡片" not in text and "Codex 行业卡片" not in text:
        issues.append("missing Codex index card")
    if "> [!" not in text:
        issues.append("missing Obsidian callouts")
    return issues
