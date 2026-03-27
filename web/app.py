from __future__ import annotations
import json, mimetypes, threading, time, uuid, os
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
SITE_DIR = BASE_DIR / "site"
STATIC_DIR = BASE_DIR / "static"
RUNTIME_DIR = BASE_DIR / "runtime"
RUNTIME_DIR.mkdir(exist_ok=True)
AGENT_LOG_FILE = RUNTIME_DIR / "agent_logs.json"

executor = ThreadPoolExecutor(max_workers=20)
active_agents = {}
chats = {}
lock = threading.Lock()

DEFAULT_AGENTS = [
    {"id": "claude", "name": "Claude", "role": "Analyst"},
    {"id": "chatgpt", "name": "ChatGPT", "role": "Generalist"},
    {"id": "gemini", "name": "Gemini", "role": "Researcher"},
]

def _count_tokens(text: str) -> int:
    return max(1, len(text.split()))

def _read_logs():
    if not AGENT_LOG_FILE.exists():
        return []
    return json.loads(AGENT_LOG_FILE.read_text(encoding="utf-8"))

def _persist_log(entry):
    logs = _read_logs()
    logs.append(entry)
    AGENT_LOG_FILE.write_text(json.dumps(logs[-500:], ensure_ascii=False, indent=2), encoding="utf-8")

def _run_agent(agent_id: str, prompt: str):
    with lock:
        active_agents[agent_id]["status"] = "running"
    time.sleep(0.8)
    output = f"{agent_id} processed: {prompt[:80]}"
    _persist_log({
        "timestamp": time.time(),
        "agent_id": agent_id,
        "prompt": prompt,
        "output": output,
        "tokens": _count_tokens(prompt) + _count_tokens(output),
        "latency_sec": 0.8
    })
    with lock:
        active_agents[agent_id]["status"] = "idle"
        active_agents[agent_id]["last_output"] = output

def _chat_reply(chat_id: str, message: str):
    time.sleep(0.7)
    with lock:
        chat = chats.get(chat_id)
        if not chat or chat.get("paused"):
            return
        agent_id = chat["agent_id"]
        reply_text = f"{agent_id} yanıtı: {message[:120]}"
        chat["messages"].append({"sender": agent_id, "text": reply_text, "ts": time.time()})
        chat["tokens_total"] += _count_tokens(reply_text)
        chat["status"] = "idle"

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND); return
        data = file_path.read_bytes()
        ctype = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_body_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        return json.loads(body.decode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/": return self._send_file(SITE_DIR / "index.html")
        if path == "/logs": return self._send_file(SITE_DIR / "logs.html")
        if path == "/analytics": return self._send_file(SITE_DIR / "analytics.html")
        if path.startswith("/static/"): return self._send_file(STATIC_DIR / path.removeprefix("/static/"))
        if path == "/api/agents/status":
            with lock: return self._send_json(active_agents)
        if path == "/api/logs": return self._send_json(_read_logs())
        if path == "/api/chats":
            with lock: return self._send_json(list(chats.values()))
        if path == "/api/metrics":
            logs = _read_logs()
            total_tokens = sum(i["tokens"] for i in logs)
            avg_latency = (sum(i["latency_sec"] for i in logs)/len(logs)) if logs else 0
            return self._send_json({"total_runs": len(logs), "total_tokens": total_tokens, "avg_latency": avg_latency})
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/agents/start":
            payload = self._read_body_json()
            prompt = payload.get("prompt", "Sample mission")
            agents = payload.get("agents", DEFAULT_AGENTS)
            with lock:
                for a in agents:
                    active_agents[a["id"]] = {"name": a["name"], "role": a.get("role","generalist"), "status":"queued", "last_output":""}
            for a in agents: executor.submit(_run_agent, a["id"], prompt)
            return self._send_json({"ok":True, "active_count": len(active_agents)})

        if path == "/api/chats/start":
            payload = self._read_body_json()
            agent_id = payload.get("agent_id","chatgpt")
            chat_id = str(uuid.uuid4())[:8]
            with lock:
                chats[chat_id] = {
                    "chat_id": chat_id, "agent_id": agent_id, "title": payload.get("title", f"Yeni Sohbet - {agent_id}"),
                    "status":"idle","paused":False,"tokens_total":0,"messages":[],"created_at":time.time()
                }
            return self._send_json(chats[chat_id], HTTPStatus.CREATED)

        if path == "/api/chats/message":
            payload = self._read_body_json()
            chat_id = payload.get("chat_id","")
            message = payload.get("message","")
            if not message or chat_id not in chats:
                return self._send_json({"ok":False,"error":"invalid chat or empty message"}, HTTPStatus.BAD_REQUEST)
            with lock:
                if chats[chat_id]["paused"]:
                    return self._send_json({"ok":False,"error":"chat paused"}, HTTPStatus.CONFLICT)
                chats[chat_id]["messages"].append({"sender":"user","text":message,"ts":time.time()})
                chats[chat_id]["tokens_total"] += _count_tokens(message)
                chats[chat_id]["status"] = "running"
            executor.submit(_chat_reply, chat_id, message)
            return self._send_json({"ok":True})

        if path in ("/api/chats/pause","/api/chats/resume","/api/chats/delete"):
            payload = self._read_body_json()
            chat_id = payload.get("chat_id","")
            with lock:
                if chat_id not in chats: return self._send_json({"ok":False,"error":"chat not found"}, HTTPStatus.NOT_FOUND)
                if path.endswith("pause"): chats[chat_id]["paused"]=True; chats[chat_id]["status"]="paused"
                elif path.endswith("resume"): chats[chat_id]["paused"]=False; chats[chat_id]["status"]="idle"
                else: del chats[chat_id]; return self._send_json({"ok":True})
                return self._send_json({"ok":True,"chat":chats[chat_id]})

        self.send_error(HTTPStatus.NOT_FOUND)

def run():
    host = os.environ.get("HOST","0.0.0.0")
    port = int(os.environ.get("PORT","5000"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Server started on {host}:{port}")
    print(f"Open: http://127.0.0.1:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
