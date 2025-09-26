
# fastqtd/db.py
import os, sqlite3, json
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'fastqtd.db')

def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    c = _conn()
    cur = c.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        txn_id TEXT,
        result_json TEXT,
        created_at REAL
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS traces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id TEXT,
        path_json TEXT,
        created_at REAL
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_json TEXT,
        created_at REAL
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_json TEXT,
        created_at REAL
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS freezes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        txn_id TEXT,
        reason TEXT,
        meta_json TEXT,
        created_at REAL
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS recoveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        txn_id TEXT,
        recovery_json TEXT,
        success INTEGER,
        created_at REAL
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS tracebacks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        context TEXT,
        traceback_text TEXT,
        created_at REAL
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS reversals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        txn_id TEXT,
        reversal_txn_id TEXT,
        amount TEXT,
        meta_json TEXT,
        created_at REAL
    )''')
    c.commit()
    c.close()

def log_detection(result: dict):
    c = _conn()
    cur = c.cursor()
    cur.execute('INSERT INTO detections (txn_id, result_json, created_at) VALUES (?, ?, ?)',
                (result.get('txn_id'), json.dumps(result), result.get('checked_at')))
    c.connection.commit()
    c.close()

def add_trace(account_id, path):
    import time, json
    c = _conn()
    cur = c.cursor()
    cur.execute('INSERT INTO traces (account_id, path_json, created_at) VALUES (?, ?, ?)',
                (account_id, json.dumps(path), time.time()))
    c.connection.commit()
    c.close()

def add_alert(payload):
    import time, json
    c = _conn()
    cur = c.cursor()
    cur.execute('INSERT INTO alerts (alert_json, created_at) VALUES (?, ?)',
                (json.dumps(payload), time.time()))
    c.connection.commit()
    c.close()

def add_report(payload):
    import time, json
    c = _conn()
    cur = c.cursor()
    cur.execute('INSERT INTO reports (report_json, created_at) VALUES (?, ?)',
                (json.dumps(payload), time.time()))
    c.connection.commit()
    c.close()

def add_freeze(txn_id, reason, meta=None):
    import time, json
    c = _conn()
    cur = c.cursor()
    cur.execute('INSERT INTO freezes (txn_id, reason, meta_json, created_at) VALUES (?, ?, ?, ?)',
                (txn_id, reason, json.dumps(meta or {}), time.time()))
    c.connection.commit()
    c.close()

def add_recovery(txn_id, recovery_info, success):
    import time, json
    c = _conn()
    cur = c.cursor()
    cur.execute('INSERT INTO recoveries (txn_id, recovery_json, success, created_at) VALUES (?, ?, ?, ?)',
                (txn_id, json.dumps(recovery_info), 1 if success else 0, time.time()))
    c.connection.commit()
    c.close()

def add_traceback(context, exc: Exception = None):
    import time, traceback
    tb = None
    if exc is not None:
        tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    else:
        tb = 'no-exception'
    c = _conn()
    cur = c.cursor()
    cur.execute('INSERT INTO tracebacks (context, traceback_text, created_at) VALUES (?, ?, ?)',
                (context, tb, time.time()))
    c.connection.commit()
    c.close()

def fetch_tracebacks(limit=50):
    c = _conn()
    cur = c.cursor()
    cur.execute('SELECT id, context, traceback_text, created_at FROM tracebacks ORDER BY id DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    result = []
    for r in rows:
        result.append({'id': r['id'], 'context': r['context'], 'traceback': r['traceback_text'], 'created_at': r['created_at']})
    c.close()
    return result

def add_reversal(txn_id, reversal_txn_id, amount, meta=None):
    import time, json
    c = _conn()
    cur = c.cursor()
    cur.execute('INSERT INTO reversals (txn_id, reversal_txn_id, amount, meta_json, created_at) VALUES (?, ?, ?, ?, ?)',
                (txn_id, reversal_txn_id, str(amount), json.dumps(meta or {}), time.time()))
    c.connection.commit()
    c.close()

def fetch_traces_for_account(account_id):
    """Helper to fetch trace rows for an account_id"""
    c = _conn()
    cur = c.cursor()
    cur.execute('SELECT id, account_id, path_json, created_at FROM traces WHERE account_id = ? ORDER BY id DESC', (account_id,))
    rows = cur.fetchall()
    res = []
    for r in rows:
        res.append({'id': r['id'], 'account_id': r['account_id'], 'path': json.loads(r['path_json']), 'created_at': r['created_at']})
    c.close()
    return res
