# db.py
import os, psycopg2,json

DSN = (
    f"host={os.getenv('DB_HOST','localhost')} "
    f"port={os.getenv('DB_PORT','5432')} "
    f"dbname={os.getenv('DB_NAME','nextlayer')} "
    f"user={os.getenv('DB_USER','nl_user')} "
    f"password={os.getenv('DB_PASS','nlpass')}"
)

def connect():
    return psycopg2.connect(DSN)

# UPSERT now includes 'position'
UPSERT = """
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

def fetch_trades(cur, identifier: str, limit: int = 200):
    cur.execute(
        """SELECT tradeId, opened_at, closed_at, type, signal,
                  open_price, close_price, position
           FROM trades
           WHERE identifier=%s
           ORDER BY opened_at DESC
           LIMIT %s""",
        (identifier, limit),
    )
    rows = cur.fetchall()
    out = []
    for (tradeId, opened_at, closed_at, typ, signal, open_price, close_price, position) in rows:
        out.append(dict(
            tradeId=tradeId,
            opened_at=opened_at.isoformat() if opened_at else None,
            closed_at=closed_at.isoformat() if closed_at else None,
            type=typ,
            signal=signal,
            open_price=float(open_price) if open_price is not None else None,
            close_price=float(close_price) if close_price is not None else None,
            position=position,  # NEW
        ))
    return out

""" gett all trades """
def fetch_all_trades(cur, limit: int = 2000):
    """
    trades tablosundaki tüm kayıtları getirir.
    """
    cur.execute(
        """SELECT tradeId, identifier, opened_at, closed_at, type, signal,
                         open_price, close_price, position
           FROM trades
           ORDER BY opened_at DESC
           LIMIT %s""",
        (limit,),
    )
    rows = cur.fetchall()
    out = []
    for (tradeId, identifier, opened_at, closed_at, typ, signal, open_price, close_price, position) in rows:
        out.append(dict(
            tradeId=tradeId,
            identifier=identifier,
            opened_at=opened_at.isoformat() if opened_at else None,
            closed_at=closed_at.isoformat() if closed_at else None,
            type=typ,
            signal=signal,
            open_price=float(open_price) if open_price is not None else None,
            close_price=float(close_price) if close_price is not None else None,
            position=float(position) if position is not None else None,
        ))
    return out




""" confiugration table"""
def insert_configuration(cur, data: dict):
    """
    configuration tablosuna veri ekler.
    data: dict {
        tv_username, tv_password, executor, exchange, runner_id,
        starting_balance, margin_type, leverage, currency_pair,
        order_type, base_point, divide_equity, transaction_ratio,
        trade_entry_time, trade_exit_time, trade_pnl
    }
    """
    cur.execute(
        """
        INSERT INTO configuration (
            tv_username, tv_password, executor, exchange, runner_id,
            starting_balance, margin_type, leverage, currency_pair,
            order_type, base_point, divide_equity, transaction_ratio,
            trade_entry_time, trade_exit_time, trade_pnl
        ) VALUES (
            %(tv_username)s, %(tv_password)s, %(executor)s, %(exchange)s, %(runner_id)s,
            %(starting_balance)s, %(margin_type)s, %(leverage)s, %(currency_pair)s,
            %(order_type)s, %(base_point)s, %(divide_equity)s, %(transaction_ratio)s,
            %(trade_entry_time)s, %(trade_exit_time)s, %(trade_pnl)s
        )
        RETURNING runner_id;
        """,
        data
    )
    return cur.fetchone()[0]


def fetch_all_configurations(cur, limit: int = 100):
    """
    configuration tablosundaki verileri çeker.
    """
    cur.execute(
        """
        SELECT runner_id, tv_username, tv_password, executor, exchange,
               starting_balance, margin_type, leverage, currency_pair,
               order_type, base_point, divide_equity, transaction_ratio,
               trade_entry_time, trade_exit_time, trade_pnl
        FROM configuration
        ORDER BY runner_id DESC
        LIMIT %s;
        """,
        (limit,)
    )
    rows = cur.fetchall()
    out = []
    for r in rows:
        out.append(dict(
            runner_id=r[0],
            tv_username=r[1],
            tv_password=r[2],
            executor=r[3],
            exchange=r[4],
            starting_balance=float(r[5]) if r[5] is not None else None,
            margin_type=r[6],
            leverage=float(r[7]) if r[7] is not None else None,
            currency_pair=r[8],
            order_type=r[9],
            base_point=float(r[10]) if r[10] is not None else None,
            divide_equity=int(r[11]) if r[11] is not None else None,
            transaction_ratio=float(r[12]) if r[12] is not None else None,
            trade_entry_time=int(r[13]) if r[13] is not None else None,
            trade_exit_time=int(r[14]) if r[14] is not None else None,
            trade_pnl=float(r[15]) if r[15] is not None else None
        ))
    return out




""" signal table"""
# --------------------------
# insert
# --------------------------
def insert_signal(signal_data: dict):
    """signals tablosuna veri ekler"""
    sql = """
    INSERT INTO public.signals
    (tradeid, identifier, opened_at, closed_at, type, signal, open_price, close_price, position)
    VALUES (%(tradeid)s, %(identifier)s, %(opened_at)s, %(closed_at)s, %(type)s, %(signal)s, %(open_price)s, %(close_price)s, %(position)s)
    ON CONFLICT (tradeid)
    DO UPDATE SET
        closed_at = EXCLUDED.closed_at,
        type = EXCLUDED.type,
        signal = EXCLUDED.signal,
        close_price = EXCLUDED.close_price,
        position = EXCLUDED.position;
    """
    with psycopg2.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, signal_data)
            conn.commit()
    print("Signal added ✅")


# --------------------------
# fetch
# --------------------------
def fetch_signals(identifier: str = None, limit: int = 100):
    """signals tablosundan veri çeker"""
    sql = "SELECT tradeid, identifier, opened_at, closed_at, type, signal, open_price, close_price, position FROM public.signals"
    params = ()
    if identifier:
        sql += " WHERE identifier = %s"
        params = (identifier,)
    sql += " ORDER BY opened_at DESC LIMIT %s"
    params += (limit,)

    with psycopg2.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    # Satırları dict listesine çevir
    result = []
    for r in rows:
        result.append({
            "tradeid": r[0],
            "identifier": r[1],
            "opened_at": r[2].isoformat() if r[2] else None,
            "closed_at": r[3].isoformat() if r[3] else None,
            "type": r[4],
            "signal": r[5],
            "open_price": float(r[6]) if r[6] is not None else None,
            "close_price": float(r[7]) if r[7] is not None else None,
            "position": float(r[8]) if r[8] is not None else None
        })
    return result


""" trade_bakcups table"""


UPSERT_SQL = """
INSERT INTO trade_backup (
    runner_id,
    identifier,
    first_balance,
    now_balance,
    buyed_or_selled_coin_qty,
    trade_count
)
VALUES (
    %(runner_id)s,
    %(identifier)s,
    %(first_balance)s,
    %(now_balance)s,
    %(buyed_or_selled_coin_qty)s,
    %(trade_count)s
)
ON CONFLICT (runner_id, identifier)
DO UPDATE SET
    now_balance = EXCLUDED.now_balance,
    buyed_or_selled_coin_qty = EXCLUDED.buyed_or_selled_coin_qty,
    trade_count = EXCLUDED.trade_count
;
"""

def upsert_trade_backup(trade: dict):
    """trade_backup tablosuna kayıt ekler veya günceller"""
    with psycopg2.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(UPSERT_SQL, trade)
        conn.commit()
    print("Trade backup updated ✅")


def fetch_trade_backup():
    with psycopg2.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute("SELECT runner_id, identifier, first_balance, now_balance, buyed_or_selled_coin_qty, trade_count FROM trade_backup")
        rows = cur.fetchall()
        out = []
        for row in rows:
            out.append({
                "runner_id": row[0],
                "identifier": row[1],
                "first_balance": float(row[2]) if row[2] is not None else None,
                "now_balance": float(row[3]) if row[3] is not None else None,
                "buyed_or_selled_coin_qty": float(row[4]) if row[4] is not None else None,
                "trade_count": row[5]
            })
        return out
    
