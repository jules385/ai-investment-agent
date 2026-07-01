from __future__ import annotations

import re
from datetime import date
from pathlib import Path
import shutil

from archive_formatter import AI_CONTENT_END, append_before_marker, frontmatter, write_ai_note
from archive_router import split_stock_key, stock_dir

TODAY = date.today().isoformat()


def stock_index_content(stock_key: str, industry: str) -> str:
    symbol, name = split_stock_key(stock_key)
    return frontmatter({
        "symbol": symbol,
        "name": name,
        "industry": industry,
        "last_updated": TODAY,
        "tags": ["stock"],
    }) + f"""# {stock_key}

## 当前结论

> [!abstract] 当前结论
> 待从最新 Chief 报告维护。

## 文件导航

- [[基本面]]
- [[技术面]]
- [[筹码面]]
- [[情绪面]]
- [[投资决策]]
- [[原始报告/]]
- [[../../跟踪面板/{stock_key}|跟踪面板]]
"""


def dimension_content(stock_key: str, title: str, industry: str) -> str:
    symbol, name = split_stock_key(stock_key)
    return frontmatter({
        "symbol": symbol,
        "name": name,
        "industry": industry,
        "dimension": title.replace(".md", ""),
        "last_updated": TODAY,
        "tags": ["stock", "dimension"],
    }) + f"# {stock_key} {title.replace('.md', '')}\n\n"


def tracking_content(stock_key: str, industry: str) -> str:
    symbol, name = split_stock_key(stock_key)
    return frontmatter({
        "symbol": symbol,
        "name": name,
        "industry": industry,
        "last_updated": TODAY,
        "tags": ["tracking"],
    }) + f"""# {stock_key} 跟踪面板

## 核心假设追踪

| 假设 | 对应逻辑 | 当前状态 | 最新证据 | 证伪条件 | 更新时间 |
|------|----------|:--:|---------|---------|---------|

## 主要跟踪指标

| 指标 | 当前值 | 阈值 | 状态 | 频率 | 对应逻辑 | 数据来源 |
|------|-------|------|:--:|------|----------|----------|

## 跟踪日志

| 日期 | 类型 | 新变化 | 影响方向 | 更新了哪条逻辑 | 来源 |
|------|------|--------|:--:|----------------|------|

## 下次跟踪指引

- [ ] 补充下一次跟踪任务
"""


def industry_content(industry: str, stock_key: str) -> str:
    return frontmatter({
        "industry_name": industry,
        "stocks": [stock_key],
        "last_updated": TODAY,
        "tags": ["industry"],
    }) + f"# {industry}\n\n## 相关标的\n\n- [[个股逻辑/{stock_key}/_index|{stock_key}]]\n"


def ensure_baseline_files(base: Path, stock_key: str, industry: str, overwrite: bool = False) -> None:
    files = {
        f"个股逻辑/{stock_key}/_index.md": stock_index_content(stock_key, industry),
        f"个股逻辑/{stock_key}/基本面.md": dimension_content(stock_key, "基本面.md", industry),
        f"个股逻辑/{stock_key}/技术面.md": dimension_content(stock_key, "技术面.md", industry),
        f"个股逻辑/{stock_key}/筹码面.md": dimension_content(stock_key, "筹码面.md", industry),
        f"个股逻辑/{stock_key}/情绪面.md": dimension_content(stock_key, "情绪面.md", industry),
        f"个股逻辑/{stock_key}/投资决策.md": dimension_content(stock_key, "投资决策.md", industry),
        f"跟踪面板/{stock_key}.md": tracking_content(stock_key, industry),
        f"行业知识库/{industry}.md": industry_content(industry, stock_key),
    }
    legacy_raw_file = base / f"个股逻辑/{stock_key}/原始摘录.md"
    if legacy_raw_file.exists():
        legacy_raw_file.unlink()
    (base / f"个股逻辑/{stock_key}/原始报告").mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        path = base / rel
        if rel.startswith("跟踪面板/") and path.exists():
            continue
        if overwrite or not path.exists():
            write_ai_note(path, content, format_content=False)


def copy_raw_reports(base: Path, source: Path, stock_key: str, overwrite: bool = True) -> list[Path]:
    """Copy source Markdown reports verbatim; this step is not AI-classified."""
    target_dir = base / f"个股逻辑/{stock_key}/原始报告"
    target_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    if source.is_dir():
        files = sorted(p for p in source.rglob("*.md") if p.is_file())
        root = source
    else:
        files = [source] if source.suffix.lower() == ".md" else []
        root = source.parent
    for src in files:
        rel = src.relative_to(root)
        dst = target_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if overwrite or not dst.exists():
            shutil.copy2(src, dst)
        copied.append(dst)
    return copied


def append_update(base: Path, target_file: str, target_section: str, block: str) -> Path:
    path = base / target_file
    if not path.exists():
        write_ai_note(path, f"# {Path(target_file).stem}\n\n", format_content=False)
    if target_section:
        wrapped = f"## {target_section}\n\n{block.strip()}\n"
    else:
        wrapped = block.strip() + "\n"
    append_before_marker(path, wrapped)
    return path


def append_decision_log(
    base: Path,
    stock_key: str,
    source_file: str,
    source_path: Path,
    conclusion: str,
    logic_change: bool = False,
    effective_date: str = "",
) -> Path:
    path = base / f"{stock_dir(stock_key)}/投资决策.md"
    if not path.exists():
        write_ai_note(path, dimension_content(stock_key, "投资决策.md", ""), format_content=False)
    date_text = effective_date or TODAY
    change_text = "是" if logic_change else "否"
    row = (
        f"| {date_text} | 跟踪报告 | {conclusion} | {change_text} | "
        f"`{source_file}` | `{source_path.as_posix()}` |\n"
    )
    text = path.read_text(encoding="utf-8")
    if row.strip() in text:
        return path
    heading = "## 跟踪记录"
    table = (
        f"{heading}\n\n"
        "| 日期 | 类型 | 结论 | 是否改变逻辑 | 来源文件 | 原文路径 |\n"
        "|------|------|------|:--:|----------|----------|\n"
    )
    if heading not in text:
        append_before_marker(path, table + row)
        return path
    if "| 日期 | 类型 | 结论 | 是否改变逻辑 | 来源文件 | 原文路径 |" not in text:
        text = text.replace(heading, table.rstrip(), 1)
    marker = AI_CONTENT_END
    if marker in text:
        ai, user = text.split(marker, 1)
        text = ai.rstrip() + "\n" + row + "\n\n" + marker + user
    else:
        text = text.rstrip() + "\n" + row
    text = re.sub(r"\n{2,}(\| \d{4}-\d{2}-\d{2} \|)", r"\n\1", text)
    path.write_text(text, encoding="utf-8")
    return path


def replace_summary(base: Path, target_file: str, target_section: str, block: str) -> Path:
    path = base / target_file
    if not path.exists():
        write_ai_note(path, f"# {Path(target_file).stem}\n\n", format_content=False)
    text = path.read_text(encoding="utf-8")
    marker = AI_CONTENT_END
    ai, user = (text.split(marker, 1) + [""])[:2] if marker in text else (text, "")
    heading = f"## {target_section}" if target_section else "## 当前结论"
    pattern = re.compile(rf"^{re.escape(heading)}\n[\s\S]*?(?=^## |\Z)", re.MULTILINE)
    replacement = f"{heading}\n\n{block.strip()}\n\n"
    if pattern.search(ai):
        ai = pattern.sub(replacement, ai)
    else:
        ai = ai.rstrip() + "\n\n" + replacement
    content = ai.rstrip() + f"\n\n{marker}\n" + (user.strip() + "\n" if user.strip() else "")
    path.write_text(content, encoding="utf-8")
    write_ai_note(path, path.read_text(encoding="utf-8").split(marker, 1)[0])
    return path


def append_tracking_task(base: Path, stock_key: str, item: str) -> None:
    path = base / f"跟踪面板/{stock_key}.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if item in text:
        return
    marker = "## 下次跟踪指引"
    if marker in text:
        text = text.replace(marker, marker + f"\n\n- [ ] {item}", 1)
        path.write_text(text, encoding="utf-8")
