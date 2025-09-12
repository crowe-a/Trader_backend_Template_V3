import asyncio
import httpx,os,json
from datetime import datetime

BASE_URL = "http://localhost:8000"  # kendi FastAPI sunucunun adresi
BASE_URL   = "http://127.0.0.1:8000"
IDENTIFIER = "JSAqsyMo"
CHART_URL  = "https://www.tradingview.com/chart/JSAqsyMo/"
LISTEN_SECS = 1500
REFRESH_ENABLED = True  # toggle to verify both modes
TV_USER = os.getenv("EMAIL") or None
TV_PASS = os.getenv("PASSWORD") or None


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def classify_events(response: dict):
    """
    response: await get_debug_webhooks(clear=True) çıktısı
    return: dict with classified events
    """
    classified = {"alive": [], "open": [], "close": [], "dead": [], "other": []}

    events = response.get("events", [])
    for evt in events:
        if not isinstance(evt, dict):
            # Eğer bir string geldiyse, JSON'a çevir
            try:
                evt = json.loads(evt)
            except Exception:
                classified["other"].append(evt)
                continue

        kind = evt.get("kind")
        if kind in classified:
            classified[kind].append(evt)
        else:
            classified["other"].append(evt)

    return classified

def filter_open_events(response: dict):
    """
    response: await get_debug_webhooks(clear=True) çıktısı
    return: sadece 'close' kind'li eventlerin listesi
    """
    open_events = []

    events = response.get("events", [])
    for evt in events:
        if not isinstance(evt, dict):
            # if it string convert json
            try:
                evt = json.loads(evt)
            except Exception:
                continue  # delete is not json

        if evt.get("kind") == "open":
            open_events.append(evt)

    return open_events
# --- Charts list ---
async def list_charts():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/charts")
        return r.json()

# --- Chart Status ---
async def get_chart_status(identifier: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/charts/{identifier}/status")
        return r.json()

# --- Chart creator ---
async def create_chart(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/charts", json=payload)
        return r.json()

# --- Chart delete ---
async def stop_chart(identifier: str):
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{BASE_URL}/charts/{identifier}")
        return r.json()

# --- Chart Events (for one-time shooting without SSE) ---
async def get_events(identifier: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/charts/{identifier}/events")
        return r.text  # Since it is an SSE stream, text will be returned.

async def get_closed_events(identifier: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/charts/{identifier}/closed/events")
        return r.text

# --- Trades ---
async def get_trades(identifier: str, limit: int = 200):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/charts/{identifier}/trades", params={"limit": limit})
        return r.json()

# --- Viewer ---
async def open_view(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/view", json=payload)
        return r.json()

async def view_chart(identifier: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/charts/{identifier}/view")
        return r.json()
    


async def post_debug_executor(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/debug/executor", json=payload)
        print(f"POST /debug/executor -> {r.status_code}, {r.json()}")
        return r.json()

async def get_debug_webhooks(clear: bool = False):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/debug/executor", params={"clear": clear})
        print(f"GET /debug/executor -> {r.status_code}, {r.json()}")

       
        return r.json()

async def login(username: str, password: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/login", json={"username": username, "password": password})
        print(f"POST /login -> {r.status_code}, {r.json()}")
        return r.json()
    
async def main():
    # 1. List running charts
    print(await list_charts())
    print(f"[{ts()}] Test start")
    print(f"[cfg] base={BASE_URL}")
    print(f"[cfg] identifier={IDENTIFIER}")
    print(f"[cfg] chart_url={CHART_URL}")
    print(f"[cfg] listen_seconds={LISTEN_SECS}")
    print(f"[cfg] refresh_enabled={REFRESH_ENABLED}")
    print(f"[cfg] tv_username={'<set>' if TV_USER else '<env EMAIL missing>'}")


   
    # 2. Creating a new chart
    payload = payload = {
            "identifier": IDENTIFIER,
            "chart_url": CHART_URL,
            "executor_url": f"{BASE_URL}/debug/executor",
            "refresh_enabled": REFRESH_ENABLED,
            # NEW: pass creds to backend (None if not present, which keeps old behavior)
            "tv_username": TV_USER,
            "tv_password": TV_PASS,
        }
    
    # print(await create_chart(payload))

    # 3. Check the chart status
    print(await get_chart_status("JSAqsyMo"))

    # # 4. get all trades
    # print(await get_trades("JSAqsyMo", limit=50))##

    # # 5. Chart delete
    # print(await stop_chart(IDENTIFIER))

    # # print(await open_view(payload))

    # # print(await view_chart(IDENTIFIER))

    # print(await get_closed_events(IDENTIFIER))

    # print(await get_events(IDENTIFIER))

    # await post_debug_executor({"kind": "test_event", "data": {"msg": "hello2"}})
    # r=await get_debug_webhooks(clear=True)# debug
 
    # classified_events = filter_open_events(r)
    # print(classified_events)
    # print(f"Alive events: {len(classified_events['alive'])}")
    # print(f"Open events: {len(classified_events['open'])}")
    # print(f"Dead events: {len(classified_events['dead'])}")
    # print(f"Other events: {len(classified_events['other'])}")
    # await login("admin", "secret123")
    # await login("admin", "wrong")


