import json
import sqlite3
from typing import Optional

import requests

from config import (
    CONFIDENCE_THRESHOLD, DB_PATH, OLLAMA_MODEL,
    OLLAMA_URL, RULES_PATH, TAXONOMY,
)


# ---------------------------------------------------------------------------
# Rules cache
# ---------------------------------------------------------------------------

def load_rules() -> dict:
    try:
        with open(RULES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_rules(rules: dict) -> None:
    with open(RULES_PATH, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)


def lookup_rules(merchant: str, rules: dict) -> Optional[dict]:
    key = merchant.lower().strip()
    # Skip metadata keys
    if key.startswith('_'):
        return None
    # Exact match
    if key in rules and not key.startswith('_'):
        entry = rules[key]
        if 'category' in entry and 'subcategory' in entry:
            return entry
    # Prefix match
    for rule_key, val in rules.items():
        if rule_key.startswith('_'):
            continue
        if 'category' not in val:
            continue
        if key.startswith(rule_key) or rule_key.startswith(key):
            return val
    return None


# ---------------------------------------------------------------------------
# Few-shot corrections context
# ---------------------------------------------------------------------------

def _load_corrections(limit: int = 20) -> list[dict]:
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""
            SELECT merchant, description, type, category, subcategory
            FROM corrections
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [
            {'merchant': r[0], 'description': r[1], 'type': r[2],
             'category': r[3], 'subcategory': r[4]}
            for r in rows
        ]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Ollama LLM
# ---------------------------------------------------------------------------

def _build_prompt(merchant: str, amount: float, description: str, corrections: list[dict]) -> str:
    direction = 'expense/outflow' if amount < 0 else 'income/inflow'
    taxonomy_text = json.dumps(TAXONOMY, ensure_ascii=False, indent=2)

    few_shot = ''
    if corrections:
        examples = '\n'.join(
            f'  - "{c["merchant"]}" → {c["type"]} / {c["category"]} / {c["subcategory"]}'
            for c in corrections
        )
        few_shot = f"\nRecent human corrections (use as guidance):\n{examples}\n"

    return (
        "You are a personal finance transaction classifier.\n"
        "Classify the transaction into exactly one type, category, and subcategory from the taxonomy.\n"
        'Respond ONLY with JSON: {"type": "...", "category": "...", "subcategory": "...", "confidence": 0.0}\n\n'
        f"Taxonomy (type → category → subcategories):\n{taxonomy_text}\n"
        f"{few_shot}\n"
        "Transaction:\n"
        f"  Merchant: {merchant}\n"
        f"  Amount: {amount} EUR ({direction})\n"
        f"  Description: {str(description)[:160]}"
    )


def call_ollama(merchant: str, amount: float, description: str) -> Optional[dict]:
    corrections = _load_corrections()
    prompt = _build_prompt(merchant, amount, description, corrections)
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json().get('response', '{}')
        result = json.loads(raw)
        if 'category' in result and 'subcategory' in result and 'type' in result:
            result.setdefault('confidence', 0.5)
            return result
    except requests.exceptions.ConnectionError:
        pass  # Ollama not running
    except Exception as e:
        print(f"  [llm warn] {e}")
    return None


# ---------------------------------------------------------------------------
# Core labelling waterfall
# ---------------------------------------------------------------------------

def _label_one(tx: dict, rules: dict) -> dict:
    # Skip already-labelled rows (pre-labelled at ingest for savings/self-transfers)
    if tx.get('labelling_source'):
        return {}

    merchant = tx.get('merchant', '')

    # Layer 1 — rules cache
    hit = lookup_rules(merchant, rules)
    if hit:
        return {
            'type': hit['type'],
            'category': hit['category'],
            'subcategory': hit['subcategory'],
            'labelling_source': 'rule',
            'confidence': None,
            'reviewed': 1,
        }

    # Layer 2 — Ollama LLM
    result = call_ollama(merchant, tx.get('amount', 0), tx.get('description', ''))
    if result:
        return {
            'type': result['type'],
            'category': result['category'],
            'subcategory': result['subcategory'],
            'confidence': result['confidence'],
            'labelling_source': 'llm',
            'reviewed': 0,
        }

    # Ollama unreachable — leave unlabelled (will show red in UI)
    return {
        'type': None,
        'category': None,
        'subcategory': None,
        'labelling_source': None,
        'confidence': None,
        'reviewed': 0,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def label_new_transactions() -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, merchant, amount, description, labelling_source
        FROM transactions
        WHERE labelling_source IS NULL
    """).fetchall()

    rules = load_rules()
    stats = {'labelled': 0, 'rule': 0, 'llm': 0, 'failed': 0}
    total = len(rows)
    print(f"Labelling {total} unlabelled transactions...")

    for i, row in enumerate(rows, 1):
        tx = dict(row)
        merchant = tx.get('merchant', '?')
        try:
            update = _label_one(tx, rules)
            if not update:
                continue
            conn.execute("""
                UPDATE transactions
                SET type=?, category=?, subcategory=?, confidence=?,
                    labelling_source=?, reviewed=?
                WHERE id=?
            """, (
                update.get('type'),
                update.get('category'),
                update.get('subcategory'),
                update.get('confidence'),
                update.get('labelling_source'),
                update.get('reviewed', 0),
                tx['id'],
            ))
            conn.commit()
            src = update.get('labelling_source') or 'none'
            stats['labelled'] += 1
            if src == 'rule':
                stats['rule'] += 1
            elif src == 'llm':
                stats['llm'] += 1
            else:
                stats['failed'] += 1

            conf = f"  conf={update['confidence']:.2f}" if update.get('confidence') is not None else ''
            print(f"  [{i}/{total}] {src.upper():4s}  {merchant:<35} -> {update.get('category')}/{update.get('subcategory')}{conf}")

        except Exception as e:
            print(f"  [{i}/{total}] ERROR  {merchant}: {e}")
            stats['failed'] += 1

    conn.commit()
    conn.close()
    print(f"\nDone: {stats['labelled']} labelled ({stats['rule']} rule, {stats['llm']} llm, {stats['failed']} failed/skipped)")
    return stats


def relabel_transaction(tx_id: str, tx_type: str, category: str, subcategory: str) -> None:
    """Update a single transaction label. Does NOT touch rules.json — use learner.run_learn() for that."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        UPDATE transactions
        SET type=?, category=?, subcategory=?, labelling_source='human', reviewed=1
        WHERE id=?
    """, (tx_type, category, subcategory, tx_id))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    label_new_transactions()
