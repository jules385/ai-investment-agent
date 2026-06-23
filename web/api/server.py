import json
import os
import re
from datetime import datetime
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, Response, jsonify, request, stream_with_context
from flask_cors import CORS


BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from web.api.parser import ai_extract


WORKSPACE_DATA = BASE_DIR / "reports" / "workspace-data.json"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEEPSEEK_MODEL = "deepseek-v4-pro"

app = Flask(__name__)
CORS(app)


def empty_workspace() -> dict:
    return {
        "stocks_parsed": 0,
        "industries": {},
        "theses": {},
        "tracking": {},
        "stocks": {},
    }


def load_system_prompt() -> str:
    prompt_parts = [
        "You are an A-share AI investment research assistant.",
        "Use the analyst skill definitions below as role and workflow context.",
    ]
    skills_dir = BASE_DIR / "skills" / "analysts"
    for skill_file in sorted(skills_dir.rglob("SKILL.md")):
        try:
            prompt_parts.append(f"\n# {skill_file.parent.name}\n{skill_file.read_text(encoding='utf-8')}")
        except UnicodeDecodeError:
            prompt_parts.append(f"\n# {skill_file.parent.name}\n{skill_file.read_text(encoding='utf-8-sig')}")
    return "\n\n".join(prompt_parts)


SYSTEM_PROMPT = load_system_prompt()


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def normalize_history(history: list, message: str) -> list:
    messages = []
    for item in history or []:
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": str(content)})

    if not messages or messages[-1].get("role") != "user" or messages[-1].get("content") != message:
        messages.append({"role": "user", "content": message})
    return messages


def stream_anthropic(message: str, history: list, model: str):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        yield sse("error", {"message": "ANTHROPIC_API_KEY is not configured. Set it and restart the Flask server."})
        return

    body = {
        "model": model or DEFAULT_MODEL,
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "messages": normalize_history(history, message),
        "stream": True,
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

    yield from proxy_sse_response(request_obj, "anthropic")


def stream_deepseek(message: str, history: list):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        yield sse("error", {"message": "DEEPSEEK_API_KEY is not configured. Set it and restart the Flask server."})
        return

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(normalize_history(history, message))
    body = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": True,
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

    yield from proxy_sse_response(request_obj, "deepseek")


def proxy_sse_response(request_obj: Request, provider: str):
    try:
        with urlopen(request_obj, timeout=120) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if not line.startswith("data:"):
                    continue

                data = line.removeprefix("data:").strip()
                if data == "[DONE]":
                    yield sse("done", {})
                    return

                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    continue

                if provider == "anthropic":
                    yield from parse_anthropic_event(payload)
                else:
                    yield from parse_deepseek_event(payload)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="ignore")
        yield sse("error", {"message": f"Chat provider returned HTTP {error.code}.", "detail": detail})
    except URLError as error:
        yield sse("error", {"message": f"Unable to reach chat provider: {error.reason}"})
    except TimeoutError:
        yield sse("error", {"message": "Chat provider request timed out."})


def parse_anthropic_event(payload: dict):
    event_type = payload.get("type")
    if event_type == "content_block_delta":
        text = payload.get("delta", {}).get("text")
        if text:
            yield sse("token", {"text": text})
    elif event_type == "content_block_start":
        block = payload.get("content_block", {})
        if block.get("type") == "tool_use":
            yield sse(
                "tool_call",
                {
                    "name": block.get("name", "tool"),
                    "status": "running",
                    "detail": block.get("input", {}),
                },
            )
    elif event_type == "message_stop":
        yield sse("done", {})


def parse_deepseek_event(payload: dict):
    choices = payload.get("choices") or []
    if not choices:
        return
    delta = choices[0].get("delta", {})
    text = delta.get("content")
    if text:
        yield sse("token", {"text": text})
    tool_calls = delta.get("tool_calls") or []
    for tool_call in tool_calls:
        function = tool_call.get("function", {})
        yield sse(
            "tool_call",
            {
                "name": function.get("name", "tool"),
                "status": "running",
                "detail": function.get("arguments", ""),
            },
        )
    if choices[0].get("finish_reason"):
        yield sse("done", {})


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    history = payload.get("history", [])
    model = payload.get("model") or DEFAULT_MODEL

    def generate():
        if not message:
            yield sse("error", {"message": "Message cannot be empty."})
            return
        if model == DEEPSEEK_MODEL:
            yield from stream_deepseek(message, history)
        else:
            yield from stream_anthropic(message, history, model)

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.get("/api/models")
def models():
    return jsonify([DEFAULT_MODEL, DEEPSEEK_MODEL])


def read_report_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def stock_identity(stock_dir: Path) -> tuple[str, str, str]:
    match = re.match(r"(?P<code>\d{6})-(?P<name>.+)", stock_dir.name)
    if not match:
        return stock_dir.name, stock_dir.name, stock_dir.name
    return stock_dir.name, match.group("code"), match.group("name")


def latest_file(files: list[Path]) -> Path | None:
    if not files:
        return None
    return sorted(files, key=lambda path: (path.stat().st_mtime, path.name))[-1]


def initial_report_text(stock_dir: Path) -> tuple[str, list[str]]:
    initial_dirs = [path for path in stock_dir.iterdir() if path.is_dir() and path.name.startswith("01-")]
    if not initial_dirs:
        return "", []

    report_files = sorted(initial_dirs[0].glob("*.md"))
    chief = latest_file([path for path in report_files if not path.name.startswith("子报告")])
    fundamental = latest_file([path for path in report_files if "基本面" in path.name])
    selected = [path for path in (chief, fundamental) if path]
    if not selected:
        selected = [latest_file(report_files)] if latest_file(report_files) else []

    return "\n\n".join(read_report_text(path) for path in selected), [str(path) for path in selected]


def tracking_report_text(stock_dir: Path) -> tuple[str, list[str]]:
    selected = []
    for folder in sorted(path for path in stock_dir.iterdir() if path.is_dir()):
        if not folder.name.startswith(("02-", "03-", "04-")):
            continue
        selected.extend(sorted(folder.glob("*.md")))
    return "\n\n".join(read_report_text(path) for path in selected), [str(path) for path in selected]


def extraction_payload(result: dict) -> dict:
    return result.get("extracted") if isinstance(result, dict) and isinstance(result.get("extracted"), dict) else {}


def parse_all_reports_with_ai(reports_dir: Path) -> dict:
    workspace = empty_workspace()
    workspace["generated_at"] = datetime.now().isoformat(timespec="seconds")
    workspace["ai_extraction"] = True
    workspace["errors"] = []

    if not reports_dir.exists():
        workspace["errors"].append(f"Reports directory does not exist: {reports_dir}")
        return workspace

    for stock_dir in sorted(path for path in reports_dir.iterdir() if path.is_dir()):
        markdown_files = sorted(stock_dir.rglob("*.md"))
        if not markdown_files:
            continue

        stock_key, code, name = stock_identity(stock_dir)
        initial_text, initial_sources = initial_report_text(stock_dir)
        tracking_text, tracking_sources = tracking_report_text(stock_dir)

        industry_result = ai_extract(initial_text, "industry_knowledge") if initial_text else {
            "error": "No initial coverage report found.",
            "extracted": {},
        }
        thesis_result = ai_extract(initial_text, "investment_thesis") if initial_text else {
            "error": "No initial coverage report found.",
            "extracted": {},
        }
        tracking_result = ai_extract(tracking_text, "tracking_data") if tracking_text else {
            "error": "No tracking report found.",
            "extracted": {"indicators": [], "events": [], "decisions": []},
        }

        industry_data = extraction_payload(industry_result)
        thesis_data = extraction_payload(thesis_result)
        tracking_data = extraction_payload(tracking_result)
        industry_name = industry_data.get("industry") or "AI extraction unavailable"

        stock_record = {
            "code": code,
            "name": name,
            "stock": stock_key,
            "industry": industry_name,
            "industry_knowledge": industry_data,
            "investment_thesis": thesis_data,
            "tracking_data": tracking_data,
            "errors": {
                "industry_knowledge": industry_result.get("error"),
                "investment_thesis": thesis_result.get("error"),
                "tracking_data": tracking_result.get("error"),
            },
            "source_files": initial_sources + tracking_sources,
        }
        workspace["stocks"][stock_key] = stock_record
        workspace["theses"][stock_key] = thesis_data
        workspace["tracking"][stock_key] = tracking_data

        grouped_industry = workspace["industries"].setdefault(
            industry_name,
            {
                "name": industry_name,
                "stocks": [],
                "chain": industry_data.get("chain", []),
                "tam_cagr": industry_data.get("tam_cagr", {}),
                "financial_benchmarks": industry_data.get("financial_benchmarks", {}),
            },
        )
        grouped_industry["stocks"].append({"stock": stock_key, "code": code, "name": name})
        if not grouped_industry.get("chain") and industry_data.get("chain"):
            grouped_industry["chain"] = industry_data.get("chain", [])

        for extraction_name, extraction_result in (
            ("industry_knowledge", industry_result),
            ("investment_thesis", thesis_result),
            ("tracking_data", tracking_result),
        ):
            if extraction_result.get("error"):
                workspace["errors"].append(
                    {
                        "stock": stock_key,
                        "extraction_type": extraction_name,
                        "error": extraction_result.get("error"),
                    }
                )

    workspace["stocks_parsed"] = len(workspace["stocks"])
    return workspace


@app.post("/api/parse-all")
def parse_all():
    data = parse_all_reports_with_ai(BASE_DIR / "reports" / "stocks")
    WORKSPACE_DATA.parent.mkdir(parents=True, exist_ok=True)
    WORKSPACE_DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return jsonify(
        {
            "status": "ok",
            "stocks_parsed": data.get("stocks_parsed", 0),
            "output": str(WORKSPACE_DATA),
            "industries": len(data.get("industries", {})),
            "theses": len(data.get("theses", {})),
            "tracking": len(data.get("tracking", {})),
        }
    )


@app.get("/api/workspace")
def workspace():
    if not WORKSPACE_DATA.exists():
        return jsonify(empty_workspace())
    try:
        return jsonify(json.loads(WORKSPACE_DATA.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return jsonify(empty_workspace())


@app.post("/api/research-note")
def research_note():
    payload = request.get_json(silent=True) or {}
    symbol = str(payload.get("symbol", "")).strip()
    note = str(payload.get("note", "")).strip()

    if not symbol or not note:
        return jsonify({"status": "error", "message": "symbol and note are required"}), 400

    if WORKSPACE_DATA.exists():
        try:
            workspace_data = json.loads(WORKSPACE_DATA.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            workspace_data = empty_workspace()
    else:
        workspace_data = empty_workspace()

    extraction = ai_extract(note, "tracking_data")
    extracted = extraction.get("extracted") if isinstance(extraction.get("extracted"), dict) else {}
    tracking = workspace_data.setdefault("tracking", {}).setdefault(
        symbol,
        {"indicators": [], "events": [], "decisions": []},
    )
    tracking.setdefault("indicators", []).extend(extracted.get("indicators", []))
    tracking.setdefault("events", []).extend(extracted.get("events", []))
    tracking.setdefault("decisions", []).extend(extracted.get("decisions", []))

    if extraction.get("error"):
        tracking.setdefault("events", []).append(
            {
                "date": datetime.now().date().isoformat(),
                "description": f"Research note saved, AI extraction failed: {extraction.get('error')}",
                "severity": "minor",
                "source_report": "research-note",
            }
        )

    workspace_data.setdefault("stocks", {}).setdefault(symbol, {"stock": symbol, "name": symbol})
    WORKSPACE_DATA.parent.mkdir(parents=True, exist_ok=True)
    WORKSPACE_DATA.write_text(json.dumps(workspace_data, ensure_ascii=False, indent=2), encoding="utf-8")

    return jsonify(
        {
            "status": "ok",
            "symbol": symbol,
            "error": extraction.get("error"),
            "tracking": tracking,
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=False)
