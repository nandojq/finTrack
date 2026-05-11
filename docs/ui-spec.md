# FinTrack — UI Specification

Streamlit app (`app.py`). Single-page layout with sidebar controls.

---

## Sidebar

### Import panel
- File uploader — accepts KBC CSV export (`.csv`)
- On upload: parse → normalise → deduplicate → label → insert → show summary
  - Summary: N new transactions, N duplicates skipped, N labelled by rule, N by LLM, N low-confidence
- Supports multiple KBC accounts (checking, savings). Savings account transactions auto-typed as Transfer / Savings Deposit at ingest time.

### Filters
- **Period:** date range picker (From / To), defaults to previous full month
- **Type:** multi-select of all transaction types
- **Source:** multi-select of `rule` / `llm` / `human` / `(unlabelled)`
- **Reviewed toggle:** show unreviewed only

---

## Main area

### KPI strip (top)
Four metric cards:
- Total transactions in DB
- % labelled
- Human-reviewed count
- Needs attention (LLM low-confidence count)

### Colour legend
Inline chips explaining row colour coding:
- Green = Human-corrected
- Blue = Rule-matched
- Yellow = LLM high-confidence
- Red = LLM low-confidence / unlabelled

### Transaction table
Full filtered dataset as a styled dataframe. Columns:

| Column | Display |
|--------|---------|
| date | Date |
| merchant | Merchant |
| amount | Amount (€) |
| type | Type |
| category | Category |
| subcategory | Subcategory |
| labelling_source | Source |
| confidence | Conf. |
| reviewed | ✓ |

Row colour coding applied per `labelling_source` and `confidence`. See `docs/database-schema.md`.

Clicking a row opens the row detail panel below.

---

## Row detail panel

Shown below the table when a row is selected. Two columns:

### Left — Info card
- Merchant, date, amount, account
- Raw description (truncated to 120 chars)
- Current label: type / category / subcategory
- Source badge + confidence

### Right — Relabel card
- Type radio (Income / Expense / Transfer / Financial Obligation)
- Category grid: for the selected type, all categories shown as section labels
- Subcategory buttons: one click to relabel immediately
- On click: `UPDATE transactions SET ... labelling_source='human', reviewed=1 WHERE id=?`
- Cache cleared, table reruns

---

## Learn button

Shown at the bottom when either:
- The DB contains at least one human-labelled transaction (`stats['human'] > 0`), **or**
- A correction was made in the current session (`has_corrections` session state flag)

The session flag ensures the button appears immediately after the first correction without waiting for the stats cache to refresh.

On click:
1. Scan all `labelling_source = 'human'` transactions
2. Update `rules.json` with new/corrected merchant → label mappings
3. Append new entries to `corrections` table
4. Display summary: N rules updated, N corrections added to few-shot bank

---

## Design system

See `docs/design-system.md` for the full token set and visual rules (Dieter Rams–inspired palette, typography, spacing, components).
