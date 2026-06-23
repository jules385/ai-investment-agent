import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, Response, jsonify, request, stream_with_context
from flask_cors import CORS


BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from web.api.parser import parse_all_reports


WORKSPACE_DATA = BASE_DIR / "reports" / "workspace-data.json"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEEPSEEK_MODEL = "deepseek-v4-pro"

app = Flask(__name__)
CORS(app)


def empty_workspace() -> dict:
    return {
        "industries": {},
        "theses": {},
        "tracking": {},
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


@app.post("/api/parse-all")
def parse_all():
    return jsonify(parse_all_reports(BASE_DIR / "reports" / "stocks"))


@app.get("/api/workspace")
def workspace():
    return jsonify(empty_workspace())


@app.post("/api/research-note")
def research_note():
    payload = request.get_json(silent=True) or {}
    return jsonify(
        {
            "status": "received",
            "note": payload.get("note", ""),
            "workspace": empty_workspace(),
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=False)
