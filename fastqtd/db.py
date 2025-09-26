# fastqtd/db.py
import os
import sqlite3
import json
import time
import traceback
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'fastqtd.db')

# Tunables
DEFAULT_TIMEOUT = 30.0          # sqlite3 connect timeout (seconds)
MAX_WRITE_RETRIES = 6           # number of times to retry on "database is locked"
RETRY_BASE_DELAY = 0.05         # base delay (seconds) for exponential backoff

def _ensure_db_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_conn():
    """
    Return a new sqlite3.Connection configured for better concurrency.
    Always create a new connection per operation (recommended).
    """
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH, timeout=DEFAULT_TIMEOUT, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrent reads/writes (reader won't block writer as much)
    # and set synchronous to NORMAL for better performance without losing much safety.
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
    except Exception:
        # Ignore if pragmas fail for some reason, but continue
        pass
    return conn

def _execute_write(sql: str, params: tuple = ()):
    """
    Execute a single write (INSERT/UPDATE/DELETE) with retries on 'database is locked'.
    Commits with the connection context manager to ensure proper commit/rollback.
    """
    attempt = 0
    while True:
        try:
            conn = get_conn()
            try:
                with conn:
                    cur = conn.cursor()
                    cur.execute(sql, params)
                # success, close and return
                conn.close()
                return
            finally:
                # ensure closed even if commit fails (with conn: should handle it)
                try:
                    conn.close()
                except Exception:
                    pass
        except sqlite3.OperationalError as e:
            msg = str(e).lower()
            if 'locked' in msg and attempt < MAX_WRITE_RETRIES:
                sleep_time = RETRY_BASE_DELAY * (2 ** attempt)
                time.sleep(sleep_time)
                attempt += 1
                continue
            # re-raise the original OperationalError after attempts
            raise

def _execute_fetchall(sql: str, params: tuple = ()) -> List[sqlite3.Row]:
    """
    Execute a SELECT and return rows. Uses its own connection and closes it.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()

# --- Schema initialization ---
def init_db():
    # Use _execute_write to ensure retries and proper commits
    _ensure_db_dir()
    # Create tables (one write per CREATE TABLE to use retry logic)
    tables = [
        '''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txn_id TEXT,
            result_json TEXT,
            created_at REAL
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT,
            path_json TEXT,
            created_at REAL
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_json TEXT,
            created_at REAL
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_json TEXT,
            created_at REAL
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS freezes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txn_id TEXT,
            reason TEXT,
            meta_json TEXT,
            created_at REAL
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS recoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txn_id TEXT,
            recovery_json TEXT,
            success INTEGER,
            created_at REAL
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS tracebacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            context TEXT,
            traceback_text TEXT,
            created_at REAL
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS reversals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txn_id TEXT,
            reversal_txn_id TEXT,
            amount TEXT,
            meta_json TEXT,
            created_at REAL
        )
        '''
    ]
    for sql in tables:
        _execute_write(sql, ())

# --- Convenience wrappers for common operations ---

def log_detection(result: dict):
    _execute_write(
        'INSERT INTO detections (txn_id, result_json, created_at) VALUES (?, ?, ?)',
        (result.get('txn_id'), json.dumps(result), result.get('checked_at', time.time()))
    )

def add_trace(account_id, path):
    _execute_write(
        'INSERT INTO traces (account_id, path_json, created_at) VALUES (?, ?, ?)',
        (account_id, json.dumps(path), time.time())
    )

def add_alert(payload):
    _execute_write(
        'INSERT INTO alerts (alert_json, created_at) VALUES (?, ?)',
        (json.dumps(payload), time.time())
    )

def add_report(payload):
    _execute_write(
        'INSERT INTO reports (report_json, created_at) VALUES (?, ?)',
        (json.dumps(payload), time.time())
    )

def add_freeze(txn_id, reason, meta=None):
    _execute_write(
        'INSERT INTO freezes (txn_id, reason, meta_json, created_at) VALUES (?, ?, ?, ?)',
        (txn_id, reason, json.dumps(meta or {}), time.time())
    )

def add_recovery(txn_id, recovery_info, success):
    _execute_write(
        'INSERT INTO recoveries (txn_id, recovery_json, success, created_at) VALUES (?, ?, ?, ?)',
        (txn_id, json.dumps(recovery_info), 1 if success else 0, time.time())
    )

def add_traceback(context, exc: Exception = None):
    # Build traceback text safely (don't attempt to call add_traceback if DB is already failing repeatedly)
    try:
        tb_text = None
        if exc is not None:
            tb_text = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        else:
            tb_text = 'no-exception'
        _execute_write(
            'INSERT INTO tracebacks (context, traceback_text, created_at) VALUES (?, ?, ?)',
            (context, tb_text, time.time())
        )
    except Exception as e:
        # If writing tracebacks fails (DB locked/broken), fallback to stderr file (avoid recursion)
        try:
            with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'traceback_fallback.log'), 'a') as fh:
                fh.write(f"[{time.time()}] Failed to write traceback to DB for context={context}. Exception: {e}\n")
                if exc is not None:
                    fh.write(tb_text + "\n")
        except Exception:
            # give up silently to avoid crashing further
            pass

def fetch_tracebacks(limit=50) -> List[Dict[str, Any]]:
    rows = _execute_fetchall(
        'SELECT id, context, traceback_text, created_at FROM tracebacks ORDER BY id DESC LIMIT ?',
        (limit,)
    )
    return [{'id': r['id'], 'context': r['context'], 'traceback': r['traceback_text'], 'created_at': r['created_at']} for r in rows]

def add_reversal(txn_id, reversal_txn_id, amount, meta=None):
    _execute_write(
        'INSERT INTO reversals (txn_id, reversal_txn_id, amount, meta_json, created_at) VALUES (?, ?, ?, ?, ?)',
        (txn_id, reversal_txn_id, str(amount), json.dumps(meta or {}), time.time())
    )

def fetch_traces_for_account(account_id):
    rows = _execute_fetchall(
        'SELECT id, account_id, path_json, created_at FROM traces WHERE account_id = ? ORDER BY id DESC',
        (account_id,)
    )
    return [{'id': r['id'], 'account_id': r['account_id'], 'path': json.loads(r['path_json']), 'created_at': r['created_at']} for r in rows]

# Optional: generic fetch helpers for other tables
def fetch_table(name: str):
    rows = _execute_fetchall(f"SELECT * FROM {name} ORDER BY id ASC")
    return [dict(r) for r in rows]

