from __future__ import annotations

import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from news_utils import bing_news, evidence_item, page_detail

mcp = FastMCP(
    "market-news",
    instructions="市场新闻MCP — 权威财经媒体新闻发现、热点搜索与详情读取。"
)

TRUSTED_MEDIA = {
    "cls.cn": "财联社",
    "stcn.com": "证券时报",
    "cnstock.com": "上海证券报",
    "cs.com.cn": "中国证券报",
    "yicai.com": "第一财经",
    "news.cn": "新华社",
    "cctv.com": "央视网",
}


def _tier(url: str) -> str:
    return "B" if any(domain in url for domain in TRUSTED_MEDIA) else "C"


@mcp.tool()
def search_news(start_time: str = "", end_time: str = "", keywords: list[str] | None = None, limit: int = 10) -> dict:
    """搜索市场新闻，输出日报 evidence 兼容结构。"""
    query = " ".join(keywords or ["A股", "财经", "重要新闻"])
    results = bing_news(query, count=limit)
    items = []
    for result in results:
        if result.get("error"):
            items.append(result)
            continue
        url = result.get("url", "")
        source = result.get("source_name", "")
        for domain, name in TRUSTED_MEDIA.items():
            if domain in url:
                source = name
                break
        items.append(evidence_item(
            section="industry",
            source_type="mcp",
            source_name=source or "Bing News",
            source_tier=_tier(url),
            published_at=result.get("published_at", ""),
            title=result.get("title", ""),
            summary=result.get("summary", ""),
            url=url,
        ))
    return {"query": query, "start_time": start_time, "end_time": end_time, "items": items}


@mcp.tool()
def get_hot_news(start_time: str = "", end_time: str = "", limit: int = 10) -> dict:
    """搜索A股热点新闻。"""
    return search_news(start_time=start_time, end_time=end_time, keywords=["A股", "盘前", "重要新闻"], limit=limit)


@mcp.tool()
def get_news_detail(url: str) -> dict:
    """读取新闻网页详情。"""
    return page_detail(url)


if __name__ == "__main__":
    mcp.run()
