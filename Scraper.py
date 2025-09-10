from __future__ import annotations

from seleniumbase import SB
from dotenv import load_dotenv
import os, json
from time import sleep, time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from capsolver.error import InvalidRequestError
import capsolver

load_dotenv()
EMAIL     = os.getenv("EMAIL", "")
PASSWORD  = os.getenv("PASSWORD", "")
capsolver.api_key = os.getenv("CAPSOLVER_API_KEY", "")
CHART_URL = os.getenv("CHART_URL", "https://www.tradingview.com/chart/")

COOKIES_DIR = "saved_cookies"

# -----------------------------------------------------------------------------
# Cookies (per-identifier)
# -----------------------------------------------------------------------------
def cookies_path(identifier: str) -> str:
    os.makedirs(COOKIES_DIR, exist_ok=True)
    safe = identifier.replace("/", "_")
    return os.path.join(COOKIES_DIR, f"{safe}.json")

def save_cookies_json(sb: SB, identifier: str) -> None:
    path = cookies_path(identifier)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sb.driver.get_cookies(), f, indent=2)

def load_cookies_json(sb: SB, identifier: str, url: str) -> bool:
    path = cookies_path(identifier)
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as f:
        cookies = json.load(f)
    sb.open(url)  # Must be on correct domain before adding cookies
    for c in cookies:
        sb.driver.add_cookie(c)
    sb.refresh()
    return True

# -----------------------------------------------------------------------------
# Login helpers
# -----------------------------------------------------------------------------
def get_site_key(sb: SB):
    if sb.is_element_visible("div.g-recaptcha"):
        return sb.get_attribute("div.g-recaptcha", "data-sitekey")
    iframe_src = sb.get_attribute('iframe[title="reCAPTCHA"]', "src")
    return iframe_src.split("k=")[1].split("&")[0]

def solve_recaptcha(sb: SB):
    site_key = get_site_key(sb)
    url      = sb.get_current_url()
    for task in ("ReCaptchaV2TaskProxyLess", "ReCaptchaV2EnterpriseTaskProxyLess"):
        try:
            token = capsolver.solve({
                "type": task,
                "websiteURL": url,
                "websiteKey": site_key,
            })["gRecaptchaResponse"]
            sb.execute_script(
                "const a=document.getElementById('g-recaptcha-response');"
                "if(a){a.style.display='block';a.value=arguments[0];}", token)
            sb.click("button:contains('Sign in')")
            sb.sleep(3)
            return
        except InvalidRequestError as e:
            if "unsupported captcha type" in str(e).lower():
                continue
            raise RuntimeError(e)
    raise RuntimeError("CapSolver could not solve the CAPTCHA")

def login(sb: SB, username: str | None = None, password: str | None = None):
    """Perform email login flow on TradingView home."""
    user = username if username is not None else EMAIL
    pwd  = password if password is not None else PASSWORD

    sb.open("https://www.tradingview.com/")
    sb.wait(1)
    anon = ("button.tv-header__user-menu-button."
            "tv-header__user-menu-button--anonymous."
            "js-header-user-menu-button")
    sb.wait_for_element_visible(anon); sb.click(anon); sb.sleep(1)

    drop = ("#overlap-manager-root > div:nth-child(2) > span > "
            "div.menuWrap-Kq3ruQo8 > div > div > div > button:nth-child(1)")
    sb.wait_for_element_visible(drop); sb.click(drop); sb.sleep(1)

    if not sb.is_element_visible("#id_username"):
        email_btn = ("body > div:nth-child(14) div.dialog-qyCw0PaN "
                     "div.container-U88gE00K div.wrapper-U88gE00K "
                     "> div > div > button")
        if sb.is_element_visible(email_btn):
            sb.click(email_btn); sb.sleep(1)
        else:
            for b in sb.find_elements("body div.dialog-qyCw0PaN button"):
                if "email" in b.text.lower(): b.click(); sb.sleep(1); break

    sb.type("#id_username", user)
    sb.type("#id_password", pwd)

    submit = ("body > div:nth-child(14) div.dialog-qyCw0PaN "
              "div.container-U88gE00K div.wrapper-U88gE00K "
              "> div > div > form > button")
    if sb.is_element_visible(submit):
        sb.click(submit)
    else:
        sb.click("button:contains('Sign in')")
    sb.sleep(2)

    if sb.is_element_visible('iframe[title="reCAPTCHA"]'):
        solve_recaptcha(sb)

    logged = ("button.tv-header__user-menu-button:"
              "not(.tv-header__user-menu-button--anonymous)")
    sb.wait_for_element_visible(logged, timeout=15)

def verifyIfLoggedIn(sb: SB) -> bool:
    """
    Decide quickly whether the Strategy Tester panel is active (thus logged).
    If the footer tester button says 'Open Strategy Tester', click it first.
    Then read the title: if it's 'Strategy Tester' (pane title only) => not logged.
    Otherwise assume logged.
    """
    tester_btn = ("#footer-chart-panel > div.tabbar-n3UmcVi3 > div:nth-child(1) > "
                  "div:nth-child(1) > button")
    label = sb.get_attribute(tester_btn, "aria-label") or ""
    if "Open Strategy Tester" in label:
        sb.click(tester_btn)
        sb.sleep(0.4)

    title = "#bottom-area > div.bottom-widgetbar-content.backtesting > div > div > div > div > div > strong"
    try:
        text = (sb.get_text(title) or "").strip()
        if text == "Strategy Tester":
            return False
        return True
    except Exception:
        return True

# -----------------------------------------------------------------------------
# Scraper (live only)
# -----------------------------------------------------------------------------
def _safe_text(el):
    try:
        return (el.text or "").strip()
    except Exception:
        return ""

def _q(el, css):
    try: return el.find_element(By.CSS_SELECTOR, css)
    except Exception: return None

def _qq(el, css):
    try: return el.find_elements(By.CSS_SELECTOR, css)
    except Exception: return []

# ────────── DEBUG FLAG ──────────
DEBUG_SCRAPER = True
def _dbg(msg: str):
    if DEBUG_SCRAPER:
        print(msg)

# ───────── Module-level helpers shared by both scraper functions ─────────
import re
_DT  = re.compile(r"\b\w{3}\s+\d{2},\s+\d{4},\s+\d{2}:\d{2}\b")  # Aug 10, 2025, 06:15
_PRC = re.compile(r"^\d+(?:\.\d+)?\s+USDT$")                     # 1.9299 USDT

def _clean_num(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())

# --- NEW: normalize TradingView thin spaces & enforce spacing before K/M/B ---
def _normalize_space(s: str) -> str:
    if not s:
        return ""
    # Replace narrow no-break & NBSP with normal spaces, then collapse
    s = s.replace("\u202f", " ").replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    # Ensure a normal space between number and suffix (K/M/B) if missing
    s = re.sub(r"(?<=\d)([KMB])\b", r" \1", s, flags=re.IGNORECASE)
    return s

def _format_position(v1: str, v2: str) -> str:
    v1n = _normalize_space(v1)
    v2n = _normalize_space(v2)
    if not v1n and not v2n:
        return ""
    # Append " usdt" to the second part per requirement (lowercase)
    if v2n:
        v2n = f"{v2n} usdt"
    # Combine with comma like the rest of the fields
    if v1n and v2n:
        return f"{v1n}, {v2n}"
    return v1n or v2n

def _parse_cells(tds):
    """
    Extract all fields from a <tr>.
    Returns: (num, signal, dt_open, dt_close, price_open, price_close, typ_entry, position_size)

    Contract:
      • signal  = "<entry_signal>, <exit_or_open>"
      • dt_open = nth-child(2) of the Date/Time cell
      • dt_close= nth-child(1) of the Date/Time cell ('' when still open)
      • typ_entry = nth-child(2) of the Type cell ("Entry")
    """
    num = _clean_num(_safe_text(tds[0]))

    # Type: keep the entry row label only
    typ_entry = _safe_text(_q(tds[2], "div > div:nth-child(2)")) or "Entry"

    # --- Primary mapping (current UI): [3]=Date/Time, [4]=Signal -------------
    dt_open  = _safe_text(_q(tds[3], "div > div:nth-child(2)"))
    dt_close = _safe_text(_q(tds[3], "div > div:nth-child(1)"))

    sig_entry = _safe_text(_q(tds[4], "div > div:nth-child(2)"))
    sig_exit  = (_safe_text(_q(tds[4], "div > div:nth-child(1) > div"))
                 or _safe_text(_q(tds[4], "div > div:nth-child(1)")))

    # --- Fallback (older UI): [3]=Signal, [4]=Date/Time ----------------------
    if _DT.fullmatch(sig_entry or "") and not _DT.fullmatch(dt_open or ""):
        dt_open  = _safe_text(_q(tds[4], "div > div:nth-child(2)"))
        dt_close = _safe_text(_q(tds[4], "div > div:nth-child(1)"))
        sig_entry = _safe_text(_q(tds[3], "div > div:nth-child(2)"))
        sig_exit  = (_safe_text(_q(tds[3], "div > div:nth-child(1) > div"))
                     or _safe_text(_q(tds[3], "div > div:nth-child(1)")))

    # Build the combined signal with de-duplication
    parts = [p for p in (sig_entry, sig_exit) if p]
    signal = ", ".join(dict.fromkeys(parts))  # e.g., "Strong Buy, Open"

    # Prices
    price_open  = _safe_text(_q(tds[5], "div > div:nth-child(2) div.value-SLJfw5le"))
    price_close = _safe_text(_q(tds[5], "div > div:nth-child(1) div.value-SLJfw5le"))

    # --- NEW: Position size (two lines in the same cell) ---------------------
    # td index 6 (7th column)
    pos1 = _safe_text(_q(tds[6], "div > div:nth-child(1)"))
    pos2 = _safe_text(_q(tds[6], "div > div:nth-child(2) > span:nth-child(1)"))
    position_size = _format_position(pos1, pos2)

    return num, signal, dt_open, dt_close, price_open, price_close, typ_entry, position_size


# ──────────────────────────────────────────────────────────────────────────────
# 1️⃣  LIVE stream of trades  ─ scrapeListOfTrades()
# ──────────────────────────────────────────────────────────────────────────────
def scrapeListOfTrades(sb: SB,
                       poll_interval: float = 0.25,
                       deep_scan_every: float = 5.0,
                       status_every: float = 10.0):

    tester_btn = "#footer-chart-panel div.tabbar-n3UmcVi3 button:nth-child(1)"
    if "Open Strategy Tester" in (sb.get_attribute(tester_btn, "aria-label") or ""):
        sb.click(tester_btn); sb.sleep(0.3)

    for sel in ("#List\\ of\\ Trades", "#List\\ of\\ Trades > span"):
        if sb.is_element_visible(sel):
            sb.click(sel); sb.sleep(0.3); break

    table   = "#bottom-area div.bottom-widgetbar-content.backtesting table"
    wrapper = "#bottom-area div.wrapper-UQYV_qXv > div > div"
    sb.wait_for_element_visible(table, timeout=15)
    sb.execute_script("arguments[0].scrollTop = 0;", sb.find_element(wrapper))

    last_status: dict[str, str] = {}
    open_rows:   dict[str, dict] = {}
    last_deep = last_stat = time()

    def _rows_from(trs):
        for tr in trs:
            try:
                tds = _qq(tr, "td")
                if len(tds) < 7:  # position column included
                    continue
                num, sig, dt_o, dt_c, p_o, p_c, typ, pos = _parse_cells(tds)
                if not num or not sig:
                    continue
                yield {
                    "num": num,
                    "signal": sig,         # "<entry_signal>, <exit_or_open>"
                    "type": typ,           # "Entry"
                    "open_time": dt_o,
                    "close_time": dt_c,
                    "open_price": p_o,
                    "close_price": p_c,
                    "position_size": pos,  # NEW (normalized)
                }
            except StaleElementReferenceException:
                continue

    while True:
        now = time()

        # Quick-scan visible rows
        for row in _rows_from(sb.find_elements(f"{table} > tbody > tr")[:30]):
            num    = row["num"]
            status = row["signal"].split(",")[-1].strip()  # "Open" or exit signal
            if last_status.get(num) == status:
                continue
            last_status[num] = status
            if status == "Open":
                open_rows[num] = row
            else:
                open_rows.pop(num, None)
            yield row  # trade event

        # Deep-scan open rows that scrolled off-screen
        if open_rows and now - last_deep >= deep_scan_every:
            last_deep = now
            for num in list(open_rows):
                tr = sb.execute_script(
                    "return [...document.querySelectorAll('table tbody tr')]"
                    ".find(r=>r.innerText.startsWith(arguments[0]))", num)
                if not tr:
                    continue
                for row in _rows_from([tr]):
                    status = row["signal"].split(",")[-1].strip()
                    if last_status.get(num) == status:
                        continue
                    last_status[num] = status
                    if status == "Open":
                        open_rows[num] = row
                    else:
                        open_rows.pop(num, None)
                    yield row  # trade event

        # Heartbeat for console + scheduler tick for the worker
        if now - last_stat >= status_every:
            last_stat = now
            print(f"open={len(open_rows):3d} | unique_seen={len(last_status)}")

        # ALWAYS provide a scheduler tick so the worker can check refresh timing
        yield {"__tick__": True, "ts": now}

        sleep(poll_interval)

# ──────────────────────────────────────────────────────────────────────────────
# 2️⃣  One-shot scan  ─ scan_all_trades_once()
# ──────────────────────────────────────────────────────────────────────────────
def scan_all_trades_once(sb: SB, max_rows: int = 1000) -> list[dict]:
    for sel in ("#List\\ of\\ Trades", "#List\\ of\\ Trades > span"):
        if sb.is_element_visible(sel):
            sb.click(sel); sb.sleep(0.2); break

    table = "#bottom-area div.bottom-widgetbar-content.backtesting table"
    sb.wait_for_element_visible(table, timeout=15)

    rows: list[dict] = []
    for tr in sb.find_elements(f"{table} > tbody > tr")[:max_rows]:
        tds = tr.find_elements(By.CSS_SELECTOR, "td")
        if len(tds) < 7:
            continue
        num, sig, dt_o, dt_c, p_o, p_c, typ, pos = _parse_cells(tds)
        if not num or not sig:
            continue
        rows.append({
            "num": num,
            "signal": sig,      # "<entry_signal>, <exit_or_open>"
            "type": typ,        # "Entry"
            "open_time": dt_o,
            "close_time": dt_c,
            "open_price": p_o,
            "close_price": p_c,
            "position_size": pos,  # NEW (normalized)
        })
    return rows


# -----------------------------------------------------------------------------
# Timeframe parsing and mapping
# -----------------------------------------------------------------------------
def _read_interval_raw(sb: SB) -> str:
    candidates = [
        "#header-toolbar-intervals > button > div > div",
        "#header-toolbar-intervals button div div",
        "#header-toolbar-intervals button",
    ]
    for sel in candidates:
        if sb.is_element_visible(sel):
            txt = (sb.get_text(sel) or "").strip().replace(" ", "")
            if txt:
                return txt
    js = (
        "const el=document.querySelector('#header-toolbar-intervals button');"
        "return el? el.innerText.replace(/\\s+/g,'') : '';"
    )
    try:
        val = sb.execute_script(js) or ""
        return str(val).strip()
    except Exception:
        return ""

def parse_interval_to_seconds(compact: str) -> tuple[str, int]:
    if not compact:
        return "1m", 60
    s = compact.lower()
    if s.isdigit():
        n = int(s)
        if n <= 0:
            return "1m", 60
        return f"{n}m", n * 60
    num = ""
    unit = ""
    for ch in s:
        if ch.isdigit():
            num += ch
        else:
            unit += ch
    if not num:
        return "1m", 60
    n = max(1, int(num))
    if unit in ("s",):
        return f"{n}s", n
    if unit in ("m",):
        return f"{n}m", n * 60
    if unit in ("h",):
        return f"{n}h", n * 3600
    if unit in ("d",):
        return f"{n}d", n * 86400
    if unit in ("w",):
        return f"{n}w", n * 7 * 86400
    if unit in ("mo", "month", "mo."):
        return f"{n}mo", n * 30 * 86400
    return f"{n}m", n * 60

def get_interval(sb: SB) -> tuple[str, int]:
    raw = _read_interval_raw(sb)
    return parse_interval_to_seconds(raw)
