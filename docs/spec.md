# FinTrack — System Specification

## Goal

A personal finance data tool. Core job: ingest KBC bank CSV exports, auto-label transactions, and make it fast and intuitive to manually review and correct labels.

The output is a clean, well-structured SQLite database — queryable directly by Claude or any other model for financial analysis, scenario planning, and spending insights.

**Done means:** every month, run one import, do a quick correction pass in the UI, press "Learn", and the database is clean, accurate, and ready to query.

---

## Architecture

```
KBC CSV Export (one or more accounts)
        ↓
  [ src/ingest.py ]
  Parse → Normalise → Deduplicate
        ↓
  [ src/labeller.py ]
  rules.json cache → Ollama LLM fallback (+ few-shot corrections context)
        ↓
  fintrack.db (SQLite)
        ↓
  [ src/app.py — Streamlit UI ]
  Import · Transaction table · Row detail + relabelling · Learn
        ↓
  Clean database → queryable by Claude / any LLM
```

---

## File Structure

```
fintrack/
├── src/
│   ├── app.py          # Streamlit UI — single entrypoint
│   ├── ingest.py       # KBC CSV parser, normaliser, deduplicator, DB writer
│   ├── labeller.py     # Labelling engine: rules cache → Ollama LLM fallback
│   ├── learner.py      # "Learn" process: update rules.json + corrections table
│   └── config.py       # Taxonomy, Ollama config, paths — loads from .env
├── docs/               # Full specification (this folder)
├── rules.json          # Merchant → type/category/subcategory cache
├── .env                # Secrets and personal config (never committed)
└── fintrack.db         # SQLite database (gitignored, local only)
```

---

## Labelling Engine

Three-layer waterfall applied on every import. See `docs/taxonomy.md` for the full category list.

### Layer 1 — Rules Cache
`rules.json` maps known merchant keys to `{type, category, subcategory}`. Matched against the lowercased, trimmed merchant name using two passes:
1. **Exact match** — key equals merchant name exactly
2. **Prefix match** — key starts with merchant name, or merchant name starts with key (bidirectional)

Instant and deterministic for all recurring transactions.
- `labelling_source = 'rule'`
- `confidence = null`
- `reviewed = 1` (rules are pre-trusted; no human sign-off needed)

### Layer 2 — Ollama LLM Fallback
For unmatched transactions, sends to local Ollama model with:
- Full category taxonomy
- Recent examples from `corrections` table as few-shot context
- Transaction details (merchant, amount, description)

Returns: `{type, category, subcategory, confidence}`.
- `labelling_source = 'llm'`
- `reviewed = 0`
- Transactions below `CONFIDENCE_THRESHOLD` are flagged red in the UI

**If Ollama is unreachable:** the transaction is inserted with all label fields `NULL` and `labelling_source = NULL`. It appears red in the UI. To label it, start Ollama (`ollama serve`) and re-import the same CSV — existing rows are skipped by dedup, unlabelled rows are picked up and labelled.

### Layer 3 — Human Review
User clicks any row in the app → one-click relabel → immediate save.
- `labelling_source = 'human'`
- `reviewed = true`

### Learning Loop
After a correction session, "Learn from corrections" triggers:
1. **Rules cache update:** every human-corrected merchant key is added/overwritten in `rules.json`
2. **Few-shot bank update:** new `(merchant, description)` pairs from human corrections are appended to the `corrections` table → the 20 most recent are injected into every Ollama prompt

No model retraining. The LLM gets smarter through better context.

**Note — stale corrections:** the few-shot bank deduplicates on `(merchant, description)`. If a merchant was labelled incorrectly and then corrected, the old wrong entry remains in the `corrections` table if it had the same description. This is a known limitation — it can cause conflicting few-shot examples for the same merchant. Mitigated by the rules cache (which always reflects the latest correct label) taking priority over the LLM.

---

## Data Sources

| Source | Status | Notes |
|--------|--------|-------|
| KBC current account | Supported | Latin-1, semicolon-separated CSV |
| KBC savings accounts | Supported | Same format; auto-typed as Transfer / Savings Deposit |
| Revolut | Future | Different CSV format — parser to be added |
| Edenred (meal vouchers) | Future | Track spending side only as Expense / Food & Drinks |

---

## Implementation Phases

### Phase 1 — Data pipeline
- [x] `config.py` — taxonomy, Ollama config, confidence threshold, account name map
- [x] `ingest.py` — KBC CSV parser, merchant name cleaner, deduplicator, SQLite writer
- [x] `rules.json` — seed with common Belgian merchants
- [x] `labeller.py` — rules cache lookup → Ollama LLM fallback with few-shot context
- [x] DB schema — create `transactions` + `corrections` tables
- [x] End-to-end test: real KBC CSV → clean labelled SQLite table

### Phase 2 — Streamlit UI
- [x] `app.py` — Import button + CSV pipeline trigger
- [x] Transaction table with colour coding + filters
- [x] Row detail panel with quick-relabel buttons
- [x] `learner.py` — Learn button logic (rules.json update + corrections table)
- [ ] End-to-end test: import → review → correct → learn → re-import same file (check dedup)

---

## Notes

- **Ollama must be running locally** before the labeller works (`ollama serve`). Recommended model: `llama3.2`.
- **Deduplication key** is a hash of date + amount + merchant + reference — prevents re-importing the same transactions from overlapping CSV exports.
- **The database is the product.** Once clean, it can be handed directly to Claude for open-ended queries: spending analysis, outlier detection, sabbatical scenario modelling, etc.
- **No analytics dashboard.** FinTrack's job ends at a clean database. Analysis happens outside via Claude or SQL.
