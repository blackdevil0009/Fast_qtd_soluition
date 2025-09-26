FAST+ Quantum Threat Defense (QTD) - Backend CLI (Kali friendly)
================================================================

This repository provides a modular backend CLI implementation of FAST+ QTD,
optimized for running in terminal/CLI mode.

Quick start (recommended Python 3.10+):
---------------------------------------
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ python3 scripts/setup_db.py
$ python3 scripts/train_model.py   # creates models/fraud_model.pkl
$ pip install -e .
$ fastqtd detect --txn 12345
$ fastqtd freeze --txn 12345 --reason "suspicious"
$ fastqtd recover --txn 12345
$ fastqtd traceback_log --limit 10

Notes:
- qcrypto.py uses AES-GCM as a placeholder. Replace with real PQC libraries for production.
- The ML model created by train_model.py is synthetic and for demo only.
