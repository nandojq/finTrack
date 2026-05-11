import sqlite3

from config import DB_PATH
from labeller import load_rules, save_rules


def run_learn() -> dict:
    """
    Scan all human-labelled transactions, update rules.json with merchant mappings,
    and append new examples to the corrections table for LLM few-shot context.
    Returns a summary dict.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    human_rows = conn.execute("""
        SELECT merchant, description, type, category, subcategory
        FROM transactions
        WHERE labelling_source = 'human'
          AND merchant IS NOT NULL AND merchant != ''
          AND type IS NOT NULL
    """).fetchall()

    # Existing corrections to avoid duplicates
    existing = set(
        (r[0], r[1])
        for r in conn.execute("SELECT merchant, description FROM corrections").fetchall()
    )

    rules = load_rules()
    rules_updated = 0
    corrections_added = 0

    for row in human_rows:
        merchant = row['merchant']
        key = merchant.lower().strip()

        # Update rules.json
        new_entry = {
            'type': row['type'],
            'category': row['category'],
            'subcategory': row['subcategory'],
        }
        if rules.get(key) != new_entry:
            rules[key] = new_entry
            rules_updated += 1

        # Append to corrections table if not already present
        pair = (merchant, row['description'])
        if pair not in existing:
            conn.execute("""
                INSERT INTO corrections (merchant, description, type, category, subcategory)
                VALUES (?, ?, ?, ?, ?)
            """, (merchant, row['description'], row['type'], row['category'], row['subcategory']))
            existing.add(pair)
            corrections_added += 1

    save_rules(rules)
    conn.commit()
    conn.close()

    return {'rules_updated': rules_updated, 'corrections_added': corrections_added}
