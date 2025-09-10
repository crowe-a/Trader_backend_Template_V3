from __future__ import annotations

import asyncio, json, logging, os, threading
from typing import Dict, Optional, List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from sse_starlette.sse import EventSourceResponse

import db
from chart_worker import ChartThread
from Scraper import SB, load_cookies_json

from backend import js_configure


import threading
import time, datetime, random, requests, json
from datetime import datetime
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from backend import get_ballance,  trade_executor,market_func
from bot import open_browser

import json, time, datetime, requests,asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

# -------------------------------------------
# FastAPI Setup
# -------------------------------------------
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="cok_gizli_key")

templates = Jinja2Templates(directory="templates")

bot_thread = None

# Basit user database
USERS = {"admin": "secret123"}

active_users=None
# -------------------------------------------
# Auth Dependency
# -------------------------------------------
from fastapi import Depends, HTTPException, status
from starlette.responses import RedirectResponse

def login_required(request: Request):
    if "username" not in request.session:
        # 303 ile yönlendirme
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login_form"}
        )
    return True




# -------------------------------------------
# Panel
# -------------------------------------------
@app.get("/active_runner", response_class=HTMLResponse)
def panel(request: Request, _: bool = Depends(login_required)):
    return templates.TemplateResponse("active_runner.html", {"request": request, "username": request.session["username"]})

@app.get("/add_config", response_class=HTMLResponse)
def panel(request: Request, _: bool = Depends(login_required)):
    return templates.TemplateResponse("add_config.html", {"request": request, "username": request.session["username"]})

@app.get("/stoped_runner", response_class=HTMLResponse)
def panel(request: Request, _: bool = Depends(login_required)):
    return templates.TemplateResponse("stoped_runner.html", {"request": request, "username": request.session["username"]})


# -------------------------------------------
# Bot Functions fe
# -------------------------------------------


""" step by step starting functions begin"""
def only_start():
    bot_thread = threading.Thread(target=open_browser.run)
    bot_thread.start()
    # Mevcut URL'i kontrol et

    #print("xxx")
    flag=100000
    i=0
    while flag:
        i+=1
        time.sleep(5)
        driver = open_browser.driver
        current_url = driver.current_url
        print(f"current URL: {current_url}")
        if current_url == "https://www.bydfi.com/en":
            
            flag=0
            # start_signaler()
            start_signaler_sync()
            print("chart viwer started")
            return True
        if i==20:
            print("time reseting")
            open_browser.stop()
            time.sleep(5)
            bot_thread = threading.Thread(target=open_browser.run)
            bot_thread.start()


def start_signaler_sync():
    # event loop çalışıyorsa run_until_complete hata verir, o yüzden try-except
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Zaten bir loop çalışıyor → create_task ile ekle
        asyncio.create_task(main())
    else:
        # Yeni bir loop açıp çalıştır
        asyncio.run(main())
    
    return True

""" step by step starting functions end"""




#---------------------fe endpoints begin--------------------------------------------------------------------------------------------------------------------


# """ configure from fe"""
# ConfigPayload'tan runner_id'yi çıkarıyoruz
class ConfigPayload(BaseModel):
    tv_username: str
    tv_password: str
    executor: str
    exchange: str
    starting_balance: float
    margin_type: str
    leverage: float
    currency_pair: str
    order_type: str
    base_point: float
    divide_equity: int
    transaction_ratio: Optional[float] = None  # ✅ Yeni alan


""" configuratin add a runner and chart indifier==runner_id"""
""" when any clikc come from fe to add_configuration, step by step first runner starting then chart viwer starting"""
@app.post("/add_configuration")
async def add_configuration(payload: ConfigPayload):
    data = payload.dict()
    
    # Şu anki zaman UTC timestamp olarak
    now_ts = int(datetime.datetime.utcnow().timestamp())
    data["trade_entry_time"] = now_ts
    data["trade_exit_time"] = None
    data["trade_pnl"] = 0.0

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO configuration (
                    tv_username, tv_password, executor, exchange,
                    starting_balance, margin_type, leverage, currency_pair,
                    order_type, base_point, divide_equity, transaction_ratio,
                    trade_entry_time, trade_exit_time, trade_pnl
                ) VALUES (
                    %(tv_username)s, %(tv_password)s, %(executor)s, %(exchange)s,
                    %(starting_balance)s, %(margin_type)s, %(leverage)s, %(currency_pair)s,
                    %(order_type)s, %(base_point)s, %(divide_equity)s, %(transaction_ratio)s,
                    %(trade_entry_time)s, %(trade_exit_time)s, %(trade_pnl)s
                )
                ON CONFLICT (currency_pair)
                DO UPDATE SET
                    margin_type       = EXCLUDED.margin_type,
                    leverage          = EXCLUDED.leverage,
                    order_type        = EXCLUDED.order_type,
                    base_point        = EXCLUDED.base_point,
                    divide_equity     = EXCLUDED.divide_equity,
                    transaction_ratio = EXCLUDED.transaction_ratio
                RETURNING runner_id, currency_pair;
                """,
                data
            )
            runner_id, currency_pair = cur.fetchone()

        conn.commit()
    try:
        #test_system_copy.IDENTIFIER=str(runner_id)#SPXUSDT.P
        test_system_copy.IDENTIFIER=currency_pair
        print(currency_pair)#sol-usdt
        print(test_system_copy.IDENTIFIER)
        print(type(test_system_copy.IDENTIFIER))
        
        # start_signaler_sync()
        only_start()
            
    except:
        log.warning(" runner start error  ")
        
        

        



    return {"status": "added", "runner_id": runner_id}

@app.get("/get_configurations")
async def get_configurations(limit: int = 10):
    with db.connect() as conn:
        with conn.cursor() as cur:
            configurations = db.fetch_all_configurations(cur, limit)
    # js={'identifier': 'JSAqsyMo', 'kind': 'close', 'Recalc': False, 'chart': {'url': 'https://www.tradingview.com/chart/JSAqsyMo/', 'interval': '1m'},
    #   'trade': {'id': '2177', 'entry_type': 'Entry', 'entry_signal': 'Strong Sell, Strong Buy', 'entry_price': 1.2638, 'entry_time': 'Aug 27, 2025, 14:48', 'exit_price': 1.2638, 'exit_time': 'Aug 27, 2025, 14:50', 'exit_signal': 'Strong Buy', 'position': '289.98, 365.75 usdt'},
    #   'raw': {'num': '2177', 'signal': 'Strong Sell, Strong Buy', 'type': 
    # 'Entry', 'open_time': 'Aug 27, 2025, 14:48', 'close_time': 'Aug 27, 2025, 14:50', 'open_price': '1.2638', 'close_price': '1.2638', 'position_size': '289.98, 365.75 usdt'}}

    # market_func.getpayload(js)
    return {"configurations": configurations}



@app.get("/active_config")
async def active_config():
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT runner_id, currency_pair, trade_entry_time, exchange,
                       executor, trade_exit_time, trade_pnl
                FROM configuration
                WHERE trade_exit_time IS NULL
                ORDER BY runner_id DESC
            """)
            rows = cur.fetchall()
    
    active_configs = []
    for r in rows:
        trade_exit_time = r[5]
        status = "running" if trade_exit_time is None else "stopped"
        pnl = float(r[6]) if r[6] is not None else 0.0
        active_configs.append({
            "runner_id": r[0],
            "currency_pair": r[1],
            "trade_entry_time": r[2] if r[2] else 0,  #  timestamp() not include
            "exchange": r[3],
            "broker": r[4],
            "status": status,
            "trade_pnl": pnl
        })

    return {"active_configs": active_configs}

@app.get("/stopped_config")
async def stopped_config():
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT runner_id, currency_pair, trade_entry_time, trade_exit_time,
                       exchange, executor, trade_pnl
                FROM configuration
                WHERE trade_exit_time IS NOT NULL
                ORDER BY runner_id DESC
            """)
            rows = cur.fetchall()

    stopped_configs = []
    for r in rows:
        pnl = float(r[6]) if r[6] is not None else 0.0
        stopped_configs.append({
            "runner_id": r[0],
            "currency_pair": r[1],
            "trade_entry_time": r[2] if r[2] else 0,
            "trade_exit_time": r[3] if r[3] else 0,
            "exchange": r[4],
            "broker": r[5],
            "status": "stopped",
            "trade_pnl": pnl
        })

    return {"stopped_configs": stopped_configs}




#---------------------fe endpoints end-------------------------------------------------------------------------------------------------------------------------------------------------




#---------------------webhook begin-----------------------------

# --------------------------------------
# START / STOP Webhook / configure
# --------------------------------------
first_start_flag = False  # program ilk açıldığında False

@app.post("/configure")
async def configure(request: Request):
    global first_start_flag

    if not first_start_flag:  # daha önce hiç çalışmadıysa
        js_configure.reset_json_file("activs.json")
        first_start_flag = True   # bir daha çalışmasın
        print("First config arrived, activs.json was reset")
    else:
        print("Next config, no reset")

        
    data = await request.json()
    runner_id = data.get("Runner_id")

    if not runner_id:
        return {"status": "error", "message": "Runner_id didnt found"}

    # Local JSON oku
    data_from_local = js_configure.read_data()
    print(data_from_local)
    # Runner_id daha önce var mı?
    exists = any(record[0] == runner_id for record in data_from_local)

    if not exists:
        # Yeni kayıt ekle
        action = data.get("action")

        Runner_id=data.get("Runner_id")

        amount=data.get("amount")
        Tr=data.get("Tr")
        margin=data.get("margin")#Cross Isolated
        leverageX=data.get("leverage")
        symbol=data.get("symbol")
        market_type=data.get("market_type")#"Market" or "Limit",

        #if limit selected
        Tick_Size=data.get("Tick_Size")# + - 
        order_expiry=data.get("order_expiry") #order expiry minutes

        import time
        from datetime import datetime, timedelta

        now = datetime.now()
        expire_time = now + timedelta(minutes=int(order_expiry))

        # epoch (Unix time) olarak yaz
        expire_timestamp = int(expire_time.timestamp())

        print("Şu an (epoch):", int(time.time()))
        print("5 dk sonrası (epoch):", expire_timestamp)


        js_configure.add_record([Runner_id,"",amount,Tr,margin,leverageX,symbol,market_type,Tick_Size,expire_timestamp,"","","",""])#son 4 open price,satın alınan yada satılan coin miktarı (önceki işlemleri toplayarak ilerle),işlemlerdeki kar durumu,kapanış için kalan süre
        
        push_event("configured", kind="dead", raw={"message": "Runner id append in local"})   
        data_from_local = js_configure.read_data()
        print("confiugre data: ",data_from_local)
        return {"status": "ok", "message": "Yeni kayıt eklendi", "record": data}

    else:
        push_event("configured", kind="dead", raw={"message": "Runner id already append in local"})
        return {"status": "success"}

   
""" start tv """
from fastapi import FastAPI, BackgroundTasks
from test_system_copy import main
import test_system_copy

@app.post("/start_stop")
async def start_runner(background_tasks: BackgroundTasks):
    # async ffuncton to call main signaler
    background_tasks.add_task(main)  # !
    return {"status": "signaler started"}
    





@app.post("/startstop")
async def start_stop(request: Request):
    data = await request.json()

    
    action = data.get("action")
    
    #username = data.get("username")

    # users = load_users_from_js("active_users.js")
    # for user in users:
    #     if user["username"] == username :
    #save_users_to_js(user,"active_users.js")
    #JSONResponse(content={"status": "success", "message": "bot started"}, status_code=200)
    #return {"status": "success"}
    #action = data.get("action")
    identifier = "myChart"
    if action == "start":
        global bot_thread
        if getattr(open_browser, "running", False):
            # Bot zaten çalışıyorsa
            return JSONResponse(content={"status": "400", "message": "Bot has already started."})

        # Botu başlat
        bot_thread = threading.Thread(target=open_browser.run)
        bot_thread.start()
        # Mevcut URL'i kontrol et

        
        flag=100000
        i=0
        while flag:
            i+=1
            time.sleep(3)
            driver = open_browser.driver
            current_url = driver.current_url
            print(f"Mevcut URL: {current_url}")
            if current_url == "https://www.bydfi.com/en":
                push_event(identifier, kind="alive", raw={"message": "Bot started"})
                flag=0
                return {"status": "success"}
            if i==20:
                print("time reseting")
                open_browser.stop()
                time.sleep(5)
                bot_thread = threading.Thread(target=open_browser.run)
                bot_thread.start()

                
                

    elif action == "stop":
        if getattr(open_browser, "running", False):
            open_browser.stop()
            push_event(identifier, kind="dead", raw={"message": "Bot stopped"})
            return {"status": "success"}

        push_event(identifier, kind="dead", raw={"message": "Bot already stopped"})
        return {"status": "success"}

    else:
        return JSONResponse(content={"status": "error", "message": "Invalid action"}, status_code=400)

# --------------------------------------
# Login login and amount  Webhook
# --------------------------------------


    

chart_events_buffer = {}

# -----------------------------
# Event generator
# -----------------------------
def generate_event(identifier, kind, trade=None, raw=None):
    event = {
        "identifier": identifier,
        "kind": kind,
        "chart": {
            "url": f"https://partner.bydfi.com/chart/{identifier}",
            "interval": "1m"
        }
    }
    if trade:
        event["trade"] = trade
    if raw:
        event["raw"] = raw
    if kind == "alive":
        event["activated_at"] = datetime.datetime.utcnow().isoformat()
    if kind == "dead":
        event["stopped_at"] = datetime.datetime.utcnow().isoformat()
    return event


def push_event(identifier, kind, trade=None, raw=None, executor_url=None):
    event = generate_event(identifier, kind, trade, raw)

    if identifier not in chart_events_buffer:
        chart_events_buffer[identifier] = []
    chart_events_buffer[identifier].append(event)

    if executor_url:
        try:
            requests.post(executor_url, json=event)
        except Exception as e:
            print(f"Executor'a gönderilemedi: {e}")

    return event


# -----------------------------
# Event Stream (SSE)
# -----------------------------
@app.get("/charts/{identifier}/events_stream")
async def events_stream(identifier: str):
    async def event_generator():
        last_index = 0
        while True:
            events = chart_events_buffer.get(identifier, [])
            sent_event = False
            while last_index < len(events):
                ev = events[last_index]
                yield f"data: {json.dumps(ev)}\n\n"
                last_index += 1
                sent_event = True

            # Eğer yeni event yoksa sadece beklet
            if not sent_event:
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(0.1)  # yoğunluk için küçük bekleme

    return StreamingResponse(event_generator(), media_type="text/event-stream")


#------------------webhook end----------------------







"""
FastAPI façade for Next Layer Gauntlet Signaler.
"""



# app = FastAPI()
log = logging.getLogger("api")
logging.getLogger('seleniumwire').setLevel(logging.WARNING)
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
    log.info("startup: event loop captured"),

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
#  Endpoints
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














# -------------------------------------------
# Run
# -------------------------------------------
# uvicorn main:app --reload
