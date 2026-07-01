#!/usr/bin/env python3
"""
Sync reports/workspace-data.json + reports/*.md → obsidian-vault/
Usage: python tools/sync-to-vault.py
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[1]
WORKSPACE_JSON = BASE / "reports" / "workspace-data.json"
VAULT = BASE / "obsidian-vault"
STOCK_DIR = VAULT / "个股逻辑"
INDUSTRY_DIR = VAULT / "行业知识库"
PORTFOLIO_DIR = VAULT / "组合管理"
TODAY = date.today().isoformat()

# User content below this marker is preserved on re-sync
AI_CONTENT_END = "<!-- /ai-content -->"


# ---------------------------------------------------------------------------
# utilities
# ---------------------------------------------------------------------------

def as_list(v: Any) -> list:
    if isinstance(v, list):
        return v
    return [] if v in (None, "") else [v]


def scalar(v: Any, default: str = "") -> str:
    if v in (None, ""):
        return default
    if isinstance(v, dict):
        for k in ("statement", "description", "name", "text"):
            if v.get(k):
                return str(v[k])
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def yaml_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(f'"{i}"' for i in v) + "]"
    return f'"{str(v).replace(chr(34), chr(92)+chr(34))}"'


def score(v: Any) -> int | float:
    if v in (None, ""):
        return 0
    if isinstance(v, (int, float)):
        return v
    m = re.search(r"-?\d+(?:\.\d+)?", str(v))
    return float(m.group()) if m else 0


def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name).strip() or "unknown"


def split_stock_key(key: str) -> tuple[str, str]:
    m = re.match(r"^(\d{6})[-_ ]?(.*)", key)
    return (m.group(1), m.group(2).strip()) if m else (key, key)


def status_emoji(s: Any) -> str:
    return {"green": "🟢", "normal": "🟢", "yellow": "🟡", "warning": "🟡",
            "red": "🔴", "triggered": "🔴"}.get(str(s or "").lower(), "⚪")


def severity_emoji(s: Any) -> str:
    return {"high": "🔴", "critical": "🔴", "medium": "🟠", "major": "🟠",
            "low": "🟡", "minor": "🟡"}.get(str(s or "").lower(), "⚪")


def direction_signal(thesis: dict, key: str) -> dict:
    sig = (thesis.get("signals") or {}).get(key) or {}
    return {"direction": sig.get("direction") or "unknown", "score": score(sig.get("score"))}


def build_industry_lookup(industries: dict) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for iname, ind in industries.items():
        for item in as_list((ind or {}).get("stocks")):
            k = item.get("stock") if isinstance(item, dict) else str(item)
            if k:
                lookup[k] = iname
    return lookup


# ---------------------------------------------------------------------------
# Obsidian-native rendering
# ---------------------------------------------------------------------------

def render_chain_mermaid(chain: Any) -> str:
    items = as_list(chain)
    if not items or len(items) < 2:
        return "\n".join(f"- {scalar(i)}" for i in items) if items else "暂无"
    tier_zh = {"upstream": "上游", "midstream": "中游", "downstream": "下游"}
    lines = ["```mermaid", "graph TD"]
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            lines.append(f'  N{i}["{item}"]')
            continue
        name = item.get("name", "")
        tier = tier_zh.get(item.get("tier", ""), "")
        gm = item.get("gross_margin", "")
        cos = item.get("companies", "")
        label = f"{name}" + (f"<br/>{tier}" if tier else "") + (f"<br/>毛利率 {gm}" if gm else "")
        lines.append(f'  N{i}["{label}"]')
        if cos:
            lines.append(f'  N{i} -.-> C{i}(("{cos[:30]}"))')
    for i in range(len(items) - 1):
        lines.append(f"  N{i} --> N{i+1}")
    lines.append("```")
    return "\n".join(lines)


def render_tam(tam: Any) -> str:
    if not isinstance(tam, dict):
        return str(tam or "暂无")
    rows = []
    labels = [("market_size", "市场规模"), ("cagr", "CAGR"), ("forecast_year", "预测年份")]
    for k, label in labels:
        v = tam.get(k, "")
        if v and v not in ("报告提及行业需求增长", "报告提及成长性"):
            rows.append(f"- **{label}**：{v}")
    for k, v in tam.items():
        if k not in dict(labels) and v:
            rows.append(f"- **{k}**：{v}")
    return "\n".join(rows) or "暂无"


def render_financials(fin: Any) -> str:
    if not isinstance(fin, dict):
        return str(fin or "暂无")
    header = "| 公司 | 营收 | 净利润 | 毛利率 | PE |\n|------|------|--------|------|-----|"
    rows = []
    for co, d in fin.items():
        if not isinstance(d, dict):
            rows.append(f"| {co} | {d} | | | |")
            continue
        rows.append(f"| {co} | {d.get('revenue','')} | {d.get('net_profit','')} | {d.get('gross_margin','')} | {d.get('pe','')} |")
    return (header + "\n" + "\n".join(rows)) if rows else "暂无"


def render_bull_bear(theses: list, callout: str, label: str) -> str:
    if not theses:
        return f"> [{callout}] 暂无{label}逻辑\n"
    parts = []
    for item in theses:
        if not isinstance(item, dict):
            parts.append(f"> [{callout}] {item}\n")
            continue
        stmt = item.get("statement", scalar(item))
        evidence = item.get("evidence", "")
        assume = item.get("key_assumption", item.get("assumption", ""))
        trigger = item.get("trigger_condition", "")
        status = item.get("status", "")
        lines = [f"> [{callout}] {stmt}"]
        if evidence:
            lines.append(f"> **依据**：{evidence}")
        if assume:
            lines.append(f"> **关键假设**：{assume}")
        if trigger:
            lines.append(f"> **触发条件**：{trigger}")
        if status:
            lines.append(f"> **状态**：{status}")
        parts.append("\n".join(lines) + "\n")
    return "\n".join(parts)


def render_indicators_table(indicators: list) -> str:
    if not indicators:
        return "| 指标 | 当前值 | 阈值 | 状态 | 频率 |\n|------|-------|------|:--:|----|\n| 暂无 | | | | |"
    header = "| 指标 | 当前值 | 阈值 | 状态 | 频率 |\n|------|-------|------|:--:|----|"
    rows = []
    for item in indicators:
        if not isinstance(item, dict):
            rows.append(f"| {item} | | | ⚪ | |")
            continue
        rows.append(
            f"| {item.get('name','')} | {item.get('latest_value','')} | "
            f"{item.get('threshold','')} | {status_emoji(item.get('status'))} | "
            f"{item.get('frequency','')} |"
        )
    return header + "\n" + "\n".join(rows)


# ---------------------------------------------------------------------------
# Note renderers
# ---------------------------------------------------------------------------

def render_stock_note(stock_key: str, thesis: dict, tracking: dict, industry: str) -> str:
    sym, name = split_stock_key(stock_key)
    bull = as_list(thesis.get("bull_theses"))
    bear = as_list(thesis.get("bear_theses"))
    indicators = as_list((tracking or {}).get("indicators"))
    events = as_list((tracking or {}).get("events"))
    decisions = as_list((tracking or {}).get("decisions"))
    f = direction_signal(thesis, "fundamental")
    c = direction_signal(thesis, "chip_flow")
    t = direction_signal(thesis, "technical")
    s = direction_signal(thesis, "sentiment")

    fm = {
        "symbol": sym, "name": name, "industry": industry or "unknown",
        "bull_count": len(bull), "bear_count": len(bear),
        "fundamental_direction": f["direction"], "fundamental_score": f["score"],
        "chip_flow_direction": c["direction"], "chip_flow_score": c["score"],
        "technical_direction": t["direction"], "technical_score": t["score"],
        "sentiment_direction": s["direction"], "sentiment_score": s["score"],
        "indicators_count": len(indicators), "events_count": len(events),
        "last_updated": TODAY, "tags": ["stock"],
    }

    lines = ["---"]
    lines += [f"{k}: {yaml_value(v)}" for k, v in fm.items()]
    lines += ["---", ""]

    # Header callout
    lines += [
        f"> [!abstract] {name}（{sym}）",
        f"> 行业：{industry} ｜ 基本面 {f['score']} · 筹码 {c['score']} · 技术 {t['score']} · 情绪 {s['score']}",
        "",
    ]

    lines += ["## 多方逻辑", ""]
    lines.append(render_bull_bear(bull, "success", "多方"))

    lines += ["## 空方逻辑", ""]
    lines.append(render_bull_bear(bear, "danger", "空方"))

    lines += ["## 跟踪指标", "", render_indicators_table(indicators), ""]

    lines += ["## 近期事件", ""]
    if events:
        for ev in events:
            if isinstance(ev, dict):
                lines.append(f"- {ev.get('date','')} {severity_emoji(ev.get('severity'))} {ev.get('description', scalar(ev))}")
            else:
                lines.append(f"- {ev}")
    else:
        lines.append("- 暂无")

    if decisions:
        lines += ["", "## 决策记录", "| 日期 | 操作 | 评级 | 理由 |", "|------|------|:--:|------|"]
        for d in decisions:
            if isinstance(d, dict):
                lines.append(f"| {d.get('date','')} | {d.get('action','')} | {d.get('rating','')} | {d.get('rationale','')} |")

    return "\n".join(lines) + "\n"


def render_industry_note(name: str, ind: dict) -> str:
    stocks = []
    for item in as_list(ind.get("stocks")):
        stocks.append(item.get("stock") if isinstance(item, dict) else str(item))
    stocks = [s for s in stocks if s]
    fin = ind.get("financial_benchmarks") or ind.get("financials") or {}
    tam = ind.get("tam_cagr") or {}

    fm = {
        "industry_name": name,
        "stock_count": len(stocks),
        "chain_count": len(as_list(ind.get("chain"))),
        "has_tam": bool(tam),
        "has_financials": bool(fin),
        "stocks": stocks,
        "last_updated": TODAY,
        "tags": ["industry"],
    }

    lines = ["---"]
    lines += [f"{k}: {yaml_value(v)}" for k, v in fm.items()]
    lines += ["---", ""]

    # Header callout with linked stocks
    stock_links = " · ".join(f"[[个股逻辑/{s}|{s.split('-',1)[-1] if '-' in s else s}]]" for s in stocks)
    if tam.get("market_size") or tam.get("cagr"):
        snap = f"市场规模 {tam.get('market_size','')} · CAGR {tam.get('cagr','')}"
    else:
        snap = f"覆盖 {len(stocks)} 个标的"
    lines += [f"> [!info] {name}", f"> {snap}", f"> 标的：{stock_links}", ""]

    lines += ["## 产业链", "", render_chain_mermaid(ind.get("chain")), ""]
    lines += ["## 市场空间（TAM / CAGR）", "", render_tam(tam), ""]
    lines += ["## 核心公司财务对比", "", render_financials(fin), ""]

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Incremental merge (preserve user notes below AI_CONTENT_END marker)
# ---------------------------------------------------------------------------

def write_note(path: Path, ai_content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if AI_CONTENT_END in existing:
            user_part = existing.split(AI_CONTENT_END, 1)[1].strip()
            if user_part:
                path.write_text(
                    ai_content.rstrip() + f"\n\n{AI_CONTENT_END}\n\n{user_part}\n",
                    encoding="utf-8",
                )
                return
    path.write_text(ai_content.rstrip() + f"\n\n{AI_CONTENT_END}\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Portfolio sync (reports/*.md → vault/组合管理/)
# ---------------------------------------------------------------------------

PORTFOLIO_FILES = {
    "白名单": BASE / "reports" / "白名单组合.md",
    "持仓名单": BASE / "reports" / "持仓组合.md",
    "黑名单": BASE / "reports" / "黑名单组合.md",
}

STOCK_LINK_RE = re.compile(r"\|\s*(\d{6})\s*\|\s*([^|]+?)\s*\|")


def sync_portfolio(theses_keys: list[str]) -> None:
    """Inject [[个股逻辑/...]] links into vault/组合管理/ files."""
    # Build lookup: code → stock_key
    code_to_key = {}
    for k in theses_keys:
        sym, _ = split_stock_key(k)
        code_to_key[sym] = k

    for portfolio_name, src_path in PORTFOLIO_FILES.items():
        vault_path = PORTFOLIO_DIR / f"{portfolio_name}.md"
        if not src_path.exists() or not vault_path.exists():
            continue

        src = src_path.read_text(encoding="utf-8")
        vault_content = vault_path.read_text(encoding="utf-8")

        # Replace plain code cells with wikilinks
        def linkify(m: re.Match) -> str:
            code = m.group(1).strip()
            name = m.group(2).strip()
            key = code_to_key.get(code, f"{code}-{name}")
            return f"| {code} | [[个股逻辑/{key}\\|{name}]] |"

        new_content = STOCK_LINK_RE.sub(linkify, vault_content)
        if new_content != vault_content:
            vault_path.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main sync
# ---------------------------------------------------------------------------

def sync() -> tuple[int, int]:
    if not WORKSPACE_JSON.exists():
        print("workspace-data.json not found — run update-workspace.py first", file=sys.stderr)
        return 0, 0

    with WORKSPACE_JSON.open(encoding="utf-8") as f:
        data = json.load(f)

    industries = data.get("industries") or {}
    theses = data.get("theses") or {}
    tracking = data.get("tracking") or {}

    STOCK_DIR.mkdir(parents=True, exist_ok=True)
    INDUSTRY_DIR.mkdir(parents=True, exist_ok=True)

    ind_lookup = build_industry_lookup(industries)
    stocks_synced = 0
    for stock_key, thesis_val in sorted(theses.items()):
        thesis = thesis_val if isinstance(thesis_val, dict) else {}
        track = tracking.get(stock_key) or {}
        industry = ind_lookup.get(stock_key) or "unknown"
        content = render_stock_note(stock_key, thesis, track, industry)
        write_note(STOCK_DIR / f"{stock_key}.md", content)
        stocks_synced += 1

    industries_synced = 0
    for ind_name, ind_val in sorted(industries.items()):
        ind = ind_val if isinstance(ind_val, dict) else {}
        content = render_industry_note(ind_name, ind)
        write_note(INDUSTRY_DIR / f"{safe_filename(ind_name)}.md", content)
        industries_synced += 1

    sync_portfolio(list(theses.keys()))

    return stocks_synced, industries_synced


def main() -> int:
    stocks, inds = sync()
    if stocks == 0 and inds == 0:
        return 1
    print(f"同步完成：stocks={stocks}, industries={inds}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
