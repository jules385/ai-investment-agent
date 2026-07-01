from __future__ import annotations

import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from news_utils import bing_web, evidence_item, page_detail

mcp = FastMCP(
    "macro-policy",
    instructions="宏观政策新闻MCP — 央行、统计局、财政部、发改委、工信部等官方政策新闻发现与详情读取。"
)

OFFICIAL_DOMAINS = {
    "pbc.gov.cn": "中国人民银行",
    "stats.gov.cn": "国家统计局",
    "mof.gov.cn": "财政部",
    "ndrc.gov.cn": "国家发改委",
    "miit.gov.cn": "工信部",
    "gov.cn": "中国政府网",
    "safe.gov.cn": "外汇局",
}


@mcp.tool()
def get_policy_news(start_time: str = "", end_time: str = "", keyword: str = "", limit: int = 10) -> dict:
    """搜索宏观政策官方新闻。"""
    base = keyword or "宏观 政策 A股 央行 财政 发改委"
    query = base + " site:pbc.gov.cn OR site:stats.gov.cn OR site:mof.gov.cn OR site:ndrc.gov.cn OR site:miit.gov.cn OR site:gov.cn"
    results = bing_web(query, count=limit)
    items = []
    for result in results:
        if result.get("error"):
            items.append(result)
            continue
        source = result.get("source_name", "")
        tier = "B"
        for domain, name in OFFICIAL_DOMAINS.items():
            if domain in result.get("url", ""):
                source = name
                tier = "A"
                break
        items.append(evidence_item(
            section="macro",
            source_type="mcp",
            source_name=source,
            source_tier=tier,
            title=result.get("title", ""),
            summary=result.get("summary", ""),
            url=result.get("url", ""),
        ))
    return {"query": query, "start_time": start_time, "end_time": end_time, "items": items}


@mcp.tool()
def get_macro_calendar(date: str) -> dict:
    """返回常见宏观数据发布时间检查清单。"""
    return {
        "date": date,
        "items": [
            {"event": "PMI", "source": "国家统计局", "frequency": "monthly"},
            {"event": "CPI/PPI", "source": "国家统计局", "frequency": "monthly"},
            {"event": "社融/M2", "source": "中国人民银行", "frequency": "monthly"},
            {"event": "LPR", "source": "全国银行间同业拆借中心", "frequency": "monthly"},
            {"event": "公开市场操作", "source": "中国人民银行", "frequency": "daily"},
        ],
    }


@mcp.tool()
def get_policy_detail(url: str) -> dict:
    """读取宏观政策网页详情。"""
    return page_detail(url)


if __name__ == "__main__":
    mcp.run()
