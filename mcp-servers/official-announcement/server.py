from __future__ import annotations

import re
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from news_utils import bing_web, evidence_item, page_detail

mcp = FastMCP(
    "official-announcement",
    instructions="A股公告与监管新闻MCP — 巨潮资讯、交易所、证监会等官方来源发现与详情读取。"
)

OFFICIAL_SITES = {
    "cninfo": "cninfo.com.cn",
    "sse": "sse.com.cn",
    "szse": "szse.cn",
    "csrc": "csrc.gov.cn",
    "bse": "bse.cn",
}


def _stock_query(symbol: str, keyword: str = "") -> str:
    terms = [symbol, keyword, "公告"]
    return " ".join(term for term in terms if term).strip()


@mcp.tool()
def search_company_announcements(symbol: str, start_time: str = "", end_time: str = "", keyword: str = "", limit: int = 10) -> dict:
    """搜索公司公告官方来源。返回日报 evidence 兼容结构。"""
    query = _stock_query(symbol, keyword) + " site:cninfo.com.cn OR site:sse.com.cn OR site:szse.cn"
    results = bing_web(query, count=limit)
    items = []
    for result in results:
        if result.get("error"):
            items.append(result)
            continue
        host = ""
        for name, domain in OFFICIAL_SITES.items():
            if domain in result.get("url", ""):
                host = name
                break
        items.append(evidence_item(
            section="stock",
            source_type="mcp",
            source_name=host or result.get("source_name", "official-search"),
            source_tier="A" if host else "B",
            title=result.get("title", ""),
            summary=result.get("summary", ""),
            url=result.get("url", ""),
            related_stocks=[symbol],
        ))
    return {"query": query, "start_time": start_time, "end_time": end_time, "items": items}


@mcp.tool()
def search_exchange_announcements(start_time: str = "", end_time: str = "", keyword: str = "", limit: int = 10) -> dict:
    """搜索交易所、证监会公告与监管新闻。"""
    query = f"{keyword or 'A股 监管 公告'} site:sse.com.cn OR site:szse.cn OR site:csrc.gov.cn OR site:bse.cn"
    results = bing_web(query, count=limit)
    items = [evidence_item(
        section="macro",
        source_type="mcp",
        source_name=result.get("source_name", "official-search"),
        source_tier="A" if any(domain in result.get("url", "") for domain in OFFICIAL_SITES.values()) else "B",
        title=result.get("title", ""),
        summary=result.get("summary", ""),
        url=result.get("url", ""),
    ) if not result.get("error") else result for result in results]
    return {"query": query, "start_time": start_time, "end_time": end_time, "items": items}


@mcp.tool()
def get_announcement_detail(url: str) -> dict:
    """读取公告或监管网页详情。"""
    return page_detail(url)


@mcp.tool()
def extract_announcement_entities(text: str) -> dict:
    """从公告文本中抽取股票代码、金额、日期等轻量实体。"""
    return {
        "stock_codes": sorted(set(re.findall(r"\b[0-9]{6}\b", text))),
        "amounts": re.findall(r"(?:人民币)?[0-9]+(?:\.[0-9]+)?\s*(?:亿元|万元|元)", text)[:20],
        "dates": re.findall(r"20[0-9]{2}[年/-][0-9]{1,2}[月/-][0-9]{1,2}日?", text)[:20],
    }


if __name__ == "__main__":
    mcp.run()
