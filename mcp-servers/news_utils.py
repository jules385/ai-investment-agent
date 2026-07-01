from __future__ import annotations

import html
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

USER_AGENT = "ai-investment-agent/0.3 daily-news-mcp"
_last_call = 0.0


def throttle(seconds: float = 1.0) -> None:
    global _last_call
    elapsed = time.time() - _last_call
    if elapsed < seconds:
        time.sleep(seconds - elapsed)
    _last_call = time.time()


def fetch_text(url: str, timeout: int = 12) -> str:
    throttle()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def clean_text(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def bing_news(query: str, count: int = 10) -> list[dict[str, Any]]:
    url = "https://www.bing.com/news/search?" + urllib.parse.urlencode({"q": query, "format": "rss"})
    try:
        xml_text = fetch_text(url)
        root = ET.fromstring(xml_text)
    except Exception as exc:
        return [{"error": f"bing news search failed: {str(exc)[:160]}", "query": query}]
    items: list[dict[str, Any]] = []
    for item in root.findall(".//item")[:count]:
        title = clean_text(item.findtext("title", ""))
        link = clean_text(item.findtext("link", ""))
        pub = clean_text(item.findtext("pubDate", ""))
        desc = clean_text(item.findtext("description", ""))
        source = clean_text(item.findtext("{https://www.bing.com/news/search?q=}source", ""))
        items.append({
            "title": title,
            "url": link,
            "published_at": pub,
            "summary": desc,
            "source_name": source or "Bing News",
        })
    return items


def bing_web(query: str, count: int = 10) -> list[dict[str, Any]]:
    url = "https://www.bing.com/search?" + urllib.parse.urlencode({"q": query})
    try:
        text = fetch_text(url)
    except Exception as exc:
        return [{"error": f"bing web search failed: {str(exc)[:160]}", "query": query}]
    pattern = re.compile(r'<li class="b_algo".*?<h2.*?<a href="([^"]+)".*?>(.*?)</a>.*?(?:<p>(.*?)</p>)?', re.S)
    items = []
    for href, title, desc in pattern.findall(text)[:count]:
        items.append({
            "title": clean_text(title),
            "url": html.unescape(href),
            "summary": clean_text(desc),
            "source_name": urllib.parse.urlparse(href).netloc,
        })
    return items


def normalize_datetime(value: str) -> str:
    if not value:
        return ""
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return value


def evidence_item(
    *,
    section: str,
    source_type: str,
    source_name: str,
    source_tier: str,
    title: str,
    published_at: str = "",
    summary: str = "",
    url: str = "",
    related_industries: list[str] | None = None,
    related_stocks: list[str] | None = None,
    verified_by: list[str] | None = None,
    impact_hint: str = "",
) -> dict[str, Any]:
    return {
        "section": section,
        "source_type": source_type,
        "source_name": source_name,
        "source_tier": source_tier,
        "published_at": normalize_datetime(published_at),
        "title": title,
        "summary": summary,
        "url": url,
        "raw_text_path": "",
        "related_industries": related_industries or [],
        "related_stocks": related_stocks or [],
        "verified_by": verified_by or [],
        "impact_hint": impact_hint,
        "ai_importance": "",
        "ai_reasoning": "",
        "follow_up": "",
    }


def page_detail(url: str) -> dict[str, Any]:
    try:
        text = fetch_text(url)
    except Exception as exc:
        return {"url": url, "error": str(exc)[:200]}
    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
    title = clean_text(title_match.group(1)) if title_match else ""
    body = clean_text(text)
    return {
        "url": url,
        "title": title,
        "text": body[:6000],
        "length": len(body),
    }
