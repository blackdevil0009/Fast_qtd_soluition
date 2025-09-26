import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import secrets

# NOTE: This is a placeholder encryption module using AES-GCM.
# In production, swap to properly-vetted post-quantum encryption (NIST PQC libs) and secure key management.

_MASTER_SECRET_FILE = os.path.join(os.path.dirname(__file__), '..', 'keys', 'master.key')

def _ensure_master_key():
    key_dir = os.path.dirname(_MASTER_SECRET_FILE)
    os.makedirs(key_dir, exist_ok=True)
    if not os.path.exists(_MASTER_SECRET_FILE):
        secret = secrets.token_bytes(32)
        with open(_MASTER_SECRET_FILE, 'wb') as f:
            f.write(secret)
    with open(_MASTER_SECRET_FILE, 'rb') as f:
        return f.read()

def _derive_key(info: bytes=b'fastqtd-file') -> bytes:
    master = _ensure_master_key()
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info)
    return hkdf.derive(master)

def encrypt_file(path: str) -> str:
    """Encrypt a file at path using AES-GCM and save as <path>.enc"""
    key = _derive_key(b'file-encryption')
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)
    with open(path, 'rb') as f:
        data = f.read()
    ct = aesgcm.encrypt(nonce, data, None)
    out = path + '.enc'
    with open(out, 'wb') as f:
        f.write(nonce + ct)
    return out

def decrypt_file(path: str) -> str:
    """Decrypt a .enc file and write to <path>.dec"""
    key = _derive_key(b'file-encryption')
    aesgcm = AESGCM(key)
    with open(path, 'rb') as f:
        raw = f.read()
    nonce = raw[:12]
    ct = raw[12:]
    pt = aesgcm.decrypt(nonce, ct, None)
    out = path + '.dec'
    with open(out, 'wb') as f:
        f.write(pt)
    return out
