from __future__ import annotations

import re
from pathlib import Path

STOCK_DIMENSIONS = {
    "fundamental": "基本面.md",
    "technical": "技术面.md",
    "chip": "筹码面.md",
    "sentiment": "情绪面.md",
    "decision": "投资决策.md",
    "index": "_index.md",
}


def split_stock_key(stock_key: str) -> tuple[str, str]:
    match = re.match(r"^(\d{6})[-_ ]?(.*)", stock_key)
    if match:
        return match.group(1), match.group(2).strip()
    return stock_key, stock_key


def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name).strip() or "unknown"


def stock_dir(stock_key: str) -> str:
    return f"个股逻辑/{stock_key}"


def tracking_file(stock_key: str) -> str:
    return f"跟踪面板/{stock_key}.md"


def industry_file(industry: str) -> str:
    return f"行业知识库/{safe_filename(industry)}.md"


def infer_dimension(source_file: str, heading: str) -> str:
    text = f"{source_file} {heading}"
    if any(word in text for word in ("基本面", "财务", "估值", "三端", "增长逻辑", "利润", "现金流", "资产负债")):
        return "fundamental"
    if any(word in text for word in ("技术", "趋势", "MACD", "RSI", "KDJ", "价格锚点", "买卖信号")):
        return "technical"
    if any(word in text for word in ("筹码", "资金", "股东", "北向", "融资", "龙虎榜")):
        return "chip"
    if any(word in text for word in ("情绪", "舆情", "散户", "温度")):
        return "sentiment"
    if any(word in text for word in ("投资决策", "核心投资故事", "信号汇总", "矛盾分析", "评级建议", "核心结论")):
        return "decision"
    return "decision"


def default_target_file(stock_key: str, industry: str, destination: str, source_file: str, heading: str) -> str:
    if destination == "industry":
        return industry_file(industry)
    dimension = infer_dimension(source_file, heading)
    return f"{stock_dir(stock_key)}/{STOCK_DIMENSIONS[dimension]}"


def default_target_section(heading: str, knowledge_type: str) -> str:
    if knowledge_type:
        return knowledge_type
    return heading
