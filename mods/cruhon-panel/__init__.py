"""
cruhon-panel — live log-stream dashboard for Cruhon  (@panel.*)

A zero-dependency web panel. Start it, point a browser at the printed URL,
and watch logs, metrics, and custom events stream in real time over
Server-Sent Events (SSE). Nothing but the Python standard library.

━━━ LIFECYCLE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @panel.start[]                  — start on the default host/port → URL
  @panel.start[port]              — start on a specific port → URL
  @panel.start[port; host]        — start on host:port → URL
  @panel.stop[]                   — shut the panel down
  @panel.running[]                → True if the server is up
  @panel.url[]                    → dashboard URL ("" if not running)
  @panel.open[]                   — open the dashboard in a web browser
  @panel.clients[]                → number of connected browsers
  @panel.wait[]                   — block forever, keeping the panel alive
  @panel.wait[seconds]            — keep it alive for N seconds

━━━ STREAMING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @panel.log[msg]                 — stream a log line (level INFO)
  @panel.log[msg; level]          — stream with a level (DEBUG/INFO/WARNING/ERROR)
  @panel.debug[msg]               — stream a DEBUG line
  @panel.info[msg]                — stream an INFO line
  @panel.warn[msg]                — stream a WARNING line
  @panel.error[msg]               — stream an ERROR line
  @panel.metric[name; value]      — push/update a named metric tile
  @panel.event[type; data]        — push an arbitrary JSON event
  @panel.clear[]                  — tell every browser to clear its view

━━━ @log.* INTEGRATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @panel.attach_logging[]         — mirror all @log.* / logging output to the panel
  @panel.attach_logging[level]    — … at or above a level
  @panel.detach_logging[]         — stop mirroring

Typical use:
  @panel.start[8787]
  @panel.attach_logging["INFO"]
  @log.info["server warming up"]
  @panel.metric["users"; 42]
  @panel.wait[]
"""
from __future__ import annotations

import json
import threading
import time
from collections import deque


# ─────────────────────────────────────────────────────────────
# DASHBOARD (served at /)
# ─────────────────────────────────────────────────────────────

_DASHBOARD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cruhon Panel</title>
<style>
  :root { --bg:#0d1117; --panel:#161b22; --line:#21262d; --txt:#c9d1d9;
          --muted:#8b949e; --accent:#58a6ff; }
  * { box-sizing:border-box; }
  body { margin:0; font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
         background:var(--bg); color:var(--txt); }
  header { display:flex; align-items:center; gap:12px; padding:12px 18px;
           background:var(--panel); border-bottom:1px solid var(--line); position:sticky; top:0; }
  header h1 { font-size:15px; margin:0; font-weight:600; letter-spacing:.3px; }
  #dot { width:10px; height:10px; border-radius:50%; background:#f85149; transition:.3s; }
  #dot.on { background:#3fb950; box-shadow:0 0 8px #3fb950; }
  #status { color:var(--muted); font-size:12px; }
  .spacer { flex:1; }
  button { background:#21262d; color:var(--txt); border:1px solid var(--line);
           border-radius:6px; padding:5px 12px; cursor:pointer; font:inherit; }
  button:hover { border-color:var(--accent); color:var(--accent); }
  #metrics { display:flex; flex-wrap:wrap; gap:10px; padding:14px 18px; }
  .metric { background:var(--panel); border:1px solid var(--line); border-radius:8px;
            padding:10px 16px; min-width:120px; }
  .metric .k { color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.5px; }
  .metric .v { font-size:22px; font-weight:600; margin-top:2px; }
  #log { padding:8px 18px 40px; }
  .row { display:flex; gap:10px; padding:2px 0; border-bottom:1px solid rgba(255,255,255,.03);
         white-space:pre-wrap; word-break:break-word; }
  .row .ts { color:var(--muted); flex:0 0 88px; }
  .row .lv { flex:0 0 64px; font-weight:600; }
  .DEBUG .lv { color:#8b949e; } .INFO .lv { color:#58a6ff; }
  .WARNING .lv { color:#d29922; } .ERROR .lv { color:#f85149; }
  .EVENT .lv { color:#bc8cff; }
  .row .msg { flex:1; }
</style>
</head>
<body>
<header>
  <span id="dot"></span>
  <h1>Cruhon Panel</h1>
  <span id="status">connecting…</span>
  <span class="spacer"></span>
  <button onclick="document.getElementById('log').innerHTML=''">Clear</button>
  <button id="pause" onclick="toggle()">Pause</button>
</header>
<div id="metrics"></div>
<div id="log"></div>
<script>
  const logEl = document.getElementById('log');
  const metricsEl = document.getElementById('metrics');
  const dot = document.getElementById('dot');
  const status = document.getElementById('status');
  const metrics = {};
  let paused = false, count = 0;
  function toggle(){ paused = !paused; document.getElementById('pause').textContent = paused?'Resume':'Pause'; }
  function fmtTime(t){ const d=new Date(t*1000); return d.toLocaleTimeString(); }
  function addLog(ev){
    if (paused) return;
    const row = document.createElement('div');
    const lv = (ev.level||'INFO').toUpperCase();
    row.className = 'row ' + lv;
    row.innerHTML = `<span class="ts">${fmtTime(ev.t)}</span>`+
                    `<span class="lv">${lv}</span>`+
                    `<span class="msg"></span>`;
    row.querySelector('.msg').textContent = ev.msg;
    logEl.appendChild(row);
    if (++count > 2000) logEl.removeChild(logEl.firstChild);
    window.scrollTo(0, document.body.scrollHeight);
  }
  function setMetric(name, value){
    let m = metrics[name];
    if (!m){
      m = document.createElement('div'); m.className='metric';
      m.innerHTML = `<div class="k"></div><div class="v"></div>`;
      m.querySelector('.k').textContent = name;
      metricsEl.appendChild(m); metrics[name]=m;
    }
    m.querySelector('.v').textContent = value;
  }
  function connect(){
    const es = new EventSource('/stream');
    es.onopen = () => { dot.classList.add('on'); status.textContent='live'; };
    es.onerror = () => { dot.classList.remove('on'); status.textContent='reconnecting…'; };
    es.onmessage = (e) => {
      let ev; try { ev = JSON.parse(e.data); } catch(_) { return; }
      if (ev.kind === 'metric') setMetric(ev.name, ev.value);
      else if (ev.kind === 'clear') { logEl.innerHTML=''; }
      else if (ev.kind === 'event') addLog({t:ev.t, level:'EVENT', msg:ev.type+': '+JSON.stringify(ev.data)});
      else addLog(ev);
    };
  }
  connect();
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# PANEL CORE
# ─────────────────────────────────────────────────────────────

class _Panel:
    def __init__(self, default_port=8787, default_host="127.0.0.1", history_size=200):
        self._server = None
        self._thread = None
        self._host = default_host
        self._port = None
        self._default_port = default_port
        self._default_host = default_host
        self._subscribers: set = set()
        self._lock = threading.Lock()
        self._history = deque(maxlen=history_size)
        self._log_handler = None
        self._seq = 0

    # ── Event fan-out ─────────────────────────────────────────

    def _push(self, event: dict):
        event.setdefault("t", time.time())
        self._seq += 1
        event["seq"] = self._seq
        data = json.dumps(event, default=str)
        self._history.append(data)
        with self._lock:
            dead = []
            for q in self._subscribers:
                try:
                    q.put_nowait(data)
                except Exception:
                    dead.append(q)
            for q in dead:
                self._subscribers.discard(q)

    def _subscribe(self):
        import queue
        q = queue.Queue(maxsize=1000)
        with self._lock:
            self._subscribers.add(q)
        return q

    def _unsubscribe(self, q):
        with self._lock:
            self._subscribers.discard(q)

    # ── Server lifecycle ──────────────────────────────────────

    def start(self, args: list):
        if self._server is not None:
            return self.url([])
        import http.server
        port = int(args[0]) if len(args) > 0 and args[0] is not None else self._default_port
        host = str(args[1]) if len(args) > 1 and args[1] is not None else self._default_host
        panel = self

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):  # silence default access logging
                pass

            def do_GET(self):
                if self.path.startswith("/stream"):
                    self._serve_stream()
                else:
                    self._serve_dashboard()

            def _serve_dashboard(self):
                body = _DASHBOARD.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(body)

            def _serve_stream(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                q = panel._subscribe()
                try:
                    # Replay recent history so a fresh browser has context.
                    for data in list(panel._history):
                        self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    while panel._server is not None:
                        try:
                            data = q.get(timeout=15)
                            self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
                        except Exception:
                            # Heartbeat comment keeps the connection (and our
                            # disconnect detection) alive during quiet periods.
                            self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass
                finally:
                    panel._unsubscribe(q)

        self._server = http.server.ThreadingHTTPServer((host, port), Handler)
        self._host = host
        self._port = self._server.server_address[1]
        self._thread = threading.Thread(
            target=self._server.serve_forever, name="cruhon-panel", daemon=True
        )
        self._thread.start()
        return self.url([])

    def stop(self, args: list):
        self.detach_logging([])
        srv, self._server = self._server, None
        if srv is not None:
            try:
                srv.shutdown()
                srv.server_close()
            except Exception:
                pass
        self._thread = None
        self._port = None
        with self._lock:
            self._subscribers.clear()
        self._history.clear()

    def running(self, args: list):
        return self._server is not None

    def url(self, args: list):
        if self._server is None:
            return ""
        host = "localhost" if self._host in ("0.0.0.0", "") else self._host
        return f"http://{host}:{self._port}"

    def open(self, args: list):
        u = self.url([])
        if u:
            import webbrowser
            webbrowser.open(u)
        return u

    def clients(self, args: list):
        with self._lock:
            return len(self._subscribers)

    def wait(self, args: list):
        seconds = float(args[0]) if args and args[0] is not None else None
        if seconds is None:
            try:
                while self._server is not None:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                self.stop([])
        else:
            deadline = time.time() + seconds
            while self._server is not None and time.time() < deadline:
                time.sleep(min(0.5, max(0.0, deadline - time.time())))

    # ── Streaming helpers ─────────────────────────────────────

    def log(self, args: list):
        msg = str(args[0]) if args else ""
        level = str(args[1]).upper() if len(args) > 1 else "INFO"
        self._push({"kind": "log", "level": level, "msg": msg})
        return msg

    def debug(self, args: list):
        return self.log([args[0] if args else "", "DEBUG"])

    def info(self, args: list):
        return self.log([args[0] if args else "", "INFO"])

    def warn(self, args: list):
        return self.log([args[0] if args else "", "WARNING"])

    def error(self, args: list):
        return self.log([args[0] if args else "", "ERROR"])

    def metric(self, args: list):
        if len(args) < 2:
            raise RuntimeError("[cruhon-panel] @panel.metric requires a name and a value.")
        self._push({"kind": "metric", "name": str(args[0]), "value": args[1]})
        return args[1]

    def event(self, args: list):
        etype = str(args[0]) if args else "event"
        data = args[1] if len(args) > 1 else None
        self._push({"kind": "event", "type": etype, "data": data})

    def clear(self, args: list):
        self._push({"kind": "clear"})

    # ── @log.* integration ────────────────────────────────────

    def attach_logging(self, args: list):
        import logging
        if self._log_handler is not None:
            return
        panel = self

        class _PanelHandler(logging.Handler):
            def emit(self, record):
                try:
                    panel._push({
                        "kind": "log",
                        "level": record.levelname,
                        "msg": self.format(record),
                    })
                except Exception:
                    pass

        handler = _PanelHandler()
        handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
        if args and args[0] is not None:
            handler.setLevel(getattr(logging, str(args[0]).upper(), logging.NOTSET))
        root = logging.getLogger()
        if root.level == logging.WARNING:
            # Default root level hides INFO/DEBUG — widen so the panel sees them.
            root.setLevel(logging.DEBUG)
        root.addHandler(handler)
        self._log_handler = handler

    def detach_logging(self, args: list):
        if self._log_handler is not None:
            import logging
            try:
                logging.getLogger().removeHandler(self._log_handler)
            except Exception:
                pass
            self._log_handler = None


# ─────────────────────────────────────────────────────────────
# METHOD REGISTRY
# ─────────────────────────────────────────────────────────────

_METHODS = (
    "start", "stop", "running", "url", "open", "clients", "wait",
    "log", "debug", "info", "warn", "error", "metric", "event", "clear",
    "attach_logging", "detach_logging",
)


# ─────────────────────────────────────────────────────────────
# REGISTRATION
# ─────────────────────────────────────────────────────────────

def register(api):
    api.lib("panel", None)

    def _make_handler(method_name: str):
        def handler(args: list) -> str:
            if args:
                return f'__ns__["panel"].call("{method_name}", {", ".join(args)})'
            return f'__ns__["panel"].call("{method_name}")'
        return handler

    for m in _METHODS:
        api.lib_call("panel", m, _make_handler(m))

    panel = _Panel(
        default_port=api.config("default_port", 8787),
        default_host=api.config("default_host", "127.0.0.1"),
        history_size=api.config("history_size", 200),
    )
    ns = api.namespace("panel")
    for m in _METHODS:
        ns.register(m, getattr(panel, m))

    ns.hook("destroy", lambda ns_obj: panel.stop([]))
