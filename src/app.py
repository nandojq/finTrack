import sqlite3
from datetime import date, timedelta
from pathlib import Path
import tempfile

import pandas as pd
import streamlit as st

from config import CATEGORY_TO_TYPE, CONFIDENCE_THRESHOLD, DB_PATH, TAXONOMY
from ingest import ingest_csv
from labeller import label_new_transactions, relabel_transaction
from learner import run_learn

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="FinTrack",
    page_icon="💶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design tokens — Dieter Rams palette
# See docs/design-system.md for the full specification.
# ---------------------------------------------------------------------------

C = {
    # Backgrounds
    "bg":          "#EDEBE6",   # --color-surface (main background)
    "surface":     "#F5F4F0",   # --color-white (card / widget background)
    "surface_alt": "#E2E0DA",   # --color-surface-alt (sidebar, inset areas)
    # Borders
    "border":      "#C8C5BC",   # --color-border
    # Text
    "text":        "#1A1916",   # --color-text
    "text_sub":    "#5C5A55",   # --color-text-sub
    "mid":         "#8C8982",   # --color-mid
    "black":       "#0F0E0C",   # --color-black
    # Accent — ONE element per view (Learn button only)
    "accent":      "#D4A017",   # --color-accent
    # State
    "success":     "#3A6B45",   # --color-success
    "error":       "#8B2E2E",   # --color-error
    "disabled":    "#BFBDB8",   # --color-disabled
    # Row colour coding — light tints of state colours
    "row_human":   "#EBF2EC",   # success tint
    "row_rule":    "#E8E6E0",   # neutral (surface-alt variant)
    "row_llm_hi":  "#FAF3DC",   # accent tint
    "row_llm_lo":  "#F5EAEA",   # error tint
}

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600&family=DM+Mono:wght@400;500&display=swap');

  /* ── Base ── */
  html, body, [class*="css"], .stApp {{
    font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    background-color: {C["bg"]} !important;
    color: {C["text"]} !important;
  }}
  [data-testid="stAppViewContainer"],
  [data-testid="stAppViewBlockContainer"],
  section.main, .main > div {{
    background-color: {C["bg"]} !important;
  }}
  p, span, li, label, div {{ color: {C["text"]}; }}

  /* ── Sidebar ── */
  [data-testid="stSidebar"],
  [data-testid="stSidebar"] > div {{
    background: {C["surface_alt"]} !important;
    border-right: 1px solid {C["border"]} !important;
  }}
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span,
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] div,
  [data-testid="stSidebar"] li {{ color: {C["text"]} !important; }}
  [data-testid="stSidebar"] h1 {{
    font-family: 'DM Sans', sans-serif !important;
    color: {C["black"]} !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    margin-bottom: 0;
  }}
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3 {{
    font-family: 'DM Sans', sans-serif !important;
    color: {C["mid"]} !important;
    font-size: 0.64rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 24px;
    margin-bottom: 4px;
  }}
  [data-testid="stSidebar"] hr {{ border-color: {C["border"]} !important; }}
  [data-testid="stSidebar"] [data-baseweb="tag"] {{
    background-color: {C["surface"]} !important;
    color: {C["text"]} !important;
    border-radius: 2px !important;
    border: 1px solid {C["border"]} !important;
  }}
  [data-testid="stSidebar"] [data-baseweb="tag"] span {{ color: {C["text"]} !important; }}

  /* ── Cards ── */
  .dr-card {{
    background: {C["surface"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
    padding: 20px 24px;
    margin-bottom: 12px;
  }}
  .dr-card-raised {{
    background: {C["surface"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
    padding: 20px 24px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(15,14,12,0.08);
  }}

  /* ── Metric cards ── */
  [data-testid="stMetric"] {{
    background: {C["surface"]} !important;
    border: 1px solid {C["border"]} !important;
    border-radius: 4px !important;
    padding: 16px 20px !important;
    box-shadow: none !important;
  }}
  [data-testid="stMetricLabel"] p {{
    font-size: 0.64rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: {C["mid"]} !important;
  }}
  [data-testid="stMetricValue"] div {{
    font-family: 'DM Mono', 'Courier New', monospace !important;
    font-size: 1.563rem !important;
    font-weight: 400 !important;
    color: {C["black"]} !important;
  }}

  /* ── Headings ── */
  h1, h2, h3, h4 {{
    font-family: 'DM Sans', sans-serif !important;
    color: {C["black"]} !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em !important;
  }}
  h1 {{ font-size: 1.953rem !important; }}
  h2 {{ font-size: 1.25rem !important; letter-spacing: 0 !important; }}
  h3 {{ font-size: 1rem !important; }}

  /* ── Section label (eyebrow) ── */
  .section-label {{
    font-size: 0.64rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    color: {C["mid"]} !important;
    margin-bottom: 8px;
  }}

  /* ── Dividers ── */
  hr {{
    border: none !important;
    border-top: 1px solid {C["border"]} !important;
    margin: 24px 0 !important;
  }}

  /* ── Buttons — secondary (default) ── */
  .stButton > button {{
    background: transparent !important;
    color: {C["text"]} !important;
    border: 1.5px solid {C["border"]} !important;
    border-radius: 3px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.01em !important;
    text-transform: none !important;
    padding: 8px 20px !important;
    box-shadow: none !important;
    transition: border-color 120ms ease, background 120ms ease !important;
  }}
  .stButton > button:hover {{
    border-color: {C["black"]} !important;
    background: {C["surface_alt"]} !important;
    color: {C["black"]} !important;
    box-shadow: none !important;
  }}

  /* ── Learn button — accent (ONE per view) ── */
  .learn-btn .stButton > button {{
    background: {C["accent"]} !important;
    color: {C["black"]} !important;
    border-color: {C["accent"]} !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 10px 24px !important;
  }}
  .learn-btn .stButton > button:hover {{
    filter: brightness(0.92) !important;
    background: {C["accent"]} !important;
    border-color: {C["accent"]} !important;
    color: {C["black"]} !important;
  }}

  /* ── Relabel button grid ── */
  .relabel-grid .stButton > button {{
    background: transparent !important;
    color: {C["text"]} !important;
    border: 1.5px solid {C["border"]} !important;
    border-radius: 3px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 400 !important;
    padding: 6px 10px !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    box-shadow: none !important;
    width: 100%;
  }}
  .relabel-grid .stButton > button:hover {{
    border-color: {C["black"]} !important;
    background: {C["surface_alt"]} !important;
    color: {C["black"]} !important;
  }}

  /* ── Expanders ── */
  [data-testid="stExpander"] {{
    background: {C["surface"]} !important;
    border: 1px solid {C["border"]} !important;
    border-radius: 4px !important;
    box-shadow: none !important;
    margin-bottom: 8px !important;
  }}
  [data-testid="stExpander"] summary p,
  [data-testid="stExpander"] p {{
    color: {C["text"]} !important;
    font-weight: 400;
    font-size: 0.875rem;
  }}

  /* ── DataFrames ── */
  [data-testid="stDataFrame"] {{
    border-radius: 4px !important;
    border: 1px solid {C["border"]} !important;
    background: {C["surface"]} !important;
    box-shadow: none !important;
  }}

  /* ── Alerts ── */
  [data-testid="stAlert"] {{
    border-radius: 4px !important;
    border: 1px solid {C["border"]} !important;
    border-left: 3px solid {C["accent"]} !important;
    background: {C["surface"]} !important;
    box-shadow: none !important;
  }}
  [data-testid="stAlert"] p {{ color: {C["text"]} !important; }}

  /* ── Form widget labels — eyebrow style ── */
  [data-testid="stRadio"] label p,
  [data-testid="stSelectbox"] label p,
  [data-testid="stMultiSelect"] label p,
  [data-testid="stDateInput"] label p,
  [data-testid="stFileUploader"] label p,
  [data-testid="stToggle"] label p {{
    font-size: 0.64rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    color: {C["mid"]} !important;
  }}

  /* ── Multiselect tags ── */
  [data-baseweb="tag"] {{
    background-color: {C["surface"]} !important;
    color: {C["text"]} !important;
    border-radius: 2px !important;
    border: 1px solid {C["border"]} !important;
  }}
  [data-baseweb="tag"] span {{ color: {C["text"]} !important; }}

  /* ── File uploader ── */
  [data-testid="stFileUploader"] section {{
    border: 1.5px dashed {C["border"]} !important;
    border-radius: 4px !important;
    background: {C["surface_alt"]} !important;
  }}
  [data-testid="stSidebar"] [data-testid="stFileUploader"] p,
  [data-testid="stSidebar"] [data-testid="stFileUploader"] span,
  [data-testid="stSidebar"] [data-testid="stFileUploader"] small,
  [data-testid="stSidebar"] [data-testid="stFileUploader"] div {{
    color: {C["text"]} !important;
  }}

  /* ── Status badge (legend chips) ── */
  .legend-chip {{
    display: inline-flex;
    align-items: center;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.64rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 2px;
    border: 1px solid currentColor;
    margin-right: 8px;
    margin-bottom: 4px;
  }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data(ttl=15)
def load_transactions() -> pd.DataFrame:
    try:
        conn = get_conn()
        df = pd.read_sql(
            "SELECT * FROM transactions ORDER BY date DESC, rowid DESC",
            conn, parse_dates=['date'],
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=15)
def db_stats() -> dict:
    try:
        conn = get_conn()
        row = conn.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN labelling_source IS NOT NULL THEN 1 ELSE 0 END) AS labelled,
                SUM(CASE WHEN labelling_source = 'human' THEN 1 ELSE 0 END) AS human,
                MAX(import_batch) AS last_batch
            FROM transactions
        """).fetchone()
        conn.close()
        total = row[0] or 0
        labelled = row[1] or 0
        return {
            'total': total,
            'labelled': labelled,
            'human': row[2] or 0,
            'pct_labelled': round(labelled / total * 100, 1) if total else 0,
            'last_batch': row[3] or '—',
        }
    except Exception:
        return {'total': 0, 'labelled': 0, 'human': 0, 'pct_labelled': 0, 'last_batch': '—'}


def invalidate_cache():
    st.cache_data.clear()


# ---------------------------------------------------------------------------
# Row colour coding
# ---------------------------------------------------------------------------

def _row_colour(row: pd.Series) -> list[str]:
    src = row.get('labelling_source') or ''
    conf = row.get('confidence')
    if src == 'human':
        bg = C["row_human"]
    elif src == 'rule':
        bg = C["row_rule"]
    elif src == 'llm':
        bg = C["row_llm_hi"] if (conf is not None and conf >= CONFIDENCE_THRESHOLD) else C["row_llm_lo"]
    else:
        bg = C["row_llm_lo"]
    return [f'background-color: {bg}; color: {C["text"]}'] * len(row)


def style_table(df: pd.DataFrame) -> object:
    return df.style.apply(_row_colour, axis=1).format(
        {'amount': '€ {:.2f}', 'confidence': lambda x: f'{x:.2f}' if pd.notna(x) else '—'},
        na_rep='—',
    )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("FinTrack")

    stats = db_stats()
    st.caption(f"**{stats['total']}** transactions · **{stats['pct_labelled']}%** labelled")
    if stats['last_batch'] != '—':
        st.caption(f"Last import: {stats['last_batch'][:30]}")

    st.divider()

    st.subheader("Import")
    uploaded = st.file_uploader("KBC CSV export", type="csv", label_visibility="collapsed")

    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            tmp.write(uploaded.getbuffer())
            tmp_path = tmp.name

        with st.spinner("Importing…"):
            r = ingest_csv(tmp_path)
        st.success(f"{r['inserted']} new · {r['skipped']} skipped")

        with st.spinner("Labelling…"):
            lr = label_new_transactions()
        st.success(f"{lr['labelled']} labelled ({lr['rule']} rule · {lr['llm']} LLM)")

        invalidate_cache()
        Path(tmp_path).unlink(missing_ok=True)
        st.rerun()

    st.divider()
    st.subheader("Filters")

    today = date.today()
    try:
        conn = get_conn()
        earliest = conn.execute("SELECT MIN(date) FROM transactions").fetchone()[0]
        conn.close()
        default_from = date.fromisoformat(earliest) if earliest else today.replace(day=1)
    except Exception:
        default_from = today.replace(day=1)
    date_from = st.date_input("From", value=default_from)
    date_to   = st.date_input("To",   value=today)

    all_types = list(TAXONOMY.keys())
    sel_types = st.multiselect("Type", all_types, default=all_types)

    all_srcs = ['rule', 'llm', 'human', '(unlabelled)']
    sel_srcs = st.multiselect("Source", all_srcs, default=all_srcs)

    show_unreviewed = st.toggle("Unreviewed only", value=False)


# ---------------------------------------------------------------------------
# Main — KPI strip
# ---------------------------------------------------------------------------

stats = db_stats()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Transactions", f"{stats['total']:,}")
k2.metric("Labelled", f"{stats['pct_labelled']}%")
k3.metric("Human-reviewed", f"{stats['human']:,}")

try:
    conn = get_conn()
    lo_conf = conn.execute("""
        SELECT COUNT(*) FROM transactions
        WHERE labelling_source = 'llm' AND (confidence IS NULL OR confidence < ?)
    """, (CONFIDENCE_THRESHOLD,)).fetchone()[0]
    conn.close()
except Exception:
    lo_conf = 0
k4.metric("Needs attention", f"{lo_conf:,}")

st.divider()

# ---------------------------------------------------------------------------
# Colour legend — status badge style
# ---------------------------------------------------------------------------

st.markdown(
    f'<span class="legend-chip" style="color:{C["success"]};background:{C["row_human"]}">Human</span>'
    f'<span class="legend-chip" style="color:{C["text_sub"]};background:{C["row_rule"]};border-color:{C["border"]}">Rule</span>'
    f'<span class="legend-chip" style="color:#7A5800;background:{C["row_llm_hi"]};border-color:{C["accent"]}">LLM · high conf</span>'
    f'<span class="legend-chip" style="color:{C["error"]};background:{C["row_llm_lo"]}">LLM · low conf</span>',
    unsafe_allow_html=True,
)
st.markdown("<div style='margin-bottom:16px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Transaction table
# ---------------------------------------------------------------------------

df_all = load_transactions()

if df_all.empty:
    st.info("No transactions yet. Import a KBC CSV export using the sidebar.")
    st.stop()

# Apply filters
df = df_all.copy()
if 'date' in df.columns:
    df = df[(df['date'].dt.date >= date_from) & (df['date'].dt.date <= date_to)]

if sel_types:
    df = df[df['type'].isin(sel_types) | df['type'].isna()]

if sel_srcs:
    src_vals = [s for s in sel_srcs if s != '(unlabelled)']
    include_null = '(unlabelled)' in sel_srcs
    if include_null:
        df = df[df['labelling_source'].isin(src_vals) | df['labelling_source'].isna()]
    else:
        df = df[df['labelling_source'].isin(src_vals)]

if show_unreviewed:
    df = df[df['reviewed'] == 0]

display_cols = ['date', 'merchant', 'amount', 'type', 'category', 'subcategory',
                'labelling_source', 'confidence', 'reviewed']
available = [c for c in display_cols if c in df.columns]
view_df = df[available].copy().reset_index(drop=True)

st.markdown(f"<p class='section-label'>{len(view_df)} transactions</p>", unsafe_allow_html=True)

event = st.dataframe(
    style_table(view_df),
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        'date':             st.column_config.DateColumn('Date',        width='small'),
        'merchant':         st.column_config.TextColumn('Merchant',    width='medium'),
        'amount':           st.column_config.NumberColumn('Amount',    format='€ %.2f', width='small'),
        'type':             st.column_config.TextColumn('Type',        width='small'),
        'category':         st.column_config.TextColumn('Category',    width='medium'),
        'subcategory':      st.column_config.TextColumn('Subcategory', width='medium'),
        'labelling_source': st.column_config.TextColumn('Source',      width='small'),
        'confidence':       st.column_config.NumberColumn('Conf.',     format='%.2f', width='small'),
        'reviewed':         st.column_config.CheckboxColumn('✓',       width='small'),
    },
    key="tx_table",
)

selected_rows = event.selection.rows

# ---------------------------------------------------------------------------
# Row detail + relabelling panel
# ---------------------------------------------------------------------------

if selected_rows:
    idx = selected_rows[0]
    row = view_df.iloc[idx]

    # Reconstruct the full filtered df (with id column) to get tx_id and account
    df_with_id = df_all.copy()
    if 'date' in df_with_id.columns:
        df_with_id = df_with_id[(df_with_id['date'].dt.date >= date_from) & (df_with_id['date'].dt.date <= date_to)]
    if sel_types:
        df_with_id = df_with_id[df_with_id['type'].isin(sel_types) | df_with_id['type'].isna()]
    if sel_srcs:
        src_vals2 = [s for s in sel_srcs if s != '(unlabelled)']
        include_null2 = '(unlabelled)' in sel_srcs
        if include_null2:
            df_with_id = df_with_id[df_with_id['labelling_source'].isin(src_vals2) | df_with_id['labelling_source'].isna()]
        else:
            df_with_id = df_with_id[df_with_id['labelling_source'].isin(src_vals2)]
    if show_unreviewed:
        df_with_id = df_with_id[df_with_id['reviewed'] == 0]
    df_with_id = df_with_id.reset_index(drop=True)

    tx_id = df_with_id.iloc[idx]['id'] if idx < len(df_with_id) and 'id' in df_with_id.columns else None
    full  = df_with_id.iloc[idx] if idx < len(df_with_id) else {}

    st.divider()
    st.markdown("### Transaction detail")

    with st.container():
        col_info, col_relabel = st.columns([1, 2])

        with col_info:
            st.markdown('<div class="dr-card">', unsafe_allow_html=True)
            st.markdown(f"**Merchant:** {row.get('merchant', '—')}")
            st.markdown(f"**Date:** {row.get('date', '—')}")
            st.markdown(f"**Amount:** €{row.get('amount', 0):.2f}")
            st.markdown(f"**Account:** {full.get('account', '—')}")
            if 'description' in df_with_id.columns and idx < len(df_with_id):
                st.markdown(f"**Description:** {str(full.get('description', '—'))[:120]}")
            src  = row.get('labelling_source') or 'none'
            conf = row.get('confidence')
            conf_str = f" · conf {conf:.2f}" if pd.notna(conf) else ''
            st.markdown(f"**Label:** {row.get('type', '—')} / {row.get('category', '—')} / {row.get('subcategory', '—')}")
            st.markdown(f"**Source:** `{src}`{conf_str}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_relabel:
            if tx_id:
                st.markdown('<div class="dr-card-raised">', unsafe_allow_html=True)
                st.markdown('<p class="section-label">Relabel</p>', unsafe_allow_html=True)

                sel_type = st.radio(
                    "Type", list(TAXONOMY.keys()),
                    index=list(TAXONOMY.keys()).index(row.get('type')) if row.get('type') in TAXONOMY else 0,
                    horizontal=True,
                    key="relabel_type",
                    label_visibility="collapsed",
                )

                cats = TAXONOMY[sel_type]
                st.markdown(
                    f"<p style='font-size:0.8rem;color:{C['mid']};margin-top:8px;margin-bottom:4px'>"
                    "Select subcategory</p>",
                    unsafe_allow_html=True,
                )

                st.markdown('<div class="relabel-grid">', unsafe_allow_html=True)
                for cat, subcats in cats.items():
                    st.markdown(
                        f"<p style='font-size:0.64rem;font-weight:500;letter-spacing:0.08em;"
                        f"text-transform:uppercase;margin:12px 0 4px;color:{C['mid']}'>{cat}</p>",
                        unsafe_allow_html=True,
                    )
                    btn_cols = st.columns(min(len(subcats), 3))
                    for i, sub in enumerate(subcats):
                        with btn_cols[i % len(btn_cols)]:
                            if st.button(sub, key=f"btn_{sel_type}_{cat}_{sub}"):
                                relabel_transaction(tx_id, sel_type, cat, sub)
                                st.session_state['has_corrections'] = True
                                invalidate_cache()
                                st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Learn button — accent, ONE per view
# ---------------------------------------------------------------------------

st.divider()

has_human = stats['human'] > 0 or st.session_state.get('has_corrections', False)

if has_human:
    st.markdown("### Learn from corrections")
    st.markdown(
        f"<p style='color:{C['text_sub']};font-size:0.875rem;margin-bottom:16px'>"
        "Update rules.json and the few-shot corrections bank with all human-labelled transactions.</p>",
        unsafe_allow_html=True,
    )
    col_learn, _ = st.columns([1, 4])
    with col_learn:
        st.markdown('<div class="learn-btn">', unsafe_allow_html=True)
        if st.button("Learn from corrections", key="learn_btn"):
            with st.spinner("Learning…"):
                result = run_learn()
            st.success(
                f"Done — {result['rules_updated']} rules updated · "
                f"{result['corrections_added']} examples added to few-shot bank"
            )
            st.session_state['has_corrections'] = False
            invalidate_cache()
        st.markdown('</div>', unsafe_allow_html=True)
