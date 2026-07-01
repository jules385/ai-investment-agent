from __future__ import annotations

import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from news_utils import bing_news, evidence_item, page_detail

mcp = FastMCP(
    "industry-data",
    instructions="行业新闻与产业链事件MCP — 行业政策、价格、库存、订单、供需和产业链事件。"
)


@mcp.tool()
def get_industry_news(industry: str, start_time: str = "", end_time: str = "", limit: int = 10) -> dict:
    """搜索指定行业新闻和产业链事件。"""
    query = f"{industry} 行业 政策 订单 供需 价格 库存"
    results = bing_news(query, count=limit)
    items = []
    for result in results:
        if result.get("error"):
            items.append(result)
            continue
        items.append(evidence_item(
            section="industry",
            source_type="mcp",
            source_name=result.get("source_name", "Bing News"),
            source_tier="B",
            published_at=result.get("published_at", ""),
            title=result.get("title", ""),
            summary=result.get("summary", ""),
            url=result.get("url", ""),
            related_industries=[industry],
        ))
    return {"query": query, "start_time": start_time, "end_time": end_time, "items": items}


@mcp.tool()
def get_industry_chain_events(industry: str, start_time: str = "", end_time: str = "", limit: int = 10) -> dict:
    """搜索行业产业链事件。"""
    query = f"{industry} 产业链 供应链 扩产 订单 价格"
    results = bing_news(query, count=limit)
    items = [evidence_item(
        section="industry",
        source_type="mcp",
        source_name=result.get("source_name", "Bing News"),
        source_tier="B",
        published_at=result.get("published_at", ""),
        title=result.get("title", ""),
        summary=result.get("summary", ""),
        url=result.get("url", ""),
        related_industries=[industry],
    ) if not result.get("error") else result for result in results]
    return {"query": query, "start_time": start_time, "end_time": end_time, "items": items}


@mcp.tool()
def get_industry_detail(url: str) -> dict:
    """读取行业新闻网页详情。"""
    return page_detail(url)


if __name__ == "__main__":
    mcp.run()
