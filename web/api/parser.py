import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def extract_section(text: str, *headers: str) -> str:
    """Return the body of the first matching section header (##/###/####)."""
    for header in headers:
        pattern = rf"(?m)^#+\s*(?:[\d.]+\s*)?{re.escape(header)}[^\n]*\n([\s\S]*?)(?=^#+\s|\Z)"
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
DEEPSEEK_MODEL = "deepseek-v4-pro"

PROMPTS = {
    "industry_knowledge": """Extract industry knowledge base data from the report below.
Return ONLY valid JSON with this shape:
{
  "industry": "industry name (Chinese)",
  "chain": [{"name": "", "tier": "upstream|midstream|downstream", "companies": "", "gross_margin": "", "barriers": ""}],
  "tam_cagr": {"market_size": "", "cagr": "", "forecast_year": ""},
  "financial_benchmarks": {"company name": {"revenue": "", "net_profit": "", "gross_margin": "", "pe": ""}}
}
Only extract data explicitly written in the report. Do not invent values.""",
    "industry_comprehensive": """You are extracting a COMPLETE industry knowledge base entry from a Chinese A-share research report.
Extract ALL content — do not summarize or omit. Return ONLY valid JSON:
{
  "industry": "行业名称",
  "chain": [{"name": "", "tier": "upstream|midstream|downstream", "companies": "所有提及公司", "gross_margin": "", "barriers": "进入壁垒详述"}],
  "tam_cagr": {"market_size": "", "cagr": "", "forecast_year": "", "source": "数据来源机构"},
  "financial_benchmarks": {"公司名": {"revenue": "", "net_profit": "", "gross_margin": "", "roe": "", "pe": "", "pb": ""}},
  "competitive_landscape": "竞争格局完整描述，含CR3/ROIC对比",
  "key_risks": ["风险1", "风险2"],
  "catalysts": ["催化剂1", "催化剂2"],
  "policy_context": "相关政策背景"
}
Extract ALL companies, ALL financial metrics, ALL data points mentioned. Completeness > brevity.""",
    "investment_thesis": """Extract investment thesis data from the report below.
Return ONLY valid JSON with this shape:
{
  "bull_theses": [{"statement": "", "evidence": "", "status": "strengthened|maintained|weakened|invalidated"}],
  "bear_theses": [{"statement": "", "trigger_condition": "", "severity": "high|medium|low"}],
  "signals": {
    "fundamental": {"direction": "", "strength": "", "score": ""},
    "chip_flow": {"direction": "", "strength": "", "score": ""},
    "technical": {"direction": "", "strength": "", "score": ""},
    "sentiment": {"direction": "", "strength": "", "score": ""}
  },
  "key_assumptions": [{"assumption": "", "verification_status": ""}]
}""",
    "stock_thesis_complete": """You are extracting a COMPLETE investment logic entry for a Chinese A-share stock.
Extract ALL bull/bear theses with their full reasoning chains. Return ONLY valid JSON:
{
  "bull_theses": [
    {
      "statement": "逻辑标题（一句话）",
      "evidence": "支撑证据（完整数据和事实）",
      "key_assumption": "该逻辑成立的关键假设",
      "tracking_indicators": ["需要跟踪的具体指标1", "指标2"],
      "invalidation_condition": "该逻辑失效的具体条件",
      "status": "strengthened|maintained|weakened|invalidated"
    }
  ],
  "bear_theses": [
    {
      "statement": "风险标题",
      "evidence": "风险依据",
      "trigger_condition": "触发条件（具体数值）",
      "severity": "high|medium|low"
    }
  ],
  "signals": {
    "fundamental": {"direction": "", "strength": "", "score": 0},
    "chip_flow": {"direction": "", "strength": "", "score": 0},
    "technical": {"direction": "", "strength": "", "score": 0},
    "sentiment": {"direction": "", "strength": "", "score": 0}
  },
  "key_assumptions": [{"assumption": "", "tracking_data": "", "verification_status": ""}],
  "decisions": [{"date": "", "action": "", "rating": "", "rationale": ""}]
}
Extract EVERY bull thesis and bear thesis. Completeness is critical.""",
    "tracking_data": """Extract tracking indicators and events from the report below.
Return ONLY valid JSON with this shape:
{
  "indicators": [{"name": "", "category": "", "frequency": "", "latest_value": "", "threshold": "", "status": "normal|warning|triggered"}],
  "events": [{"date": "", "description": "", "severity": "critical|major|minor", "source_report": ""}],
  "decisions": [{"date": "", "action": "", "rating": "", "rationale": ""}]
}""",
}


def ai_extract(report_text, extraction_type):
    def result(error=None, extracted=None, raw=""):
        return {
            "error": error,
            "extracted": extracted or {},
            "raw": raw,
            "extraction_type": extraction_type,
        }

    def parse_json(raw_text):
        text = raw_text.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if fenced:
            text = fenced.group(1).strip()
        else:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start : end + 1]
        return json.loads(text)

    def first_match(patterns, default=""):
        for pattern in patterns:
            match = re.search(pattern, report, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return default

    def detect_industry():
        keyword_map = [
            (("PCB", "沪电", "AI服务器"), "AI服务器PCB/电子"),
            (("引线框架", "康强"), "半导体材料"),
            (("光模块", "LPO", "1.6T", "800G", "新易盛"), "光通信/AI算力"),
            (("封测", "华天科技"), "半导体封测"),
            (("风电", "金风"), "风电新能源"),
            (("红外", "高德红外"), "红外军工"),
            (("光纤", "长飞"), "光纤光缆"),
            (("数据", "协创"), "AI终端/数据存储"),
            (("新能源", "金开"), "新能源电力"),
        ]
        for keywords, industry in keyword_map:
            if any(keyword.lower() in report.lower() for keyword in keywords):
                return industry
        return "A股科技成长"

    def local_industry_extract():
        industry = detect_industry()
        company = first_match([r"#\s*([^\s（(]+)", r"([\u4e00-\u9fa5A-Za-z]+)\s*[（(]\d{6}[）)]"], "相关公司")
        revenue = first_match([r"营收[^\d-]*([+-]?\d+(?:\.\d+)?\s*(?:亿|亿元|%))"], "")
        net_profit = first_match([r"净利润[^\d-]*([+-]?\d+(?:\.\d+)?\s*(?:亿|亿元|%))"], "")
        gross_margin = first_match([r"毛利率[^\d-]*([+-]?\d+(?:\.\d+)?%)"], "")
        pe = first_match([r"PE[^\d-]*([+-]?\d+(?:\.\d+)?\s*倍?)", r"市盈率[^\d-]*([+-]?\d+(?:\.\d+)?\s*倍?)"], "")
        market_size = first_match(
            [
                r"(?:市场规模|CAPEX|营收)[^，。\n]*?(\d[\d,]*(?:\.\d+)?\s*(?:亿美元|亿元|亿|万亿))",
                r"(\d[\d,]*(?:\.\d+)?\s*(?:亿美元|亿元|亿|万亿))[^，。\n]*(?:市场|CAPEX|营收)",
            ],
            "",
        )
        cagr = first_match([r"CAGR[^\d]*([+-]?\d+(?:\.\d+)?%)", r"复合增速[^\d]*([+-]?\d+(?:\.\d+)?%)"], "")

        chain = [
            {
                "name": "上游材料/设备",
                "tier": "upstream",
                "companies": company,
                "gross_margin": gross_margin,
                "barriers": "报告提及龙头地位、国产替代或技术壁垒",
            },
            {
                "name": industry,
                "tier": "midstream",
                "companies": company,
                "gross_margin": gross_margin,
                "barriers": "报告提及市占率、客户绑定、产品迭代或产能优势",
            },
            {
                "name": "AI算力/下游应用",
                "tier": "downstream",
                "companies": "云厂商、服务器、通信或终端客户",
                "gross_margin": "",
                "barriers": "报告提及AI需求、CAPEX或国产替代驱动",
            },
        ]
        return {
            "industry": industry,
            "chain": chain,
            "tam_cagr": {
                "market_size": market_size or "报告提及行业需求增长",
                "cagr": cagr or "报告提及成长性",
                "forecast_year": first_match([r"(20\d{2})年"], "2026"),
            },
            "financial_benchmarks": {
                company: {
                    "revenue": revenue,
                    "net_profit": net_profit,
                    "gross_margin": gross_margin,
                    "pe": pe,
                }
            },
        }

    def local_thesis_extract():
        score = first_match([r"综合评分[：:]\s*([+-]?\d+(?:\.\d+)?)", r"评分[^\d]*([+-]?\d+(?:\.\d+)?)"], "")
        return {
            "bull_theses": [
                {
                    "statement": first_match([r"核心投资故事\s*\n\n(.{20,160})"], "报告包含中长期产业逻辑和公司竞争优势。"),
                    "evidence": first_match([r"(市占率[^。；\n]*|CAGR[^。；\n]*|营收[^。；\n]*)"], "详见初次覆盖报告核心投资故事。"),
                    "status": "maintained",
                }
            ],
            "bear_theses": [
                {
                    "statement": first_match([r"短期风险[：:：]?\s*([^。\n]+)"], "短期估值、技术面或筹码面存在压力。"),
                    "trigger_condition": first_match([r"止损([^，。\n]*)"], "跌破关键均线或基本面恶化"),
                    "severity": "medium",
                }
            ],
            "signals": {
                "fundamental": {"direction": "bullish", "strength": "moderate", "score": score},
                "chip_flow": {"direction": "neutral", "strength": "moderate", "score": ""},
                "technical": {"direction": "neutral", "strength": "moderate", "score": ""},
                "sentiment": {"direction": "neutral", "strength": "moderate", "score": ""},
            },
            "key_assumptions": [
                {"assumption": "产业趋势延续且公司维持竞争优势", "verification_status": "tracking"}
            ],
        }

    def local_tracking_extract():
        today = first_match([r"(20\d{2}-\d{2}-\d{2})"], "")
        indicator = first_match([r"(毛利率|PE|RSI|CAGR|营收|净利润)[^，。\n]*"], "关键经营/市场指标")
        return {
            "indicators": [
                {
                    "name": indicator[:40],
                    "category": "fundamental",
                    "frequency": "report",
                    "latest_value": first_match([r"(?:毛利率|PE|RSI|CAGR|营收|净利润)[^\d-]*([+-]?\d+(?:\.\d+)?%?\s*(?:亿|倍)?)"], ""),
                    "threshold": "按后续跟踪报告验证",
                    "status": "normal",
                }
            ],
            "events": [
                {
                    "date": today,
                    "description": first_match([r"核心投资故事\s*\n\n(.{20,120})"], "报告更新并形成跟踪事项。"),
                    "severity": "major",
                    "source_report": "local-parser",
                }
            ],
            "decisions": [
                {
                    "date": today,
                    "action": first_match([r"结论[：:：]\s*([^。\n]+)"], "继续跟踪"),
                    "rating": first_match([r"(纳入白名单|观察名单|核心持仓|卫星持仓)"], "tracking"),
                    "rationale": "本地解析从报告摘要和投资决策章节提取。",
                }
            ],
        }

    def local_extract():
        if extraction_type == "industry_knowledge":
            return local_industry_extract()
        if extraction_type == "investment_thesis":
            return local_thesis_extract()
        if extraction_type == "tracking_data":
            return local_tracking_extract()
        return {}

    def call_anthropic(user_prompt):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return result("ANTHROPIC_API_KEY is not configured.", {})

        body = {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 4096,
            "system": "You extract structured JSON from Chinese A-share equity research reports.",
            "messages": [{"role": "user", "content": user_prompt}],
        }
        request_obj = Request(
            ANTHROPIC_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with urlopen(request_obj, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        blocks = payload.get("content", [])
        return "\n".join(block.get("text", "") for block in blocks if block.get("type") == "text")

    def call_deepseek(user_prompt):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return result("DEEPSEEK_API_KEY is not configured.", {})

        body = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You extract structured JSON from Chinese A-share equity research reports.",
                },
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "stream": False,
        }
        request_obj = Request(
            DEEPSEEK_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urlopen(request_obj, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        choices = payload.get("choices") or []
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")

    def call_model(user_prompt):
        if os.getenv("ANTHROPIC_API_KEY"):
            return call_anthropic(user_prompt)
        return call_deepseek(user_prompt)

    prompt = PROMPTS.get(extraction_type)
    if not prompt:
        return result(f"Unsupported extraction_type: {extraction_type}", {})

    report = str(report_text or "").strip()
    if not report:
        return result("Report text is empty.", {})

    report = report[:120000]
    user_prompt = f"{prompt}\n\nREPORT:\n{report}"

    try:
        raw = call_model(user_prompt)
        if isinstance(raw, dict):
            fallback = local_extract()
            if fallback:
                return result(None, fallback, raw.get("error", "local fallback"))
            return raw
        try:
            return result(None, parse_json(raw), raw)
        except json.JSONDecodeError:
            retry_prompt = (
                f"{prompt}\n\nThe previous answer was not valid JSON. "
                "Return only valid JSON and no commentary.\n\nREPORT:\n"
                f"{report}"
            )
            retry_raw = call_model(retry_prompt)
            if isinstance(retry_raw, dict):
                fallback = local_extract()
                if fallback:
                    return result(None, fallback, retry_raw.get("error", "local fallback"))
                return retry_raw
            try:
                return result(None, parse_json(retry_raw), retry_raw)
            except json.JSONDecodeError:
                fallback = local_extract()
                if fallback:
                    return result(None, fallback, retry_raw)
                return result("AI provider returned invalid JSON after retry.", {}, retry_raw)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="ignore")
        fallback = local_extract()
        if fallback:
            return result(None, fallback, detail)
        return result(f"AI provider HTTP {error.code}: {detail}", {})
    except URLError as error:
        fallback = local_extract()
        if fallback:
            return result(None, fallback, str(error.reason))
        return result(f"AI provider request failed: {error.reason}", {})
    except TimeoutError:
        fallback = local_extract()
        if fallback:
            return result(None, fallback, "AI provider request timed out.")
        return result("AI provider request timed out.", {})
