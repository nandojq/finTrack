# CLAUDE.md — FinTrack

Instruction set for Claude Code working on this project. Keep the Session Log updated after every task.

---

## Quick orientation

**FinTrack** is a personal finance data pipeline with a Streamlit review UI. It ingests KBC bank CSV exports, auto-labels transactions (rules cache → Ollama LLM), and outputs a clean SQLite database queryable by Claude.

**There is no analytics layer.** The database is the product.

Full specification lives in `docs/`:
- `docs/spec.md` — architecture, file structure, labelling engine, data sources, implementation phases
- `docs/taxonomy.md` — full category taxonomy with labelling rules
- `docs/database-schema.md` — schema for `transactions` and `corrections` tables, with example queries
- `docs/ui-spec.md` — Streamlit UI specification (import, table, row detail, learn button)
- `docs/design-system.md` — Dieter Rams–inspired visual tokens and rules

---

## Architecture (summary)

```
KBC CSV Export
      ↓
 src/ingest.py → normalise → deduplicate → DB insert
      ↓
 src/labeller.py → rules.json cache → Ollama LLM fallback (few-shot corrections)
      ↓
 fintrack.db (SQLite)
      ↓
 src/app.py (Streamlit) → table view → row detail → relabel → Learn button
      ↓
 src/learner.py → update rules.json + corrections table
```

---

## Key constraints

- **Sensitive config in `.env` only** — account numbers and name variants are never hardcoded. `.env` is gitignored.
- **`fintrack.db` is gitignored** — local only, never committed.
- **`data/` and `*.csv` are gitignored** — drag CSV exports into the Streamlit uploader, never commit them.
- **Ollama must be running** (`ollama serve`) before the labeller works.
- **`DB_PATH` and `RULES_PATH` are absolute** (resolved in `config.py` relative to `__file__`) — safe regardless of working directory.

---

## Current status

### Phase 1 — Data pipeline: complete
### Phase 2 — Streamlit UI: complete (end-to-end test pending)
- End-to-end test (import → correct → learn → re-import dedup check) not yet formally verified.

### Phase 3 — Future data sources
- Revolut CSV parser
- Edenred meal voucher support

---

## Session Log

> Format: `YYYY-MM-DD — what was built/changed/decided.`

- 2026-04-09 — Project spec finalised. Architecture, schema, taxonomy, UI spec, and labelling engine all locked.
- 2026-04-09 — Full rebuild complete. Phase 1 and Phase 2 built and tested. 213 rows imported from real KBC CSV, 81 rule-matched, 132 LLM-labelled. Dedup confirmed. CLAUDE.md written to repo root.
- 2026-05-11 — Repository hygiene pass. Sensitive config moved to `.env` (account number, name variants). `DB_PATH`/`RULES_PATH` made absolute. `.gitignore` fixed (added `fintrack.db`, `data/`, `*.csv`). Full spec migrated from Notion to `docs/` folder. `README.md` rewritten. `requirements.txt` pinned. Git history rewritten to remove committed bank data and sensitive config.
- 2026-05-11 — Spec review and bug fixes. Fixed: incoming self-transfers now `Transfer/Internal Transfer` (were `Income/Other Income`). Savings account withdrawals now `Internal Transfer` (were `Savings Deposit`). Rule-matched transactions now enter with `reviewed=1`. Account field in row detail panel fixed (was always showing `—`). Spec updated: `src/` paths in architecture diagram, category structure clarified in taxonomy, Ollama unreachable state documented, rules prefix-match algorithm documented, Learn button session state condition documented, stale corrections limitation documented, `reviewed` semantics table added.
- 2026-05-11 — Date display fix: stripped time component from date column in transaction table (`dt.date`). rules.json expanded with 360+ new merchant → label mappings from a labelling session.
