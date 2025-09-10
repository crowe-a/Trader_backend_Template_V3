"""
FastAPI façade for Next Layer Gauntlet Signaler.
"""

from __future__ import annotations

import asyncio, json, logging, os, threading
from typing import Dict, Optional, List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from sse_starlette.sse import EventSourceResponse

import db
from chart_worker import ChartThread
from Scraper import SB, load_cookies_json

app = FastAPI()
log = logging.getLogger("api")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

# -----------------------------------------------------------------------------
# State
# -----------------------------------------------------------------------------
MAIN_LOOP: asyncio.AbstractEventLoop | None = None

# Broadcast-friendly: store a list of subscriber queues per identifier
listeners: Dict[str, List[asyncio.Queue]] = {}  # id -> [queues...]
threads:   Dict[str, ChartThread]         = {}  # id -> thread
subs:      Dict[str, int]                 = {}  # id -> active SSE count
chart_urls: Dict[str, str]                = {}  # id -> chart_url

WEBHOOK_LOG: list[dict] = []
WEBHOOK_MAX = 500

@app.on_event("startup")
async def startup():
    global MAIN_LOOP
    MAIN_LOOP = asyncio.get_running_loop()
    log.info("startup: event loop captured")

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class ChartSpec(BaseModel):
    identifier: str
    chart_url:  str
    executor_url: Optional[HttpUrl] = None
    refresh_enabled: bool = False
    # NEW: allow per-request TradingView credentials (optional)
    tv_username: Optional[str] = None
    tv_password: Optional[str] = None

class ViewSpec(BaseModel):
    identifier: str
    chart_url:  str

class LoginRequest(BaseModel):
    username: str
    password: str

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _publish(identifier: str, evt: dict):
    """Fan-out an event to all subscriber queues for this identifier."""
    if MAIN_LOOP is None:
        return
    queues = listeners.get(identifier)
    if not queues:
        return
    subs_count = subs.get(identifier, 0)
    kind = evt.get("kind")
    trade_id = evt.get("trade", {}).get("id")
    log.info("publish %s trade=%s -> %d subs", kind, trade_id, subs_count)
    for q in list(queues):
        try:
            MAIN_LOOP.call_soon_threadsafe(q.put_nowait, evt)
        except Exception:
            continue

def _stop_queue(identifier: str):
    """Send sentinel to all queues so active SSE generators exit cleanly."""
    queues = listeners.get(identifier) or []
    if MAIN_LOOP:
        for q in list(queues):
            try:
                MAIN_LOOP.call_soon_threadsafe(q.put_nowait, None)
            except Exception:
                continue

def _open_visible_window(identifier: str, url: str):
    try:
        with SB(headless=False) as sb:
            load_cookies_json(sb, identifier, url)
            sb.open(url)
            try:
                sb.driver.maximize_window()
            except Exception:
                pass
            sb.wait_for_ready_state_complete()
            if os.getenv("VIEW_NONBLOCK", "0") == "1":
                sb.sleep(5)
                return
            try:
                input("Viewer open. Press Enter here to close it …")
            except Exception:
                sb.sleep(10)
    except Exception:
        log.exception("viewer thread crashed for %s", identifier)

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/charts")
async def list_charts():
    return {"running": list(listeners.keys())}

@app.get("/charts/{identifier}/status")
async def chart_status(identifier: str):
    t = threads.get(identifier)
    if not t:
        return {"running": False}
    return {
        "running": True,
        "opens_seen": t.opens_seen,
        "closes_seen": t.closes_seen,
        "last_event_ts": t.last_event_ts.isoformat() if t.last_event_ts else None,
        "chart_url": chart_urls.get(identifier),
        "interval": t.interval_str,
        "next_refresh_at": t.next_refresh_at.isoformat() if t.next_refresh_at else None,
        "refresh_enabled": t.refresh_enabled,
    }

@app.post("/charts", status_code=201)
async def create_chart(spec: ChartSpec):
    log.info("POST /charts start id=%s", spec.identifier)
    if spec.identifier in listeners:
        raise HTTPException(409, "chart already running")

    # Initialize subscriber list for this identifier
    listeners[spec.identifier] = []
    subs[spec.identifier] = 0
    chart_urls[spec.identifier] = spec.chart_url

    w = ChartThread(
        identifier=spec.identifier,
        chart_url=spec.chart_url,
        publish=lambda evt: _publish(spec.identifier, evt),
        executor_url=str(spec.executor_url) if spec.executor_url else None,
        poll_interval=0.25,
        deep_scan_every=5.0,
        status_every=10.0,
        refresh_enabled=spec.refresh_enabled,
        # pass-through new (optional) creds
        tv_username=spec.tv_username,
        tv_password=spec.tv_password,
    )
    threads[spec.identifier] = w
    w.start()
    log.info("POST /charts id=%s thread started", spec.identifier)
    return {"ok": True}

@app.delete("/charts/{identifier}")
async def stop_chart(identifier: str):
    if identifier not in listeners:
        raise HTTPException(404, "unknown chart")

    t = threads.pop(identifier, None)
    if t:
        t.stop()
        log.info("chart %s stop requested", identifier)

    _stop_queue(identifier)
    listeners.pop(identifier, None)
    subs.pop(identifier, None)
    chart_urls.pop(identifier, None)
    return {"ok": True}

@app.get("/charts/{identifier}/events")
async def sse_all(identifier: str):
    return await _sse_impl(identifier, close_only=False)

@app.get("/charts/{identifier}/closed/events")
async def sse_closed(identifier: str):
    return await _sse_impl(identifier, close_only=True)

async def _sse_impl(identifier: str, close_only: bool):
    if identifier not in listeners:
        raise HTTPException(404, "unknown chart")

    q: asyncio.Queue = asyncio.Queue(maxsize=1000)
    listeners[identifier].append(q)
    subs[identifier] = subs.get(identifier, 0) + 1
    log.info("SSE subscribe %s (subs=%d, close_only=%s)", identifier, subs[identifier], close_only)

    async def gen():
        try:
            while True:
                evt = await q.get()
                if evt is None:
                    break
                if close_only and evt.get("kind") != "close":
                    continue
                yield {"data": json.dumps(evt)}
        finally:
            subs[identifier] = max(0, subs.get(identifier, 1) - 1)
            try:
                if identifier in listeners and q in listeners[identifier]:
                    listeners[identifier].remove(q)
            except Exception:
                pass
            log.info("SSE unsubscribe %s (subs=%d)", identifier, subs.get(identifier, 0))

    return EventSourceResponse(gen())

@app.get("/charts/{identifier}/trades")
async def get_trades(identifier: str, limit: int = Query(200, ge=1, le=2000)):
    with db.connect() as conn, conn.cursor() as cur:
        rows = db.fetch_trades(cur, identifier, limit)
        return {"identifier": identifier, "count": len(rows), "rows": rows}

# --- Viewer (non-blocking) ---
@app.post("/view", status_code=202)
async def open_view(spec: ViewSpec):
    threading.Thread(
        target=_open_visible_window,
        args=(spec.identifier, spec.chart_url),
        daemon=True,
        name=f"Viewer[{spec.identifier}]",
    ).start()
    return {"ok": True, "started": True}

@app.post("/charts/{identifier}/view", status_code=202)
async def view_chart(identifier: str):
    url = chart_urls.get(identifier) or os.getenv("CHART_URL")
    if not url:
        raise HTTPException(400, "no chart_url known; supply via /view")
    threading.Thread(
        target=_open_visible_window,
        args=(identifier, url),
        daemon=True,
        name=f"Viewer[{identifier}]",
    ).start()
    return {"ok": True, "started": True}

# --- Debug webhook sink ---
@app.post("/debug/executor")
async def debug_executor(payload: dict):
    WEBHOOK_LOG.append(payload)
    if len(WEBHOOK_LOG) > WEBHOOK_MAX:
        del WEBHOOK_LOG[: len(WEBHOOK_LOG) - WEBHOOK_MAX]
    log.info("EXECUTOR WEBHOOK: %s", payload.get("kind"))
    return {"ok": True}

@app.get("/debug/executor")
async def get_debug_webhooks(clear: bool = False):
    data = list(WEBHOOK_LOG)
    if clear:
        WEBHOOK_LOG.clear()
    return {"count": len(data), "events": data}

# --- Simple login check (reads credentials from .env via os.getenv) ---
@app.post("/login")
async def login_endpoint(req: LoginRequest):
    ok = (
        req.username == os.getenv("API_LOGIN_USERNAME", "")
        and req.password == os.getenv("API_LOGIN_PASSWORD", "")
    )
    return {"authenticated": bool(ok)}