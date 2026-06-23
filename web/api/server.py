from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

from parser import parse_all_reports


BASE_DIR = Path(__file__).resolve().parents[2]
WORKSPACE_DATA = BASE_DIR / "web" / "workspace-data.json"

app = Flask(__name__)
CORS(app)


def empty_workspace() -> dict:
    return {
        "industries": {},
        "theses": {},
        "tracking": {},
    }


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "")
    history = payload.get("history", [])

    return jsonify(
        {
            "response": f"已收到：{message or '空消息'}。这是检查点 1 的 mock 响应。",
            "history_length": len(history),
        }
    )


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
