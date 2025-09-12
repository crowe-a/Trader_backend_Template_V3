from __future__ import annotations

import asyncio, json, logging, os, threading
from typing import Dict, Optional, List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from sse_starlette.sse import EventSourceResponse

import db

import sys
sys.dont_write_bytecode = True

from backend import js_configure
from backend import signaler_req

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
log = logging.getLogger("api")
app.add_middleware(SessionMiddleware, secret_key="secret key")

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

@app.get("/global_page", response_class=HTMLResponse)
def panel(request: Request, _: bool = Depends(login_required)):
    return templates.TemplateResponse("globalpage.html", {"request": request, "username": request.session["username"]})


# -------------------------------------------
# Bot Functions fe
# -------------------------------------------





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
    
    # Current time as UTC timestamp
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
                RETURNING runner_id, currency_pair,tv_username,tv_password;
                """,
                data
            )
            runner_id, currency_pair ,tv_username,tv_password= cur.fetchone()

        conn.commit()
    
    try:
        global bot_thread
        if getattr(open_browser, "running", False):

            print("Bot has already started.")
            return JSONResponse(content={"status": "400", "message": "Bot has already started."})

        # Start the bot

        # Check the current URL
        else:
            bot_thread = threading.Thread(target=open_browser.run)
            bot_thread.start()
            flag=100000
            i=0
            while flag:
                i+=1
                time.sleep(3)
                driver = open_browser.driver
                current_url = driver.current_url
                print(f"current URL: {current_url}")
                if current_url == "https://www.bydfi.com/en":
                    # push_event(identifier, kind="alive", raw={"message": "Bot started"})
                    flag=0
                    
                                    
                   
                    return {"status": "success"}
                if i==20:
                    i=0
                    print("time reseting")
                    open_browser.stop()
                    time.sleep(5)
                    bot_thread = threading.Thread(target=open_browser.run)
                    bot_thread.start()
        
        
        
   

        
            
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



@app.get("/global_runner")
async def global_page():
   
    # Here we return constant values
    """ get total runner from db"""
    with db.connect() as conn:
        with conn.cursor() as cur:
            total_runners=db.fetch_config_count(cur)
            # print(total_runners)

    """ get total pnl  from db """
    with db.connect() as conn:
        with conn.cursor() as cur:   # Fetch data
            configs = db.fetch_all_configurations(cur) # assign to only one variable
            i=0
            total_profit=0
            for i in range(len(configs)):
                total_profit=total_profit+configs[i]["trade_pnl"]
    
    """ get total balalce from backup table"""
    with db.connect() as conn:
        with conn.cursor() as cur:    # Fetch data
            configs = db.fetch_trade_backup() # assign to only one variable
            i=0
            total_ballacne=0
            # print(configs)
            for i in range(len(configs)):
                total_ballacne=total_ballacne+configs[i]["now_balance"]
            # print(total_ballacne)
                # time.sleep(10)
            # print(configs)  # tüm kayıtları liste halinde göreceksin
            # print(len(configs))  # kaç kayıt geldiğini kontrol et

    #print("total PNL:", total_pnl)

    return {
        "balance": total_ballacne,
        "profit": total_profit,
        "runners": total_runners
    }

#---------------------fe endpoints end-------------------------------------------------------------------------------------------------------------------------------------------------



#---------------------webhook begin-----------------------------

# --------------------------------------
# START / STOP Webhook / configure
# --------------------------------------
first_start_flag = False  # False when the program is first opened

@app.post("/configure")
async def configure(request: Request):
    global first_start_flag

    if not first_start_flag:  # if it has never worked before
        js_configure.reset_json_file("activs.json")
        first_start_flag = True   # never work again
        print("First config arrived, activs.json was reset")
    else:
        print("Next config, no reset")

        
    data = await request.json()
    runner_id = data.get("Runner_id")

    if not runner_id:
        return {"status": "error", "message": "Runner_id didnt found"}

    # Read local JSON
    data_from_local = js_configure.read_data()
    print(data_from_local)
    # Does runner_id already exist?
    exists = any(record[0] == runner_id for record in data_from_local)

    if not exists:
        # Add new record
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

        # write as epoch (Unix time)
        expire_timestamp = int(expire_time.timestamp())

        print("current (epoch):", int(time.time()))
        print("5 minuts later (epoch):", expire_timestamp)


        js_configure.add_record([Runner_id,"",amount,Tr,margin,leverageX,symbol,market_type,Tick_Size,expire_timestamp,"","","",""])#son 4 open price,satın alınan yada satılan coin miktarı (önceki işlemleri toplayarak ilerle),işlemlerdeki kar durumu,kapanış için kalan süre
        
        push_event("configured", kind="dead", raw={"message": "Runner id append in local"})   
        data_from_local = js_configure.read_data()
        print("confiugre data: ",data_from_local)
        return {"status": "ok", "message": "Yeni kayıt eklendi", "record": data}

    else:
        push_event("configured", kind="dead", raw={"message": "Runner id already append in local"})
        return {"status": "success"}

   
""" tv endpoints """
"""
request example in webhook

config_js={"runner_id":209,
    "data": {'identifier': 'JSAqsyMo', 'kind': 'close', 'Recalc': False, 'chart': {'url': 'https://www.tradingview.com/chart/JSAqsyMo/', 'interval': '1m'},
    'trade': {'id': '2184', 'entry_type': 'Entry', 'entry_signal': 'Strong Sell, Strong Buy', 'entry_price': 239.416, 'entry_time': 'Aug 27, 2025, 14:48', 'exit_price': 239.416, 'exit_time': 'Aug 27, 2025, 14:50', 'exit_signal': 'Strong Buy', 'position': '289.98, 365.75 usdt'},
    'raw': {'num': '2184', 'signal': 'Strong Sell, Strong Buy', 'type': 
    'Entry', 'open_time': 'Aug 27, 2025, 14:48', 'close_time': 'Aug 27, 2025, 14:50', 'open_price': '239.416', 'close_price': '239.416', 'position_size': '289.98, 365.75 usdt'}}
}


config=requests.post("http://127.0.0.1:5000/signal", json=config_js)

like that


"""
@app.post("/signal")
async def signal(request: Request):
    {"runner_id":1,"data":{}} #example
    data_raw = await request.json()
    runner_id = data_raw.get("runner_id")
    data=data_raw.get("data")
    # print(runner_id,data)
    market_func.getpayload(data_raw)


    if runner_id==None:
        return {"status": "error", "message": "Runner_id didnt found"}

    elif runner_id !=None:
        return {"status": "success"}







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











# # -----------------------------------------------------------------------------
# #  Endpoints requests
# # -----------------------------------------------------------------------------

# import asyncio

# payload = payload = {
#         "identifier": IDENTIFIER,
#         "chart_url": CHART_URL,
#         "executor_url": f"{BASE_URL}/debug/executor",
#         "refresh_enabled": REFRESH_ENABLED,
#         # NEW: pass creds to backend (None if not present, which keeps old behavior)
#         "tv_username": TV_USER,
#         "tv_password": TV_PASS,
#     }

# # print(await create_chart(payload))

# # 3. check Chart status 
# print(await get_chart_status("JSAqsyMo"))

# # # 4. get trade records
# # print(await get_trades("JSAqsyMo", limit=50))##

# # # 5. Chart delete
# # print(await stop_chart(IDENTIFIER))

# # # print(await open_view(payload))

# # # print(await view_chart(IDENTIFIER))

# # print(await get_closed_events(IDENTIFIER))

# # print(await get_events(IDENTIFIER))

# # await post_debug_executor({"kind": "test_event", "data": {"msg": "hello2"}})
# r=await get_debug_webhooks(clear=True)# debug

# classified_events = filter_open_events(r)










# -------------------------------------------
# Run
# -------------------------------------------
# uvicorn main:app --reload
