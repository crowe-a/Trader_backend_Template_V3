# test_system.py  (hard-coded configuration)
import asyncio,requests,time
import json
import os
from datetime import datetime

from dotenv import load_dotenv
import httpx

load_dotenv()

BASE_URL   = "http://127.0.0.1:8000"
IDENTIFIER = None
CHART_URL  = "https://www.tradingview.com/chart/JSAqsyMo/"
LISTEN_SECS = 1500
REFRESH_ENABLED = True  # toggle to verify both modes


config_js={
            "action": "configure",
            "Runner_id":"1",

            
            "amount": "1000",
            "Tr":"0.2" , 
            "margin":"cross",
            "leverage":"10",
            "symbol": "beamx_usdt",
            "market_type": "Limit",
            
            "Tick_Size":"10" , 
            "order_expiry":"5"
            
              }


# config=requests.post("http://127.0.0.1:8000/configure", json=config_js)
# flag1=100
# while flag1:
#     time.sleep(1)
#     print(config.status_code)
#     print(config.json())
#     if config.status_code==200:
#         flag1=1
#         break
#     if config.status_code==400:
#         flag1=0


# r=requests.post("http://127.0.0.1:8000/start_stop", json={"action": "start",})
# flag=100
# while flag:
#     time.sleep(1)
#     print(r.status_code)  # 200
#     print(r.json())  
#     if r.status_code==200:
#         flag=1
#         break
#     if r.status_code==400:
#         flag=0


time.sleep(1)

# Pull test TV creds from .env to pass through the /charts payload
TV_USER = os.getenv("EMAIL") or None
TV_PASS = os.getenv("PASSWORD") or None

def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")

REQUIRED_OPEN_KEYS  = {"id", "entry_type", "entry_signal", "entry_price", "entry_time"}
REQUIRED_CLOSE_KEYS = REQUIRED_OPEN_KEYS | {"exit_price", "exit_time"}

async def sse_collect(client: httpx.AsyncClient, path: str, seconds: int):
    url = f"{BASE_URL}{path}"
    deadline = asyncio.get_event_loop().time() + seconds
    events = []
    async with client.stream("GET", url, timeout=None) as resp:
        if resp.status_code != 200:
            print(f"[{ts()}] SSE {path} status {resp.status_code}")
            return events
        buf = []
        async for line in resp.aiter_lines():
            if asyncio.get_event_loop().time() >= deadline:
                break
            if line is None:
                continue
            if line == "":
                if not buf:
                    continue
                data_lines = [ln[5:].lstrip() for ln in buf if ln.startswith("data:")]
                buf.clear()
                if not data_lines:
                    continue
                payload = "\n".join(data_lines)
                try:
                    evt = json.loads(payload)
                except Exception:
                    print(f"[{ts()}] SSE parse error")
                    continue
                if "data" in evt and isinstance(evt["data"], dict):
                    evt = evt["data"]
                events.append(evt)
            else:
                buf.append(line)
    return events

def validate_open_payload(evt: dict) -> bool:
    if evt.get("kind") != "open":
        return False
    trade = evt.get("trade", {})
    missing = REQUIRED_OPEN_KEYS - set(trade.keys())
    if missing:
        print(f"[{ts()}] Open payload missing keys: {sorted(missing)}")
        return False
    return True

def validate_close_payload(evt: dict) -> bool:
    if evt.get("kind") != "close":
        return False
    trade = evt.get("trade", {})
    missing = REQUIRED_CLOSE_KEYS - set(trade.keys())
    if missing:
        print(f"[{ts()}] Close payload missing keys: {sorted(missing)}")
        return False
    return True

def validate_alive_payload(evt: dict) -> bool:
    return evt.get("kind") == "alive" and "activated_at" in evt and "chart" in evt

def validate_dead_payload(evt: dict) -> bool:
    return evt.get("kind") == "dead" and "stopped_at" in evt and "chart" in evt

async def main():
    global IDENTIFIER
    print(f"[{ts()}] Test start")
    print(f"[cfg] base={BASE_URL}")
    print(f"[cfg] identifier={IDENTIFIER}")
    print(f"[cfg] chart_url={CHART_URL}")
    print(f"[cfg] listen_seconds={LISTEN_SECS}")
    print(f"[cfg] refresh_enabled={REFRESH_ENABLED}")
    print(f"[cfg] tv_username={'<set>' if TV_USER else '<env EMAIL missing>'}")

    timeout = httpx.Timeout(connect=60.0, read=60.0, write=30.0, pool=None)
    async with httpx.AsyncClient(http2=False, timeout=timeout) as client:
        payload = {
            "identifier": IDENTIFIER,
            "chart_url": CHART_URL,
            "executor_url": f"{BASE_URL}/debug/executor",
            "refresh_enabled": REFRESH_ENABLED,
            # NEW: pass creds to backend (None if not present, which keeps old behavior)
            "tv_username": TV_USER,
            "tv_password": TV_PASS,
        }
        print(f"[{ts()}] POST /charts")
        r = await client.post(f"{BASE_URL}/charts", json=payload)
        print(f"[{ts()}] Start status {r.status_code}")
        if r.status_code not in (200, 201):
            print(f"[{ts()}] Aborting; cannot start runner")
            return

        await asyncio.sleep(5)

        status = await client.get(f"{BASE_URL}/charts/{IDENTIFIER}/status")
        print(f"[{ts()}] Status {status.status_code} {status.text}")

        print(f"[{ts()}] Listening for events")
        all_events_task    = asyncio.create_task(sse_collect(client, f"/charts/{IDENTIFIER}/events", LISTEN_SECS))
        closed_events_task = asyncio.create_task(sse_collect(client, f"/charts/{IDENTIFIER}/closed/events", LISTEN_SECS))
        all_events   = await all_events_task
        closed_only  = await closed_events_task

        opens  = [e for e in all_events if e.get("kind") == "open"]
        closes = [e for e in all_events if e.get("kind") == "close"]
        alive  = [e for e in all_events if e.get("kind") == "alive"]
        dead   = [e for e in all_events if e.get("kind") == "dead"]

        print(f"[{ts()}] Event counts: all={len(all_events)} opens={len(opens)} closes={len(closes)} alive={len(alive)} dead={len(dead)}")
        print(f"[{ts()}] Closed stream count={len(closed_only)}")

        if alive:
            if validate_alive_payload(alive[0]):
                print(f"[{ts()}] Alive payload OK")
            else:
                print(f"[{ts()}] Alive payload invalid")
        else:
            print(f"[{ts()}] No alive payload received")

        for e in opens:
            if validate_open_payload(e):
                print(f"[{ts()}] Open payload OK id={e.get('trade', {}).get('id')} recalc={e.get('Recalc')}")
            else:
                print(f"[{ts()}] Open payload invalid")

        for e in closes:
            if validate_close_payload(e):
                print(f"[{ts()}] Close payload OK id={e.get('trade', {}).get('id')} recalc={e.get('Recalc')}")
            else:
                print(f"[{ts()}] Close payload invalid")

        r = await client.get(f"{BASE_URL}/debug/executor")
        if r.status_code == 200:
            data = r.json()
            print(f"[{ts()}] Webhook events count={data.get('count')}")
        else:
            print(f"[{ts()}] Webhook buffer status {r.status_code}")

        r = await client.delete(f"{BASE_URL}/charts/{IDENTIFIER}")
        print(f"[{ts()}] Stop status {r.status_code}")

        await asyncio.sleep(3)

        r = await client.get(f"{BASE_URL}/debug/executor")
        if r.status_code == 200:
            data = r.json()
            kinds = [e.get("kind") for e in data.get("events", [])]
            dead_count = kinds.count("dead")
            print(f"[{ts()}] Dead notifications in buffer={dead_count}")
        else:
            print(f"[{ts()}] Webhook buffer status {r.status_code}")

        # ---- Login endpoint checks (both true & false cases) ----
        print(f"[{ts()}] POST /login (true creds)")
        r = await client.post(f"{BASE_URL}/login", json={"username": "admin", "password": "secret123"})
        try:
            print(f"[{ts()}] Login true -> {r.json()}")
        except Exception:
            print(f"[{ts()}] Login true -> status {r.status_code}")

        print(f"[{ts()}] POST /login (false creds)")
        r = await client.post(f"{BASE_URL}/login", json={"username": "admin", "password": "wrong"})
        try:
            print(f"[{ts()}] Login false -> {r.json()}")
        except Exception:
            print(f"[{ts()}] Login false -> status {r.status_code}")

    print(f"[{ts()}] Test end")

# if __name__ == "__main__":
#     # Run server separately with:
#     #   VIEW_NONBLOCK=1 uvicorn api:app --reload
#     asyncio.run(main())
