# fastqtd/cli.py
import click
from .engine import detect_transaction, trace_account, freeze_transaction, recover_transaction_by_ai, instant_revert, register_sim_txn
from .qcrypto import encrypt_file, decrypt_file
from .scamalert import send_alert
from .legalconnect import report_case
from .db import fetch_tracebacks
from .auto_traceback import trace_subtransactions_for_txn, build_graph_from_start_account, trace_using_db

@click.group()
def cli():
    """FAST+ Quantum Threat Defense (QTD) CLI"""
    pass

@cli.command()
@click.option('--txn', required=True, help='Transaction ID')
def detect(txn):
    """Detect fraudulent transaction"""
    result = detect_transaction(txn)
    click.echo(result)

@cli.command()
@click.option('--account', required=True, help='Account ID')
def trace(account):
    """Trace scammer account (DB-simulated)"""
    result = trace_account(account)
    click.echo(result)

@cli.command()
@click.option('--txn', required=True, help='Transaction ID')
@click.option('--amount', required=True, type=float, help='Suspected amount to freeze')
@click.option('--reason', default='suspected_fraud', help='Reason to freeze')
def freeze(txn, amount, reason):
    """Freeze only the suspected amount for a transaction/account"""
    result = freeze_transaction(txn, amount, reason)
    click.echo(result)

@cli.command()
@click.option('--txn', required=True, help='Transaction ID to attempt recovery')
def recover(txn):
    """Attempt recovery of a transaction using AI model (legacy)"""
    result = recover_transaction_by_ai(txn)
    click.echo(result)

@cli.command()
@click.option('--txn', required=True, help='Transaction ID to instant revert (attempt immediate reversal)')
@click.option('--amount', required=False, type=float, help='Amount to revert (optional)')
def instant_revert_cmd(txn, amount):
    """Attempt instant revert (immediate reversal) of a transaction"""
    result = instant_revert(txn, requested_amount=amount)
    click.echo(result)

@cli.command()
@click.option('--txn', required=True, help='Transaction ID to trace sub-transactions for (simulated ledger)')
@click.option('--depth', default=5, type=int, help='Max depth/hops to trace')
def auto_trace(txn, depth):
    """Trace sub-transactions originated from a txn's recipient (demo-mode)"""
    res = trace_subtransactions_for_txn(txn, max_depth=depth)
    click.echo(json_dump(res))

@cli.command()
@click.option('--account', required=True, help='Start account for auto tracing (simulated ledger)')
@click.option('--hops', default=5, type=int, help='Hops to search')
def auto_trace_account(account, hops):
    """Auto-trace forward flows for a starting account (demo-mode)"""
    res = build_graph_from_start_account(account, max_hops=hops)
    click.echo(json_dump(res))

@cli.command()
@click.option('--txn', required=True, help='Transaction ID')
@click.option('--from-acct', required=True, help='From account (for simulation registration)')
@click.option('--to-acct', required=True, help='To account (for simulation registration)')
@click.option('--amount', required=True, type=float, help='Amount for simulated txn')
def register_txn(txn, from_acct, to_acct, amount):
    """Register a simulated transaction in the in-memory demo ledger"""
    res = register_sim_txn(txn, from_acct, to_acct, amount)
    click.echo(json_dump(res))

@cli.command()
@click.option('--file', 'file_path', required=True, help='File to encrypt')
def encrypt(file_path):
    """Encrypt file with quantum-safe crypto (placeholder AES-GCM)"""
    encrypted_path = encrypt_file(file_path)
    click.echo(f'Encrypted file: {encrypted_path}')

@cli.command()
@click.option('--file', 'file_path', required=True, help='File to decrypt')
def decrypt(file_path):
    """Decrypt a .enc file"""
    out = decrypt_file(file_path)
    click.echo(f'Decrypted to: {out}')

@cli.command()
@click.option('--message', required=True, help='Scam alert message')
def alert(message):
    """Send scam alert (prints to console and logs)"""
    send_alert(message)
    click.echo('Alert sent (logged).')

@cli.command()
@click.option('--case-id', required=True, help='Case ID to report')
def report(case_id):
    """Report scam to authorities (simulated)"""
    report_case(case_id)
    click.echo('Report submitted (simulated).')

@cli.command()
@click.option('--limit', default=20, help='Number of traceback rows to show')
def traceback_log(limit):
    """Show recent internal tracebacks captured by the system"""
    rows = fetch_tracebacks(limit)
    click.echo(rows)

def json_dump(obj):
    try:
        import json
        return json.dumps(obj, indent=2)
    except Exception:
        return str(obj)

if __name__ == '__main__':
    cli()
