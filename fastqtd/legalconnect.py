import time
from .db import add_report

def report_case(case_id: str):
    payload = {
        'case_id': case_id,
        'reported_at': time.time(),
        'status': 'submitted (simulated)'
    }
    add_report(payload)
    return payload
