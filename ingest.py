import hashlib
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import CHECKING_ACCOUNT, DB_PATH, OWN_NAME_VARIANTS


# ---------------------------------------------------------------------------
# Amount parsing
# ---------------------------------------------------------------------------

def parse_amount(s: str) -> float:
    return float(str(s).replace('.', '').replace(',', '.'))


# ---------------------------------------------------------------------------
# Transaction type detection (internal — used for merchant extraction only)
# ---------------------------------------------------------------------------

def detect_tx_type(description: str) -> str:
    d = str(description).upper()
    if d.startswith('PAYMENT VIA DEBIT MASTERCARD') or d.startswith('PAYMENT VIA BANCONTACT'):
        return 'CARD'
    if 'CREDIT TRANSFER FROM' in d or 'INSTANT CREDIT TRANSFER FROM' in d:
        return 'TRANSFER_IN'
    if 'SENDING MONEY INSTANTLY TO' in d or 'SENDING MONEY TO' in d:
        return 'TRANSFER_OUT'
    if 'EUROPEAN DIRECT DEBIT' in d:
        return 'DIRECT_DEBIT'
    if 'CASH WITHDRAWAL' in d:
        return 'ATM'
    if 'AUTOMATIC SAVINGS' in d:
        return 'SAVINGS'
    if d.startswith('CHARGE '):
        return 'BANK_CHARGE'
    if 'CORRECTING ENTRY' in d:
        return 'CORRECTION'
    return 'OTHER'


# ---------------------------------------------------------------------------
# Merchant name extraction
# ---------------------------------------------------------------------------

def extract_merchant(description: str, counterparty_raw: str, reference: str, tx_type: str) -> str:
    desc = str(description)

    if tx_type in ('CARD', 'ATM'):
        m = re.search(r'AT \d{2}\.\d{2} TIME (.+?) [A-Z]{2}\d{4,5}', desc)
        if m:
            return m.group(1).strip().title()
        m = re.search(r'TIME (.+?)(?:\s{2,}|$)', desc)
        if m:
            return m.group(1).strip().title()
        if tx_type == 'ATM':
            return 'Atm Withdrawal'

    if tx_type in ('TRANSFER_IN', 'TRANSFER_OUT'):
        cp = str(counterparty_raw).strip()
        if cp.lower() == 'stripe':
            return str(reference).strip().title()
        return cp.title()

    if tx_type == 'DIRECT_DEBIT':
        m = re.search(r'CREDITOR\s*:\s*(.+?)\s+CREDITOR REF', desc, re.IGNORECASE)
        if m:
            return m.group(1).strip().title()

    if tx_type == 'SAVINGS':
        return 'Automatic Savings'

    if tx_type == 'BANK_CHARGE':
        return 'Kbc Bank Charge'

    if tx_type == 'CORRECTION':
        return 'Correcting Entry'

    cp = str(counterparty_raw).strip()
    if cp and cp.lower() not in ('', 'nan', 'none'):
        return cp.title()
    return desc[:40].strip().title()


# ---------------------------------------------------------------------------
# Deduplication hash  (date | amount | merchant | reference)
# ---------------------------------------------------------------------------

def make_hash(date: str, amount: float, merchant: str, reference: str) -> str:
    key = f"{date}|{amount}|{merchant.lower().strip()}|{str(reference).lower().strip()}"
    return hashlib.sha256(key.encode()).hexdigest()


# ---------------------------------------------------------------------------
# SQLite schema
# ---------------------------------------------------------------------------

def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id                TEXT PRIMARY KEY,
            date              DATE NOT NULL,
            amount            REAL NOT NULL,
            description       TEXT,
            merchant          TEXT,
            account           TEXT,
            type              TEXT,
            category          TEXT,
            subcategory       TEXT,
            confidence        REAL,
            labelling_source  TEXT,
            reviewed          BOOLEAN DEFAULT 0,
            import_batch      TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS corrections (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant    TEXT,
            description TEXT,
            type        TEXT,
            category    TEXT,
            subcategory TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Core ingest
# ---------------------------------------------------------------------------

def ingest_csv(csv_path: str) -> dict:
    path = Path(csv_path)
    df = pd.read_csv(path, sep=';', encoding='latin-1', lineterminator='\r')
    df.columns = [c.strip() for c in df.columns]

    col_map = {
        'Date': 'date',
        'Description': 'description',
        'Amount': 'amount',
        'Counterparty name': 'counterparty_raw',
        'Free-format reference': 'reference',
        'Account number': 'account',
    }
    df = df.rename(columns=col_map)
    keep = [v for v in col_map.values() if v in df.columns]
    df = df[keep].copy()

    df['date'] = pd.to_datetime(df['date'].str.strip(), format='%d/%m/%Y').dt.date
    df['amount'] = df['amount'].apply(parse_amount)

    for col in ('counterparty_raw', 'reference', 'account', 'description'):
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()

    df['tx_type'] = df['description'].apply(detect_tx_type)
    df['merchant'] = df.apply(
        lambda r: extract_merchant(
            r['description'], r.get('counterparty_raw', ''), r.get('reference', ''), r['tx_type']
        ),
        axis=1,
    )

    # Detect savings account — any account other than the checking account
    # gets auto-labelled as Transfer / Savings Deposit
    account_val = df['account'].iloc[0] if 'account' in df.columns and not df.empty else CHECKING_ACCOUNT
    is_savings = account_val.strip() != CHECKING_ACCOUNT

    # Detect self-transfers on the checking account
    own_upper = [v.upper().strip() for v in OWN_NAME_VARIANTS]
    if not is_savings and 'counterparty_raw' in df.columns:
        df['_self_transfer'] = df['counterparty_raw'].apply(
            lambda cp: cp.upper().strip() in own_upper
        )
    else:
        df['_self_transfer'] = False

    # Compute hashes
    df['id'] = df.apply(
        lambda r: make_hash(str(r['date']), r['amount'], r['merchant'], r.get('reference', '')),
        axis=1,
    )

    import_batch = f"{path.name} @ {datetime.now().strftime('%Y-%m-%d')}"

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    total = len(df)
    inserted = 0
    skipped = 0

    for _, row in df.iterrows():
        # Pre-label savings account transactions
        if is_savings:
            pre_type, pre_cat, pre_sub, pre_src = 'Transfer', 'Transfer', 'Savings Deposit', 'rule'
        # Pre-label self-transfers on checking account
        elif row['_self_transfer']:
            if row['amount'] < 0:
                pre_type, pre_cat, pre_sub, pre_src = 'Transfer', 'Transfer', 'Internal Transfer', 'rule'
            else:
                pre_type, pre_cat, pre_sub, pre_src = 'Income', 'Income', 'Other Income', 'rule'
        else:
            pre_type = pre_cat = pre_sub = pre_src = None

        try:
            conn.execute("""
                INSERT OR IGNORE INTO transactions
                  (id, date, amount, description, merchant, account,
                   type, category, subcategory, labelling_source, import_batch)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['id'],
                str(row['date']),
                row['amount'],
                row.get('description', ''),
                row['merchant'],
                row.get('account', ''),
                pre_type,
                pre_cat,
                pre_sub,
                pre_src,
                import_batch,
            ))
            if conn.execute("SELECT changes()").fetchone()[0]:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  [warn] skipping row: {e}")
            skipped += 1

    conn.commit()
    conn.close()

    return {'total': total, 'inserted': inserted, 'skipped': skipped}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <path/to/file.csv>")
        sys.exit(1)
    result = ingest_csv(sys.argv[1])
    print(f"\nImport complete: {result['total']} rows | {result['inserted']} inserted | {result['skipped']} skipped")
