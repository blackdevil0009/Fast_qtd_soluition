# fastqtd/auto_traceback.py
"""
Auto-traceback module:
- Given an account or a starting transaction, traverse simulated transfer edges (mule-to-mule)
  and return a full graph of sub-transactions and involved accounts.
- For demo: it uses DB traces (if present) and also can accept a synthetic transfer list.
"""

import time, json
from .db import fetch_traces_for_account, add_traceback

# Simple in-memory simulated ledger for demo. In production, replace this with bank/ledger API calls.
# Format: { 'txn_id': {'from': acct, 'to': acct, 'amount': 100, 'timestamp': ...} }
SIM_LEDGER = {}

def register_simulated_txn(txn_id, from_acct, to_acct, amount):
    SIM_LEDGER[txn_id] = {
        'from': from_acct,
        'to': to_acct,
        'amount': amount,
        'timestamp': time.time()
    }

def build_graph_from_start_account(start_account, max_hops=5):
    """
    BFS over SIM_LEDGER edges finding all transactions originating from start_account,
    following to subsequent accounts (mule flows).
    """
    try:
        visited_accounts = set()
        visited_txns = set()
        results = []

        queue = [start_account]
        hops = 0
        while queue and hops < max_hops:
            next_queue = []
            for acct in queue:
                # fetch ledger txns where 'from' == acct
                for txn_id, txn in list(SIM_LEDGER.items()):
                    if txn['from'] == acct and txn_id not in visited_txns:
                        visited_txns.add(txn_id)
                        results.append({
                            'txn_id': txn_id,
                            'from': txn['from'],
                            'to': txn['to'],
                            'amount': txn['amount'],
                            'timestamp': txn['timestamp']
                        })
                        if txn['to'] not in visited_accounts:
                            next_queue.append(txn['to'])
                            visited_accounts.add(txn['to'])
            queue = next_queue
            hops += 1

        return {
            'start_account': start_account,
            'txns': results,
            'hops_searched': hops
        }
    except Exception as e:
        add_traceback('build_graph_from_start_account', e)
        raise

def trace_subtransactions_for_txn(txn_id, max_depth=5):
    """
    For a given txn_id, trace forward all child txns where 'from' == original 'to' and so on.
    Returns a list of sub-transactions.
    """
    try:
        if txn_id not in SIM_LEDGER:
            return {'txn_id': txn_id, 'found': False, 'sub_txns': []}
        root = SIM_LEDGER[txn_id]
        start_acct = root['to']
        return build_graph_from_start_account(start_acct, max_hops=max_depth)
    except Exception as e:
        add_traceback('trace_subtransactions_for_txn', e)
        raise

def trace_using_db(account_id, max_hops=4):
    """
    Use stored traces in DB (fastqtd.db traces table) to expand the chain.
    DB traces are expected to be stored as lists of account hops.
    """
    try:
        rows = fetch_traces_for_account(account_id)
        aggregated = []
        for r in rows:
            aggregated.append(r['path'])
        # flatten and unique
        flat = []
        for p in aggregated:
            for a in p:
                if a not in flat:
                    flat.append(a)
        return {'account': account_id, 'aggregated_paths': flat, 'rows_used': len(rows)}
    except Exception as e:
        add_traceback('trace_using_db', e)
        raise
