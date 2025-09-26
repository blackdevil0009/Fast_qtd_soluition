import time, json

def scan_profile(profile_json: str):
    """Pretend to scan a profile JSON for signs of fakeness."""
    try:
        obj = json.loads(profile_json)
    except Exception:
        return {'ok': False, 'reason': 'invalid json', 'score': 0.0}

    score = 0.0
    if 'profile_pic' not in obj: score += 0.3
    if 'bio' in obj and len(obj['bio']) < 20: score += 0.2
    if 'links' in obj and len(obj['links']) > 5: score += 0.2
    return {'ok': True, 'fake_score': score, 'checked_at': time.time()}
