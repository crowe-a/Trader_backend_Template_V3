from __future__ import annotations

import logging, os, threading, psycopg2, requests
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from backend import market_func
from Scraper import (
    SB, load_cookies_json, save_cookies_json,
    verifyIfLoggedIn, login, scrapeListOfTrades,
    get_interval, scan_all_trades_once,
)

log = logging.getLogger(__name__)

LOCAL_TZ = datetime.now().astimezone().tzinfo

DB_DSN = (
    f"host={os.getenv('DB_HOST','localhost')} "
    f"port={os.getenv('DB_PORT','5432')} "
    f"dbname={os.getenv('DB_NAME','nextlayer')} "
    f"user={os.getenv('DB_USER','nl_user')} "
    f"password={os.getenv('DB_PASS','nlpass')}"
)

# >>> UPDATED: include 'position' in the UPSERT <<<
UPSERT_SQL = """
INSERT INTO trades
(identifier, opened_at, closed_at, type, signal, open_price, close_price, position)
VALUES (%(identifier)s,%(opened)s,%(closed)s,%(type)s,%(signal)s,%(open_price)s,%(close_price)s,%(position)s)
ON CONFLICT (identifier, opened_at)
DO UPDATE SET
  closed_at    = EXCLUDED.closed_at,
  type         = EXCLUDED.type,
  signal       = EXCLUDED.signal,
  -- IMPORTANT: keep the first open price we ever stored
  close_price  = EXCLUDED.close_price,
  position     = EXCLUDED.position;
"""


def parse_tv_dt(s: str) -> datetime | None:
    if not s:
        return None
    return datetime.strptime(s, "%b %d, %Y, %H:%M").replace(tzinfo=LOCAL_TZ)

def _to_float(v: Optional[str]) -> Optional[float]:
    if not v:
        return None
    try:
        return float(v.replace(",", ""))
    except Exception:
        return None

def _epoch_seconds(dt: datetime) -> int:
    return int(dt.timestamp())

def _aligned_midpoint(now: datetime, interval_seconds: int) -> datetime:
    """
    Midpoint of the current candle if safely before it; otherwise next candle midpoint.
    A 1-second guard is applied to avoid refreshing at the boundary.
    """
    if interval_seconds <= 0:
        interval_seconds = 60
    guard = 1
    now_epoch = _epoch_seconds(now)
    base = (now_epoch // interval_seconds) * interval_seconds
    mid = base + interval_seconds // 2
    if now_epoch <= mid - guard:
        when = mid
    else:
        when = base + interval_seconds + interval_seconds // 2
    return datetime.fromtimestamp(when, tz=now.tzinfo)

def _exit_signal_from_raw(raw: dict) -> Optional[str]:
    """
    Extract the exit signal from the combined signal text.
    For example:
      'Strong Buy, Open'                 -> None (still open)
      'Strong Buy, Strong Sell'          -> 'Strong Sell'
      'Strong Sell, Strong Buy'          -> 'Strong Buy'
    """
    sig = (raw.get("signal") or "").strip()
    if not sig:
        return None
    parts = [p.strip() for p in sig.split(",") if p.strip()]
    if not parts:
        return None
    if parts[-1].lower() == "open":
        return None
    return parts[-1]

# --- direction parsing helper (first segment before comma) ---
def _direction_from_raw_signal(raw: dict) -> Optional[str]:
    """
    Return 'buy' or 'sell' if the first segment of the signal contains those words,
    otherwise None. We only use this for OPEN events.
    """
    first = ((raw.get("signal") or "").split(",")[0] or "").strip().lower()
    if "buy" in first:
        return "buy"
    if "sell" in first:
        return "sell"
    return None

# >>> UPDATED: include 'position' in the OPEN payload <<<
def _payload_open(identifier: str, chart_url: str, interval_str: str, entry: dict, raw: dict, recalc: bool) -> dict:
    return {
        "identifier": identifier,
        "kind": "open",
        "Recalc": bool(recalc),  # Only opens can be True
        "chart": {"url": chart_url, "interval": interval_str},
        "trade": {
            "id": entry.get("id"),
            "entry_type": entry.get("entry_type"),
            "entry_signal": entry.get("entry_signal"),
            "entry_price": entry.get("entry_price"),
            "entry_time": entry.get("entry_time"),
            "position": entry.get("position_size") or raw.get("position_size"),
        },
        "raw": raw,
    }

# >>> UPDATED: include 'position' in the CLOSE payload <<<
def _payload_close(identifier: str, chart_url: str, interval_str: str, entry: dict, raw: dict) -> dict:
    return {
        "identifier": identifier,
        "kind": "close",
        "Recalc": False,  # Always False for closes (single-owner flip policy)
        "chart": {"url": chart_url, "interval": interval_str},
        "trade": {
            "id": entry.get("id"),
            "entry_type": entry.get("entry_type"),
            "entry_signal": entry.get("entry_signal"),
            "entry_price": entry.get("entry_price"),
            "entry_time": entry.get("entry_time"),
            "exit_price": _to_float(raw.get("close_price")),
            "exit_time": raw.get("close_time"),
            "exit_signal": _exit_signal_from_raw(raw),
            "position": raw.get("position_size"),
        },
        "raw": raw,
    }

def _payload_alive(identifier: str, chart_url: str, interval_str: str, activated_at: datetime) -> dict:
    return {
        "identifier": identifier,
        "kind": "alive",
        "chart": {"url": chart_url, "interval": interval_str},
        "activated_at": activated_at.isoformat(),
    }

def _payload_dead(identifier: str, chart_url: str, interval_str: str, stopped_at: datetime) -> dict:
    return {
        "identifier": identifier,
        "kind": "dead",
        "chart": {"url": chart_url, "interval": interval_str},
        "stopped_at": stopped_at.isoformat(),
    }

class ChartThread(threading.Thread):
    def __init__(
        self,
        identifier: str,
        chart_url: str,
        publish: Callable[[dict], None],
        executor_url: Optional[str] = None,
        poll_interval: float = 0.25,
        deep_scan_every: float = 5.0,
        status_every: float = 10.0,
        refresh_enabled: bool = False,
        # per-request TV creds (already present)
        tv_username: Optional[str] = None,
        tv_password: Optional[str] = None,
    ):
        super().__init__(daemon=True, name=f"Chart[{identifier}]")
        self.identifier = identifier
        self.chart_url  = chart_url
        self.publish    = publish
        self.executor_url = executor_url

        self.poll_interval   = poll_interval
        self.deep_scan_every = deep_scan_every
        self.status_every    = status_every
        self.refresh_enabled = refresh_enabled

        self._stop = threading.Event()
        self._ann_open:  set[str] = set()
        self._ann_close: set[str] = set()
        self._persisted_close: set[str] = set()

        self.opens_seen  = 0
        self.closes_seen = 0
        self.last_event_ts: datetime | None = None

        self._posted_alive = False
        self._posted_dead  = False

        self.interval_str: str = "1m"
        self.interval_seconds: int = 60
        self.next_refresh_at: Optional[datetime] = None

        self._historical_closed: set[str] = set()
        self._entry_info: Dict[str, Dict[str, Any]] = {}

        # track current direction from the latest OPEN trade
        self._current_direction: Optional[str] = None  # 'buy' | 'sell' | None

        # per-request creds for TradingView
        self.tv_username = tv_username
        self.tv_password = tv_password

    def stop(self):
        self._stop.set()

    # >>> UPDATED: pass 'position' to the UPSERT <<<
    @staticmethod
    def _upsert(cur, evt: dict, identifier: str, entry_price: Optional[float] = None):
        cur.execute(
            UPSERT_SQL,
            dict(
                identifier  = identifier,
                opened      = parse_tv_dt(evt.get("open_time")),
                closed      = parse_tv_dt(evt.get("close_time")),
                type        = evt.get("type"),
                signal      = evt.get("signal"),
                # Prefer the snapshot taken when the trade opened
                open_price  = entry_price if entry_price is not None else _to_float(evt.get("open_price")),
                close_price = _to_float(evt.get("close_price")),
                position    = evt.get("position") or evt.get("position_size"),
            ),
        )

    def _post_webhook(self, payload: dict, logger):
        if not self.executor_url:
            return
        try:

            try:
                #  
                market_func.getpayload(payload)
                
                # #print("payload:",payload)
            except Exception as e:
                log.warning("%s payload sending failed: %s", self.name, e)
                
            logger.info("executor payload: %s", payload)
            requests.post(self.executor_url, json=payload, timeout=2.5)
        except Exception as e:
            log.warning("%s webhook failed: %s", self.name, e)

    def _refresh_schedule(self, sb: SB, now: datetime):
        if not self.refresh_enabled:
            self.next_refresh_at = None
            return
        s, sec = get_interval(sb)
        if not s:
            s, sec = "1m", 60
        self.interval_str = s
        self.interval_seconds = max(1, sec)
        self.next_refresh_at = _aligned_midpoint(now, self.interval_seconds)

    # >>> UPDATED: snapshot 'position' on entry <<<
    def _entry_from_row(self, raw: dict) -> dict:
        return {
            "id": raw.get("num"),
            "entry_type": raw.get("type"),
            "entry_signal": raw.get("signal"),
            "entry_price": _to_float(raw.get("open_price")),
            "entry_time": raw.get("open_time"),
            "position": raw.get("position_size"),
        }

    def _store_entry_if_absent(self, raw: dict):
        num = raw.get("num")
        if num not in self._entry_info:
            self._entry_info[num] = self._entry_from_row(raw)

    def _baseline_after_activation(self, sb: SB, logger, cur, conn):
        """
        Baseline: emit OPEN for trades currently open, ignore already-closed.
        """
        rows = scan_all_trades_once(sb)
        for raw in rows:
            num = raw.get("num")
            sig_last = (raw.get("signal") or "").split(", ")[-1]
            if sig_last == "Open":
                if num not in self._ann_open:
                    self._store_entry_if_absent(raw)
                    entry = self._entry_info[num]
                    # Determine recalc for OPENs only
                    new_dir = _direction_from_raw_signal(raw)
                    recalc = False
                    if new_dir is not None:
                        recalc = (self._current_direction != new_dir)
                        self._current_direction = new_dir
                    self._ann_open.add(num)
                    self.opens_seen += 1
                    self.last_event_ts = datetime.now(LOCAL_TZ)
                    pay = _payload_open(self.identifier, self.chart_url, self.interval_str, entry, raw, recalc)
                    self.publish(pay)
                    self._post_webhook(pay, logger)
                    logger.info("open %s (baseline)", num)
            else:
                self._historical_closed.add(num)

    def _emit_synthetic_open_then_close(self, raw: dict, logger, cur, conn):
        """
        For a row that is already closed and we never emitted an 'open'
        (e.g., open+close occurred during refresh), emit synthetic OPEN followed by CLOSE.
        """
        num = raw.get("num")
        self._store_entry_if_absent(raw)
        entry = self._entry_info[num]

        if num not in self._ann_open:
            new_dir = _direction_from_raw_signal(raw)
            recalc = False
            if new_dir is not None:
                recalc = (self._current_direction != new_dir)
                self._current_direction = new_dir
            pay_open = _payload_open(self.identifier, self.chart_url, self.interval_str, entry, raw, recalc)
            self._ann_open.add(num)
            self.opens_seen += 1
            self.publish(pay_open)
            self._post_webhook(pay_open, logger)
            logger.info("open %s (synthetic)", num)

        if num not in self._ann_close:
            pay_close = _payload_close(self.identifier, self.chart_url, self.interval_str, entry, raw)
            self._ann_close.add(num)
            self.closes_seen += 1
            self.publish(pay_close)
            self._post_webhook(pay_close, logger)
            if num not in self._persisted_close:
                self._upsert(cur, raw, self.identifier, entry_price=entry.get("entry_price"))
                conn.commit()
                self._persisted_close.add(num)
                logger.info("db upsert %s (catch-up)", num)
            logger.info("close %s (synthetic)", num)

    def _catch_up_after_refresh(self, sb: SB, logger, cur, conn):
        """
        After a browser refresh, scan the table once and emit missed events.
        Ensures single-delivery by using _ann_open / _ann_close sets.
        """
        rows = scan_all_trades_once(sb)
        for raw in rows:
            num = raw.get("num")
            sig_last = (raw.get("signal") or "").split(", ")[-1]

            if sig_last == "Open":
                if num not in self._ann_open:
                    self._store_entry_if_absent(raw)
                    entry = self._entry_info[num]
                    new_dir = _direction_from_raw_signal(raw)
                    recalc = False
                    if new_dir is not None:
                        recalc = (self._current_direction != new_dir)
                        self._current_direction = new_dir
                    self._ann_open.add(num)
                    self.opens_seen += 1
                    self.last_event_ts = datetime.now(LOCAL_TZ)
                    pay = _payload_open(self.identifier, self.chart_url, self.interval_str, entry, raw, recalc)
                    self.publish(pay)
                    self._post_webhook(pay, logger)
                    logger.info("open %s (catch-up)", num)
                continue

            # Closed
            if num in self._historical_closed and num not in self._ann_open:
                continue

            if num in self._ann_open:
                if num not in self._ann_close:
                    self._store_entry_if_absent(raw)
                    entry = self._entry_info[num]
                    pay = _payload_close(self.identifier, self.chart_url, self.interval_str, entry, raw)
                    self._ann_close.add(num)
                    self.closes_seen += 1
                    self.publish(pay)
                    self._post_webhook(pay, logger)
                    if num not in self._persisted_close:
                        self._upsert(cur, raw, self.identifier, entry_price=entry.get("entry_price"))
                        conn.commit()
                        self._persisted_close.add(num)
                        logger.info("db upsert %s (catch-up)", num)
                    logger.info("close %s (catch-up)", num)
            else:
                self._emit_synthetic_open_then_close(raw, logger, cur, conn)

    def _maybe_refresh(self, sb: SB, now: datetime, logger, cur, conn):
        if not self.refresh_enabled or not self.next_refresh_at:
            return
        if now >= self.next_refresh_at:
            logger.info(
                "refresh trigger @ %s (interval=%s, next=%s)",
                now.strftime("%H:%M:%S"),
                self.interval_str,
                self.next_refresh_at.strftime("%H:%M:%S"),
            )
            try:
                sb.refresh()
            except Exception as e:
                log.warning("%s refresh failed: %s", self.name, e)
            try:
                self._catch_up_after_refresh(sb, logger, cur, conn)
            except Exception as e:
                log.warning("%s catch-up failed: %s", self.name, e)

            # Reschedule and log
            self._refresh_schedule(sb, datetime.now(LOCAL_TZ))
            if self.next_refresh_at:
                logger.info(
                    "next refresh scheduled @ %s",
                    self.next_refresh_at.strftime("%H:%M:%S"),
                )

    def run(self):
        logger = logging.getLogger(self.name)
        logger.info("worker started")
        try:
            with psycopg2.connect(DB_DSN) as conn, conn.cursor() as cur, SB(headless=False) as sb:
                if load_cookies_json(sb, self.identifier, self.chart_url):
                    logger.info("cookies loaded for %s", self.identifier)
                else:
                    logger.info("no cookies file for %s", self.identifier)

                logger.info("opening chart url %s", self.chart_url)
                sb.open(self.chart_url)
                sb.wait(1)

                # Schedule refresh before any event emissions
                now = datetime.now(LOCAL_TZ)
                self._refresh_schedule(sb, now)
                if self.next_refresh_at:
                    logger.info(
                        "initial refresh scheduled @ %s (interval=%s)",
                        self.next_refresh_at.strftime("%H:%M:%S"),
                        self.interval_str,
                    )

                logged = verifyIfLoggedIn(sb)
                logger.info("verifyIfLoggedIn -> %s", logged)
                if not logged:
                    logger.info("logging-in")
                    # pass per-request creds if provided
                    login(sb, self.tv_username, self.tv_password)
                    logger.info("login complete; reopening chart url")
                    sb.open(self.chart_url)
                    sb.wait(1)
                    save_cookies_json(sb, self.identifier)
                    logger.info("cookies saved for %s", self.identifier)
                    now = datetime.now(LOCAL_TZ)
                    self._refresh_schedule(sb, now)
                    if self.next_refresh_at:
                        logger.info(
                            "initial refresh scheduled @ %s (interval=%s)",
                            self.next_refresh_at.strftime("%H:%M:%S"),
                            self.interval_str,
                        )

                # Ensure we have a schedule if refresh is enabled
                if self.refresh_enabled and not self.next_refresh_at:
                    self._refresh_schedule(sb, datetime.now(LOCAL_TZ))
                    if self.next_refresh_at:
                        logger.info(
                            "initial refresh scheduled @ %s (interval=%s)",
                            self.next_refresh_at.strftime("%H:%M:%S"),
                            self.interval_str,
                        )

                # Send alive and publish to SSE
                if not self._posted_alive:
                    activated = datetime.now(LOCAL_TZ)
                    alive_payload = _payload_alive(self.identifier, self.chart_url, self.interval_str, activated)
                    self.publish(alive_payload)
                    self._post_webhook(alive_payload, logger)
                    self._posted_alive = True

                # Baseline after activation: only emit currently-open
                self._baseline_after_activation(sb, logger, cur, conn)

                # Live tail
                for raw in scrapeListOfTrades(
                    sb,
                    poll_interval=self.poll_interval,
                    deep_scan_every=self.deep_scan_every,
                    status_every=self.status_every,
                ):
                    if self._stop.is_set():
                        logger.info("stop requested")
                        break

                    if raw.get("__tick__"):
                        self._maybe_refresh(sb, datetime.now(LOCAL_TZ), logger, cur, conn)
                        continue

                    self._maybe_refresh(sb, datetime.now(LOCAL_TZ), logger, cur, conn)

                    num = raw.get("num")
                    sig_last = (raw.get("signal") or "").split(", ")[-1]

                    if sig_last == "Open":
                        if num not in self._ann_open:
                            self._store_entry_if_absent(raw)
                            entry = self._entry_info[num]
                            # Determine recalc for OPENs only
                            new_dir = _direction_from_raw_signal(raw)
                            recalc = False
                            if new_dir is not None:
                                recalc = (self._current_direction != new_dir)
                                self._current_direction = new_dir
                            self._ann_open.add(num)
                            self.opens_seen += 1
                            self.last_event_ts = datetime.now(LOCAL_TZ)
                            pay = _payload_open(self.identifier, self.chart_url, self.interval_str, entry, raw, recalc)
                            self.publish(pay)
                            self._post_webhook(pay, logger)
                            logger.info("open %s", num)
                        continue

                    # Closed
                    if num in self._historical_closed and num not in self._ann_open:
                        continue

                    if num not in self._ann_open:
                        # Synthetic open then close when open+close happened in between scans
                        self._emit_synthetic_open_then_close(raw, logger, cur, conn)
                        continue

                    if num not in self._ann_close:
                        self._store_entry_if_absent(raw)
                        entry = self._entry_info[num]
                        self._ann_close.add(num)
                        self.closes_seen += 1
                        self.last_event_ts = datetime.now(LOCAL_TZ)
                        pay = _payload_close(self.identifier, self.chart_url, self.interval_str, entry, raw)
                        self.publish(pay)
                        self._post_webhook(pay, logger)
                        logger.info("close %s", num)

                    if num not in self._persisted_close:
                        self._upsert(cur, raw, self.identifier, entry_price=entry.get("entry_price"))
                        conn.commit()
                        self._persisted_close.add(num)
                        logger.info("db upsert %s", num)

        except Exception:
            logger.exception("worker crashed")
        finally:
            if not self._posted_dead:
                stopped = datetime.now(LOCAL_TZ)
                dead_payload = _payload_dead(self.identifier, self.chart_url, self.interval_str, stopped)
                self.publish(dead_payload)
                self._post_webhook(dead_payload, logger)
                self._posted_dead = True
            logger.info("worker finished. opens=%s closes=%s", self.opens_seen, self.closes_seen)
