# scripts/demo.py
"""
Extended End-to-End Demo for FAST+ QTD Backend (CLI mode)
---------------------------------------------------------
Simulates a fraud case and inspects DB records.
"""

import json
from fastqtd.engine import detect_transaction, freeze_transaction, instant_revert, register_sim_txn
from fastqtd.auto_traceback import trace_subtransactions_for_txn
from fastqtd.db import init_db, _conn

def pp(obj, title=None):
    if title:
        print(f"\n--- {title} ---")
    print(json.dumps(obj, indent=2))

def fetch_table(name):
    conn = _conn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {name}")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def run_demo():
    print("=== FAST+ QTD Demo Start ===")

    # 1. Init DB
    init_db()

    # 2. Register mule transactions
    print("\n[Step 1] Register mule transactions...")
    register_sim_txn("T1", "muleA", "muleB", 5000)
    register_sim_txn("T2", "muleB", "muleC", 4000)
    register_sim_txn("T3", "muleC", "muleD", 3900)

    # 3. Detect fraud on T1
    print("\n[Step 2] Detecting fraud for T1...")
    detection = detect_transaction("T1")
    print(detection)

    # 4. Freeze only part of T1 (suspected amount = 4000)
    print("\n[Step 3] Freezing partial amount from T1...")
    freeze_result = freeze_transaction("T1", suspect_amount=4000, reason="pattern matched")
    print(freeze_result)

    # 5. Auto-trace mule flow starting from T1 recipient
    print("\n[Step 4] Auto-tracing mule flow from T1...")
    traced = trace_subtransactions_for_txn("T1", max_depth=5)
    pp(traced)

    # 6. Instant revert (try to recover frozen funds)
    print("\n[Step 5] Performing instant revert for T1...")
    revert = instant_revert("T1", requested_amount=4000)
    print(revert)

    # 7. Inspect DB tables
    print("\n[Step 6] Inspecting DB records...")
    pp(fetch_table("detections"), "Detections")
    pp(fetch_table("freezes"), "Freezes")
    pp(fetch_table("recoveries"), "Recoveries")
    pp(fetch_table("reversals"), "Reversals")
    pp(fetch_table("tracebacks"), "Tracebacks")

    print("\n=== FAST+ QTD Demo End ===")

if __name__ == "__main__":
    run_demo()
