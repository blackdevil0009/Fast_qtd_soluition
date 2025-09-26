import time
from .db import add_alert

def send_alert(message: str):
    payload = {
        'message': message,
        'sent_at': time.time()
    }
    # For CLI demo: print to console and log to DB
    print('[SCAM ALERT]', message)
    add_alert(payload)
