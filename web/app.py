from __future__ import annotations
import json, mimetypes, threading, time, uuid, os
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR=Path(__file__).resolve().parent
SITE_DIR=BASE_DIR/"site"; STATIC_DIR=BASE_DIR/"static"; RUN=BASE_DIR/"runtime"; RUN.mkdir(exist_ok=True)
LOG=RUN/"agent_logs.json"
executor=ThreadPoolExecutor(max_workers=20)
active_agents={}; chats={}; lock=threading.Lock()
DEFAULT_AGENTS=[{"id":"claude","name":"Claude","role":"Analyst"},{"id":"chatgpt","name":"ChatGPT","role":"Generalist"},{"id":"gemini","name":"Gemini","role":"Researcher"}]

def tok(t): return max(1,len(t.split()))
def read_logs(): return json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
def write_log(e):
    x=read_logs(); x.append(e); LOG.write_text(json.dumps(x[-500:],ensure_ascii=False,indent=2),encoding="utf-8")

def run_agent(agent_id,prompt):
    with lock: active_agents[agent_id]["status"]="running"
    time.sleep(0.8); out=f"{agent_id} processed: {prompt[:100]}"
    write_log({"timestamp":time.time(),"agent_id":agent_id,"prompt":prompt,"output":out,"tokens":tok(prompt)+tok(out),"latency_sec":0.8})
    with lock: active_agents[agent_id]["status"]="idle"; active_agents[agent_id]["last_output"]=out

def chat_reply(chat_id,msg):
    time.sleep(0.7)
    with lock:
        c=chats.get(chat_id)
        if not c or c.get("paused"): return
        txt=f"{c['agent_id']} yanıtı: {msg[:140]}"
        c["messages"].append({"sender":c["agent_id"],"text":txt,"ts":time.time()})
        c["tokens_total"]+=tok(txt); c["status"]="idle"

class H(BaseHTTPRequestHandler):
    def js(self,p,s=200):
        b=json.dumps(p,ensure_ascii=False).encode(); self.send_response(s); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def file(self,p):
        if not p.exists(): self.send_error(404); return
        d=p.read_bytes(); ct=mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        self.send_response(200); self.send_header("Content-Type",ct); self.send_header("Content-Length",str(len(d))); self.end_headers(); self.wfile.write(d)
    def body(self):
        l=int(self.headers.get("Content-Length","0")); return json.loads((self.rfile.read(l) if l else b"{}").decode())
    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/": return self.file(SITE_DIR/"index.html")
        if p=="/logs": return self.file(SITE_DIR/"logs.html")
        if p=="/analytics": return self.file(SITE_DIR/"analytics.html")
        if p.startswith("/static/"): return self.file(STATIC_DIR/p.removeprefix("/static/"))
        if p=="/api/agents/status":
            with lock: return self.js(active_agents)
        if p=="/api/logs": return self.js(read_logs())
        if p=="/api/chats":
            with lock: return self.js(list(chats.values()))
        if p=="/api/metrics":
            x=read_logs(); tt=sum(i["tokens"] for i in x); al=(sum(i["latency_sec"] for i in x)/len(x)) if x else 0
            return self.js({"total_runs":len(x),"total_tokens":tt,"avg_latency":al})
        self.send_error(404)
    def do_POST(self):
        p=urlparse(self.path).path
        if p=="/api/agents/start":
            b=self.body(); prompt=b.get("prompt","Sample mission"); agents=b.get("agents",DEFAULT_AGENTS)
            with lock:
                for a in agents: active_agents[a["id"]]={"name":a["name"],"role":a.get("role","generalist"),"status":"queued","last_output":""}
            for a in agents: executor.submit(run_agent,a["id"],prompt)
            return self.js({"ok":True,"active_count":len(active_agents)})
        if p=="/api/chats/start":
            b=self.body(); aid=b.get("agent_id","chatgpt"); cid=str(uuid.uuid4())[:8]
            with lock: chats[cid]={"chat_id":cid,"agent_id":aid,"title":b.get("title",f"Yeni Sohbet - {aid}"),"status":"idle","paused":False,"tokens_total":0,"messages":[]}
            return self.js(chats[cid],201)
        if p=="/api/chats/message":
            b=self.body(); cid=b.get("chat_id",""); m=b.get("message","")
            if not m or cid not in chats: return self.js({"ok":False,"error":"invalid chat or empty message"},400)
            with lock:
                if chats[cid]["paused"]: return self.js({"ok":False,"error":"chat paused"},409)
                chats[cid]["messages"].append({"sender":"user","text":m,"ts":time.time()}); chats[cid]["tokens_total"]+=tok(m); chats[cid]["status"]="running"
            executor.submit(chat_reply,cid,m); return self.js({"ok":True})
        if p in ("/api/chats/pause","/api/chats/resume","/api/chats/delete"):
            b=self.body(); cid=b.get("chat_id","")
            with lock:
                if cid not in chats: return self.js({"ok":False,"error":"chat not found"},404)
                if p.endswith("pause"): chats[cid]["paused"]=True; chats[cid]["status"]="paused"
                elif p.endswith("resume"): chats[cid]["paused"]=False; chats[cid]["status"]="idle"
                else: del chats[cid]; return self.js({"ok":True})
                return self.js({"ok":True,"chat":chats[cid]})
        self.send_error(404)

if __name__=="__main__":
    host=os.environ.get("HOST","0.0.0.0"); port=int(os.environ.get("PORT","5000"))
    s=ThreadingHTTPServer((host,port),H); print(f"Server started on {host}:{port}"); print(f"http://127.0.0.1:{port}"); s.serve_forever()
