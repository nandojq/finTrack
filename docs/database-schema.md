# FinTrack — Database Schema

SQLite database at `fintrack.db` (gitignored — local only).

---

## `transactions` table

Primary data store. One row per unique bank transaction.

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | SHA-256 hash of `date\|amount\|merchant\|reference` — deduplication key |
| `date` | DATE | Transaction date (YYYY-MM-DD) |
| `amount` | REAL | Negative = outflow, positive = inflow |
| `description` | TEXT | Raw bank description text |
| `merchant` | TEXT | Parsed/cleaned merchant name |
| `account` | TEXT | KBC account identifier (IBAN) |
| `type` | TEXT | `Income` / `Expense` / `Transfer` / `Financial Obligation` |
| `category` | TEXT | e.g. `Food & Drinks` |
| `subcategory` | TEXT | e.g. `Restaurants` |
| `confidence` | REAL | LLM confidence score 0.0–1.0; `null` if rule-matched |
| `labelling_source` | TEXT | `rule` / `llm` / `human` / `null` (unlabelled) |
| `reviewed` | BOOLEAN | `1` once human has confirmed or corrected |
| `import_batch` | TEXT | Source CSV filename + import timestamp |

### Deduplication

The `id` hash prevents re-importing the same transaction when CSV exports overlap in date range. `INSERT OR IGNORE` is used on every row — safe to re-import the same file.

### Colour coding in UI

| `labelling_source` | `confidence` | UI colour |
|--------------------|-------------|-----------|
| `human` | any | Green |
| `rule` | null | Blue |
| `llm` | ≥ threshold | Yellow |
| `llm` | < threshold or null | Red |
| `null` | null | Red |

---

## `corrections` table

Few-shot example bank for the LLM. Populated by the "Learn" button.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `merchant` | TEXT | Merchant key |
| `description` | TEXT | Raw description example |
| `type` | TEXT | Correct type |
| `category` | TEXT | Correct category |
| `subcategory` | TEXT | Correct subcategory |
| `created_at` | DATETIME | When the correction was recorded |

The 20 most recent corrections are injected into every Ollama prompt as few-shot context. This means the LLM improves with use without any model retraining.

---

## Querying the database

```sql
-- All expenses this month, by category
SELECT category, subcategory, SUM(amount) as total
FROM transactions
WHERE type = 'Expense'
  AND date >= '2026-05-01' AND date < '2026-06-01'
GROUP BY category, subcategory
ORDER BY total ASC;

-- Unreviewed low-confidence transactions
SELECT merchant, amount, category, confidence
FROM transactions
WHERE labelling_source = 'llm'
  AND (confidence IS NULL OR confidence < 0.75)
  AND reviewed = 0
ORDER BY date DESC;

-- Monthly spend trend
SELECT strftime('%Y-%m', date) as month, SUM(amount) as net
FROM transactions
WHERE type = 'Expense'
GROUP BY month
ORDER BY month DESC;
```
