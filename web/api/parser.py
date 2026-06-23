import re
from datetime import datetime
from pathlib import Path


EMPTY_WORKSPACE = {
    "stocks_parsed": 0,
    "industries": {},
    "theses": {},
    "tracking": {},
    "stocks": {},
}


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def clean_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("**", "").replace("<br>", " ")).strip()


def parse_markdown_tables(text: str) -> list[dict]:
    tables = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line.startswith("|"):
            index += 1
            continue

        block = []
        while index < len(lines) and lines[index].strip().startswith("|"):
            block.append(lines[index].strip())
            index += 1

        if len(block) < 2 or not re.search(r"\|[\s:\-]+\|", block[1]):
            continue

        headers = [clean_cell(cell) for cell in block[0].strip("|").split("|")]
        rows = []
        for row_line in block[2:]:
            cells = [clean_cell(cell) for cell in row_line.strip("|").split("|")]
            if len(cells) < len(headers):
                cells.extend([""] * (len(headers) - len(cells)))
            rows.append(dict(zip(headers, cells[: len(headers)])))
        tables.append({"headers": headers, "rows": rows})
    return tables


def section_after_heading(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return ""
    start = match.start()
    next_heading = re.search(r"\n#{1,3}\s+", text[match.end() :])
    if next_heading:
        return text[start : match.end() + next_heading.start()]
    return text[start:]


def extract_industry_chain(text: str) -> list[dict]:
    section = section_after_heading(text, r"#{2,4}\s*1\.1\s*.*?产业链")
    if not section:
        section = section_after_heading(text, r"产业链")
    if not section:
        return []

    chain = []
    current = None
    for raw_line in section.splitlines():
        line = raw_line.strip()
        name_match = re.search(r"(?:├──|└──|[-*])\s*子环节\d*[：:]\s*(.+)", line)
        if name_match:
            current = {
                "name": clean_cell(name_match.group(1)),
                "representatives": "",
                "gross_margin": "",
                "barrier": "",
            }
            chain.append(current)
            continue
        if not current:
            continue
        for key, label in (
            ("representatives", "代表"),
            ("gross_margin", "毛利率"),
            ("barrier", "壁垒"),
        ):
            value_match = re.search(rf"{label}[：:]\s*(.+)", line)
            if value_match:
                current[key] = clean_cell(value_match.group(1))
    return chain


def extract_financials(text: str) -> list[dict]:
    wanted_rows = {
        "营业收入": "revenue",
        "归母净利润": "net_profit",
        "净利润": "net_profit",
        "毛利率": "gross_margin",
        "净利率": "net_margin",
        "ROE": "roe",
    }
    records: dict[str, dict] = {}

    for table in parse_markdown_tables(text):
        headers = table["headers"]
        metric_header = headers[0] if headers else ""
        year_headers = [header for header in headers[1:] if re.search(r"20\d{2}", header)]
        if not year_headers or not any("指标" in header or "报告期" in header for header in headers[:1]):
            continue

        if "报告期" in metric_header:
            for row in table["rows"][-5:]:
                period = row.get(metric_header, "")
                if not period:
                    continue
                records.setdefault(period, {"period": period})
                for header, key in (
                    ("营收", "revenue"),
                    ("归母净利", "net_profit"),
                    ("毛利率", "gross_margin"),
                    ("净利率", "net_margin"),
                    ("ROE", "roe"),
                ):
                    for column, value in row.items():
                        if header in column and value:
                            records[period][key] = value
            continue

        for row in table["rows"]:
            metric = row.get(metric_header, "")
            metric_key = None
            for label, key in wanted_rows.items():
                if label in metric:
                    metric_key = key
                    break
            if not metric_key:
                continue
            for period in year_headers[-5:]:
                records.setdefault(period, {"period": period})
                records[period][metric_key] = row.get(period, "")

    def period_sort_key(item: dict) -> str:
        return item.get("period", "")

    return sorted(records.values(), key=period_sort_key)[-5:]


def extract_investment_thesis(text: str) -> dict:
    thesis = {
        "summary": "",
        "bull": [],
        "bear": [],
        "signals": [],
        "raw": "",
        "parsed": True,
    }

    story = section_after_heading(text, r"#{2,3}\s*(核心投资故事|核心结论|投资决策|结论)")
    if story:
        paragraphs = [line.strip() for line in story.splitlines() if line.strip() and not line.startswith("#")]
        thesis["summary"] = clean_cell(paragraphs[0]) if paragraphs else ""

    for table in parse_markdown_tables(text):
        headers = table["headers"]
        if {"维度", "方向"}.issubset(set(headers)):
            for row in table["rows"]:
                thesis["signals"].append(row)

    for line in text.splitlines():
        clean = clean_cell(line)
        if re.search(r"(看多|强化|维持|优势|机会|白名单|核心持仓)", clean):
            thesis["bull"].append(clean.lstrip("-*> "))
        if re.search(r"(看空|风险|回调|弱化|降级|止损|预警)", clean):
            thesis["bear"].append(clean.lstrip("-*> "))

    yaml_match = re.search(r"```ya?ml\s+(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if yaml_match and ("signal:" in yaml_match.group(1) or "direction:" in yaml_match.group(1)):
        thesis["raw"] = yaml_match.group(1).strip()
        thesis["parsed"] = False

    thesis["bull"] = thesis["bull"][:8]
    thesis["bear"] = thesis["bear"][:8]
    return thesis


def row_status(row: dict) -> str:
    joined = " ".join(row.values())
    if "🔴" in joined or "低于阈值" in joined or "风险" in joined:
        return "red"
    if "⚠️" in joined or "🟡" in joined or "关注" in joined or "弱化" in joined:
        return "yellow"
    if "✅" in joined or "🟢" in joined or "优秀" in joined or "强化" in joined:
        return "green"
    return "neutral"


def extract_tracking_indicators(text: str) -> list[dict]:
    indicators = []
    for table in parse_markdown_tables(text):
        headers = table["headers"]
        joined_headers = " ".join(headers)
        if not re.search(r"(指标|检查项|假设|触发条件)", joined_headers):
            continue
        for row in table["rows"]:
            name = row.get("指标") or row.get("检查项") or row.get("上次核心假设") or row.get(headers[0], "")
            if not name:
                continue
            indicators.append(
                {
                    "name": name,
                    "frequency": row.get("频率", row.get("报告期", "")),
                    "threshold": row.get("阈值", row.get("触发条件", "")),
                    "status": row_status(row),
                    "detail": row,
                }
            )
    return indicators[:30]


def extract_events(text: str) -> list[dict]:
    events = []
    for table in parse_markdown_tables(text):
        for row in table["rows"]:
            joined = " ".join(row.values())
            if "🔴" not in joined and "🟡" not in joined:
                continue
            events.append(
                {
                    "level": "red" if "🔴" in joined else "yellow",
                    "title": next((value for value in row.values() if value), "事件"),
                    "detail": row,
                }
            )
    return events[:30]


def parse_single_report(report_path: str | Path) -> dict:
    path = Path(report_path)
    text = read_text(path)
    return {
        "path": str(path),
        "stock": path.stem,
        "industry_chain": extract_industry_chain(text),
        "financials": extract_financials(text),
        "thesis": extract_investment_thesis(text),
        "tracking_indicators": extract_tracking_indicators(text),
        "events": extract_events(text),
    }


def stock_identity(stock_dir: Path) -> tuple[str, str, str]:
    match = re.match(r"(?P<code>\d{6})-(?P<name>.+)", stock_dir.name)
    if not match:
        return stock_dir.name, stock_dir.name, stock_dir.name
    return stock_dir.name, match.group("code"), match.group("name")


def latest_file(files: list[Path]) -> Path | None:
    if not files:
        return None
    return sorted(files, key=lambda item: (item.stat().st_mtime, item.name))[-1]


def infer_industry(stock_name: str, chain: list[dict], text: str) -> str:
    if "PCB" in text or "沪电" in stock_name or any("PCB" in item.get("name", "") for item in chain):
        return "半导体/电子"
    if "光纤" in text:
        return "通信"
    if "风电" in text:
        return "新能源"
    return "未分类"


def parse_stock_dir(stock_dir: Path) -> dict | None:
    stock_key, code, name = stock_identity(stock_dir)
    markdown_files = sorted(stock_dir.rglob("*.md"))
    if not markdown_files:
        return None

    initial_dir = stock_dir / "01-初次覆盖"
    fundamental = latest_file(list(initial_dir.glob("子报告-基本面分析师*.md"))) if initial_dir.exists() else None
    chief = latest_file(list(initial_dir.glob("*覆盖报告*.md"))) if initial_dir.exists() else None
    primary = fundamental or latest_file(markdown_files)

    primary_text = read_text(primary) if primary else ""
    chief_text = read_text(chief) if chief else ""
    combined_initial = "\n\n".join(part for part in (chief_text, primary_text) if part)

    tracking_texts = []
    for folder in stock_dir.iterdir():
        if folder.is_dir() and re.match(r"0[234]-", folder.name):
            for report in sorted(folder.glob("*.md")):
                tracking_texts.append(read_text(report))
    tracking_text = "\n\n".join(tracking_texts)

    chain = extract_industry_chain(primary_text)
    financials = extract_financials(primary_text + "\n\n" + tracking_text)
    thesis = extract_investment_thesis(combined_initial or primary_text)
    indicators = extract_tracking_indicators(primary_text + "\n\n" + tracking_text)
    events = extract_events(tracking_text)
    industry = infer_industry(name, chain, primary_text + chief_text)

    return {
        "code": code,
        "name": name,
        "stock": stock_key,
        "format": "standard" if fundamental and chief else "legacy",
        "industry": industry,
        "industry_chain": chain,
        "financials": financials,
        "thesis": thesis,
        "tracking_indicators": indicators,
        "events": events,
        "source_files": [str(path) for path in markdown_files],
    }


def parse_all_reports(reports_dir: str | Path | None = None) -> dict:
    if reports_dir is None:
        return EMPTY_WORKSPACE.copy()

    root = Path(reports_dir)
    workspace = {
        "stocks_parsed": 0,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "industries": {},
        "theses": {},
        "tracking": {},
        "stocks": {},
    }
    if not root.exists():
        return workspace

    for stock_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        parsed = parse_stock_dir(stock_dir)
        if not parsed:
            continue

        stock_key = parsed["stock"]
        workspace["stocks"][stock_key] = parsed
        workspace["theses"][stock_key] = parsed["thesis"]
        workspace["tracking"][stock_key] = {
            "indicators": parsed["tracking_indicators"],
            "events": parsed["events"],
        }

        industry = parsed["industry"]
        industry_data = workspace["industries"].setdefault(
            industry,
            {"name": industry, "stocks": [], "chain": []},
        )
        industry_data["stocks"].append({"stock": stock_key, "code": parsed["code"], "name": parsed["name"]})
        if parsed["industry_chain"] and not industry_data["chain"]:
            industry_data["chain"] = parsed["industry_chain"]

    workspace["stocks_parsed"] = len(workspace["stocks"])
    return workspace
