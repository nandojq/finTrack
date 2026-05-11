# FinTrack

Personal finance data pipeline with a Streamlit review UI. Ingests KBC bank CSV exports, auto-labels transactions using a hybrid rules + local LLM engine, and outputs a clean SQLite database queryable by Claude.

---

## How it works

```
KBC CSV export → ingest → deduplicate → auto-label (rules → Ollama LLM) → SQLite DB → Streamlit UI
```

1. Import a KBC CSV export via the sidebar
2. Transactions are auto-labelled: known merchants via `rules.json`, unknown ones via a local Ollama model
3. Review and correct labels in the UI — one click per transaction
4. Press "Learn" — corrections update `rules.json` and the LLM few-shot context for next time
5. The resulting `fintrack.db` is clean and queryable by Claude or any SQL tool

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally with `llama3.2` (or configure another model in `.env`)

---

## Setup

```bash
# 1. Clone and install dependencies
pip install -r requirements.txt

# 2. Configure your account details
cp .env.example .env
# Edit .env — set CHECKING_ACCOUNT and OWN_NAME_VARIANTS

# 3. Start Ollama (required for LLM labelling)
ollama serve
ollama pull llama3.2

# 4. Run the app
streamlit run src/app.py
```

---

## Configuration

All personal and environment-specific config lives in `.env` (gitignored):

| Variable | Description | Default |
|----------|-------------|---------|
| `CHECKING_ACCOUNT` | Your KBC IBAN (checking account) | — |
| `OWN_NAME_VARIANTS` | Comma-separated name variants as they appear in the bank | — |
| `OLLAMA_URL` | Ollama API endpoint | `http://localhost:11434/api/generate` |
| `OLLAMA_MODEL` | Model to use | `llama3.2` |
| `CONFIDENCE_THRESHOLD` | Minimum LLM confidence to avoid red flag | `0.75` |

---

## Importing data

1. Export a CSV from KBC (current or savings account)
2. Open the app (`streamlit run app.py`)
3. Drag the CSV into the sidebar uploader
4. Review any red-flagged (low confidence) transactions
5. Press "Learn from corrections" when done

The same CSV can be re-imported safely — duplicates are detected and skipped.

---

## Specification

Full spec lives in `docs/`:

| File | Contents |
|------|---------|
| `docs/spec.md` | Architecture, labelling engine, data sources, phases |
| `docs/taxonomy.md` | Category taxonomy with labelling rules |
| `docs/database-schema.md` | Schema + example SQL queries |
| `docs/ui-spec.md` | Streamlit UI specification |
| `docs/design-system.md` | Visual design tokens and rules |
