import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-20250514"

PROMPTS = {
    "industry_knowledge": """Extract industry knowledge base data from the report below.
Return ONLY valid JSON with this shape:
{
  "industry": "industry name",
  "chain": [{"name": "", "tier": "upstream|midstream|downstream", "companies": "", "gross_margin": "", "barriers": ""}],
  "tam_cagr": {"market_size": "", "cagr": "", "forecast_year": ""},
  "financial_benchmarks": {"company name": {"revenue": "", "net_profit": "", "gross_margin": "", "pe": ""}}
}
Only extract data explicitly written in the report. Do not invent values.""",
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

    def call_anthropic(user_prompt):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return result("ANTHROPIC_API_KEY is not configured.", {})

        body = {
            "model": DEFAULT_MODEL,
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

    prompt = PROMPTS.get(extraction_type)
    if not prompt:
        return result(f"Unsupported extraction_type: {extraction_type}", {})

    report = str(report_text or "").strip()
    if not report:
        return result("Report text is empty.", {})

    report = report[:120000]
    user_prompt = f"{prompt}\n\nREPORT:\n{report}"

    try:
        raw = call_anthropic(user_prompt)
        if isinstance(raw, dict):
            return raw
        try:
            return result(None, parse_json(raw), raw)
        except json.JSONDecodeError:
            retry_prompt = (
                f"{prompt}\n\nThe previous answer was not valid JSON. "
                "Return only valid JSON and no commentary.\n\nREPORT:\n"
                f"{report}"
            )
            retry_raw = call_anthropic(retry_prompt)
            if isinstance(retry_raw, dict):
                return retry_raw
            try:
                return result(None, parse_json(retry_raw), retry_raw)
            except json.JSONDecodeError:
                return result("Claude returned invalid JSON after retry.", {}, retry_raw)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="ignore")
        return result(f"Anthropic API HTTP {error.code}: {detail}", {})
    except URLError as error:
        return result(f"Anthropic API request failed: {error.reason}", {})
    except TimeoutError:
        return result("Anthropic API request timed out.", {})
