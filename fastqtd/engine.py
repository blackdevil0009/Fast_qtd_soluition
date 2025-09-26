# fastqtd/engine.py
import os, json, time, traceback
from .db import log_detection, add_trace, add_freeze, add_recovery, add_traceback, add_reversal
from .auto_traceback import build_graph_from_start_account, trace_subtransactions_for_txn, register_simulated_txn
import joblib, random

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'fraud_model.pkl')

def _load_model():
    try:
        model = joblib.load(MODEL_PATH)
        return model
    except Exception:
        return None

def detect_transaction(txn_id: str):
    """Simulated fraud detection for a transaction id."""
    try:
        model = _load_model()
        features = _txn_to_features(txn_id)
        is_fraud = False
        score = 0.0
        if model:
            score = float(model.predict_proba([features])[0][1])
            is_fraud = score > 0.6
        else:
            score = random.random()
            is_fraud = score > 0.85

        result = {
            'txn_id': txn_id,
            'is_fraud': bool(is_fraud),
            'score': float(score),
            'checked_at': time.time()
        }
        log_detection(result)
        return json.dumps(result, indent=2)
    except Exception as e:
        add_traceback('detect_transaction', e)
        raise

def trace_account(account_id: str):
    """Simulated tracing: store a trace in local DB and return a fake path of transfers."""
    try:
        path = [account_id]
        for i in range(3):
            path.append(f'scam_{account_id}_{i}')
        trace = {
            'account': account_id,
            'path': path,
            'traced_at': time.time()
        }
        add_trace(account_id, path)
        return json.dumps(trace, indent=2)
    except Exception as e:
        add_traceback('trace_account', e)
        raise

def freeze_transaction(txn_id: str, suspect_amount: float, reason: str = 'suspected_fraud', currency: str = 'INR'):
    """
    Freeze only the suspected amount associated with txn_id.
    This function simulates creating an earmark / hold on the suspected_amount.
    """
    try:
        if suspect_amount <= 0:
            raise ValueError("suspect_amount must be > 0")

        meta = {
            'reason': reason,
            'frozen_amount': suspect_amount,
            'currency': currency,
            'frozen_at': time.time()
        }
        add_freeze(txn_id, reason, meta)
        return json.dumps({'txn_id': txn_id, 'frozen': True, 'meta': meta}, indent=2)
    except Exception as e:
        add_traceback('freeze_transaction', e)
        raise

def recover_transaction_by_ai(txn_id: str):
    """
    Legacy recover function kept for compatibility. It attempts a recovery using AI
    (proxy logic) and logs results. For instant revert use instant_revert().
    """
    try:
        model = _load_model()
        features = _txn_to_features(txn_id)
        success_prob = 0.0
        if model:
            success_prob = 1.0 - float(model.predict_proba([features])[0][1])
        else:
            success_prob = random.random() * 0.7

        success = success_prob > 0.5
        recovery_info = {
            'txn_id': txn_id,
            'attempted_at': time.time(),
            'success_prob': success_prob,
            'actions': ['freeze_related_accounts', 'notify_banks', 'submit_legal_request']
        }
        if success:
            recovery_info['reversal'] = {
                'reversal_txn_id': f'rev_{txn_id}_{int(time.time())}',
                'amount_recovered': 'partial_or_full_unknown_in_demo'
            }
        add_recovery(txn_id, recovery_info, success)
        return json.dumps({'txn_id': txn_id, 'recovered': bool(success), 'details': recovery_info}, indent=2)
    except Exception as e:
        add_traceback('recover_transaction_by_ai', e)
        raise

def instant_revert(txn_id: str, requested_amount: float = None):
    """
    Attempt an instant revert (reversal) of the given txn_id.
    - If requested_amount is specified, attempt to revert that amount.
    - Uses the model as advisory; instant revert simulates contacting bank and performing reversal.
    """
    try:
        # For demo: if txn exists in simulated ledger, reverse that exact amount; else create a synthetic reversal.
        # Check if there's a simulated txn in auto_traceback.SIM_LEDGER
        from .auto_traceback import SIM_LEDGER
        found = SIM_LEDGER.get(txn_id)
        if found:
            amount = requested_amount if requested_amount is not None else found['amount']
            reversal_id = f'ir_{txn_id}_{int(time.time())}'
            meta = {
                'reversed_amount': amount,
                'orig_from': found['from'],
                'orig_to': found['to'],
                'method': 'instant_revert_simulation',
                'timestamp': time.time()
            }
            # log reversal
            add_reversal(txn_id, reversal_id, amount, meta)
            # record recovery as success
            add_recovery(txn_id, {'reversal_txn_id': reversal_id, 'amount': amount, 'meta': meta}, True)
            return json.dumps({'txn_id': txn_id, 'reversed': True, 'reversal_txn_id': reversal_id, 'meta': meta}, indent=2)
        else:
            # no ledger entry: still attempt synthetic instant revert with probability
            model = _load_model()
            features = _txn_to_features(txn_id)
            adv = 0.4
            if model:
                adv = 1.0 - float(model.predict_proba([features])[0][1])
            success = adv > 0.5 or random.random() < 0.3
            if success:
                amount = requested_amount if requested_amount is not None else 'unknown_demo_amount'
                reversal_id = f'ir_{txn_id}_{int(time.time())}'
                meta = {'reversed_amount': amount, 'method': 'synthetic_instant_revert', 'timestamp': time.time()}
                add_reversal(txn_id, reversal_id, amount, meta)
                add_recovery(txn_id, {'reversal_txn_id': reversal_id, 'amount': amount, 'meta': meta}, True)
                return json.dumps({'txn_id': txn_id, 'reversed': True, 'reversal_txn_id': reversal_id, 'meta': meta}, indent=2)
            else:
                add_recovery(txn_id, {'attempted': True, 'reason': 'instant_revert_failed', 'advisory': adv}, False)
                return json.dumps({'txn_id': txn_id, 'reversed': False, 'advisory': adv}, indent=2)
    except Exception as e:
        add_traceback('instant_revert', e)
        raise

def register_sim_txn(txn_id, from_acct, to_acct, amount):
    """Helper to register simulated ledger transaction (for demo and tracing)."""
    try:
        # create the in-memory ledger entry
        register_simulated_txn(txn_id, from_acct, to_acct, amount)
        # attempt to store a DB trace but don't crash the whole process if DB write fails
        try:
            add_trace(from_acct, [from_acct, to_acct])
        except Exception as db_exc:
            # don't call add_traceback here because DB may be the problem; write to stderr/log instead
            print(f"Warning: add_trace failed (DB may be locked). Exception: {db_exc}")
        return {'txn_id': txn_id, 'registered': True}
    except Exception as e:
        # try to write a traceback — but guard against failing while writing tracebacks
        try:
            add_traceback('register_sim_txn', e)
        except Exception:
            # Emergency fallback
            print("Critical: failed to write traceback for register_sim_txn:", e)
        raise

def _txn_to_features(txn):
    vals = [ord(c) for c in txn][:20]
    mean = sum(vals)/len(vals) if vals else 0
    s = sum((v-mean)**2 for v in vals)/len(vals) if vals else 0
    padded = vals + [0]*(20-len(vals))
    features = padded[:5] + [mean, s, len(txn)]
    return features
