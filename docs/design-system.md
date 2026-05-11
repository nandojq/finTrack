# FinTrack — Design System

> *"Good design is as little design as possible."* — Dieter Rams

Rooted in the Ten Principles of Good Design. Every design decision must justify its existence. Nothing is decorative for decoration's sake. Everything serves function. Restraint is the highest form of sophistication.

**Core mandates:**
- Remove before you add
- Every element must earn its place
- Honesty over ornament
- Longevity over trend
- Clarity over cleverness

---

## 1. Color Palette

The palette is deliberately narrow. Neutrals dominate. Accent color is used sparingly — a signal, not decoration.

```css
:root {
  /* Neutrals */
  --color-white:        #F5F4F0;   /* Warm off-white, never pure white */
  --color-surface:      #EDEBE6;   /* Primary background */
  --color-surface-alt:  #E2E0DA;   /* Subtle card/section differentiation */
  --color-border:       #C8C5BC;   /* Dividers, outlines */
  --color-mid:          #8C8982;   /* Secondary text, placeholders */
  --color-text-sub:     #5C5A55;   /* Tertiary labels, captions */
  --color-text:         #1A1916;   /* Primary text — warm near-black */
  --color-black:        #0F0E0C;   /* True dark, used for headers and key UI */

  /* Functional Accent (Braun Yellow / Signal) */
  --color-accent:       #D4A017;   /* Warm amber-gold — used < 5% of UI surface */
  --color-accent-alt:   #E8640A;   /* Reserved for destructive or alert states */

  /* State Colors (minimal) */
  --color-success:      #3A6B45;
  --color-error:        #8B2E2E;
  --color-disabled:     #BFBDB8;
}
```

**Rules:**
- `--color-accent` appears on **one element per view** maximum — a single button, indicator, or icon
- Never use gradients. Never use shadows heavier than `0 1px 4px rgba(15,14,12,0.08)`
- Dark mode inverts the neutral stack; the accent remains warm

### Streamlit implementation

```python
C = {
    "bg":          "#EDEBE6",   # --color-surface (main background)
    "surface":     "#F5F4F0",   # --color-white (card background)
    "surface_alt": "#E2E0DA",   # --color-surface-alt (sidebar, inset areas)
    "border":      "#C8C5BC",   # --color-border
    "text":        "#1A1916",   # --color-text
    "text_sub":    "#5C5A55",   # --color-text-sub
    "mid":         "#8C8982",   # --color-mid
    "black":       "#0F0E0C",   # --color-black
    "accent":      "#D4A017",   # --color-accent (Learn button only)
    "success":     "#3A6B45",   # --color-success
    "error":       "#8B2E2E",   # --color-error
    "disabled":    "#BFBDB8",   # --color-disabled
    # Row colour coding — light tints of state colours
    "row_human":   "#EBF2EC",   # success tint
    "row_rule":    "#E8E6E0",   # neutral (surface-alt variant)
    "row_llm_hi":  "#FAF3DC",   # accent tint
    "row_llm_lo":  "#F5EAEA",   # error tint
}
```

### Row colour coding

| `labelling_source` | Condition | Background | Border/text colour |
|--------------------|-----------|------------|-------------------|
| `human` | any | `#EBF2EC` | `--color-success` |
| `rule` | any | `#E8E6E0` | `--color-border` |
| `llm` | ≥ threshold | `#FAF3DC` | `--color-accent` |
| `llm` / `null` | < threshold or null | `#F5EAEA` | `--color-error` |

---

## 2. Typography

One font family, used with extreme deliberateness.

```css
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600&family=DM+Mono:wght@400;500&display=swap');

:root {
  --font-body: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  --font-mono: 'DM Mono', 'Courier New', monospace;

  /* Type scale (Major Third — 1.250) */
  --text-xs:   0.64rem;    /*  ~10px — eyebrow labels, badges */
  --text-sm:   0.8rem;     /*  ~13px — captions, table data */
  --text-base: 1rem;       /*   16px — body */
  --text-md:   1.25rem;    /*   20px — subheadings */
  --text-lg:   1.563rem;   /*   25px — section headers */
  --text-xl:   1.953rem;   /*  ~31px — page titles */
  --text-2xl:  2.441rem;   /*   39px — display */
  --text-3xl:  3.052rem;   /* ~48px  — hero */

  /* Weights */
  --weight-light:    300;
  --weight-regular:  400;
  --weight-medium:   500;
  --weight-semibold: 600;
}
```

### Type roles

| Role | Size | Weight | Tracking | Usage |
|------|------|--------|----------|-------|
| `heading` | `--text-xl` | 500 | `-0.01em` | H1s, page titles |
| `subheading` | `--text-lg` | 400 | `0` | H2s, panel titles |
| `label` | `--text-sm` | 500 | `0.12em` | ALL CAPS labels, eyebrows |
| `body` | `--text-base` | 400 | `0` | Body text |
| `caption` | `--text-sm` | 400 | `0` | Metadata, secondary info |
| `mono` | `--text-sm` | 400 | `0` | Numbers in tables, code |

**Rules:**
- Maximum **two** type sizes visible on any single view
- Uppercase labels only for organizational labels — never body text
- Use `DM Mono` for all numeric data in tables (prevents column shifting)
- Headings: sentence case only — never Title Case For Every Word

---

## 3. Spacing System

Based on an **8px base unit**. All spacing values are multiples. No exceptions.

```css
:root {
  --space-1:   4px;    /* hairline gap */
  --space-2:   8px;    /* micro */
  --space-3:   12px;   /* small */
  --space-4:   16px;   /* base */
  --space-5:   24px;   /* medium */
  --space-6:   32px;   /* large */
  --space-7:   48px;   /* xl */
  --space-8:   64px;   /* 2xl */
}
```

**Rules:**
- Whitespace is **active**, not passive — it creates hierarchy
- Lean toward more space rather than less; the design breathes
- Never use negative margins to patch spacing failures

---

## 4. Components

### Buttons

Three types only. No ghost buttons with decorative borders.

```css
/* Secondary — default for supporting actions */
.btn--secondary {
  background: transparent;
  color: var(--color-text);
  border: 1.5px solid var(--color-border);
  border-radius: 3px;
  font-weight: 500;
  font-size: var(--text-base);
  letter-spacing: 0.01em;
  padding: 8px 20px;
  transition: border-color 120ms ease, background 120ms ease;
}
.btn--secondary:hover { border-color: var(--color-black); background: var(--color-surface-alt); }

/* Primary — filled dark, main action */
.btn--primary {
  background: var(--color-black);
  color: var(--color-white);
  border: 1.5px solid var(--color-black);
  border-radius: 3px;
}
.btn--primary:hover { background: var(--color-text); border-color: var(--color-text); }

/* Accent — signal action, ONE per view (Learn button) */
.btn--accent {
  background: var(--color-accent);
  color: var(--color-black);
  border: 1.5px solid var(--color-accent);
  font-weight: 600;
}
.btn--accent:hover { filter: brightness(0.92); }
```

**In FinTrack:**
- All buttons default to secondary (outlined)
- Learn button is the sole accent element per view
- Button labels: sentence case, verb + noun — `"Learn from corrections"`, not `"LEARN"`

### Cards

```css
.card {
  background: var(--color-white);   /* #F5F4F0 */
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: var(--space-5) var(--space-6);
}
/* Raised variant — use sparingly, only for elevated panels */
.card--raised {
  box-shadow: 0 1px 4px rgba(15,14,12,0.08);
}
```

**Rules:**
- Default state: border only, no shadow
- Shadow only for the raised variant (overlaid panels)
- Never stack shadows or use colored shadows
- Border radius: 4px (`--radius-md`) — never exceed 6px on content areas

### Status Badges

Used for the row colour legend.

```css
.badge {
  display: inline-flex;
  align-items: center;
  font-size: var(--text-xs);     /* 0.64rem */
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 3px 10px;
  border-radius: 2px;
  border: 1px solid currentColor;
}
```

### Form labels

All form widget labels use the eyebrow style:

```css
.field__label {
  font-size: var(--text-xs);     /* 0.64rem */
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-mid);
}
```

### Data tables

```css
.table th {
  font-size: var(--text-xs);
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-mid);
  border-bottom: 1.5px solid var(--color-border);
}
.table td {
  font-size: var(--text-sm);
  color: var(--color-text);
  border-bottom: 1px solid var(--color-border);
}
/* Numeric columns — always monospace */
.table td.numeric { font-family: var(--font-mono); }
```

---

## 5. Elevation & Depth

Depth is structural, not decorative.

```css
:root {
  --shadow-xs: 0 1px 2px  rgba(15, 14, 12, 0.06);
  --shadow-sm: 0 1px 4px  rgba(15, 14, 12, 0.08);
  --shadow-md: 0 2px 8px  rgba(15, 14, 12, 0.10);
}
```

- Default state: **no shadow** — use border instead
- `--shadow-sm`: raised card variant only
- `--shadow-md`: modals and dialogs only
- Never stack shadows or use coloured shadows

---

## 6. Borders & Radius

```css
:root {
  --radius-sm:   2px;    /* badges, tags */
  --radius-md:   4px;    /* cards, inputs, buttons */
  --radius-lg:   6px;    /* maximum allowed */
  --radius-full: 999px;  /* pills (avoid in this system) */
}
```

- `--radius-md` (4px) for all interactive elements
- Never use radius > 6px on content containers
- Border width: `1px` for structure, `1.5px` for active/focused states

---

## 7. Motion

Motion communicates state change. Never decorative.

```css
:root {
  --duration-fast:   150ms;
  --duration-normal: 250ms;
  --duration-slow:   400ms;
  --ease-standard:   cubic-bezier(0.2, 0, 0, 1);
}
/* All transitions max 150ms for micro-interactions */
transition: border-color 120ms ease, background 120ms ease;
```

**Rules:**
- Maximum transform: `translateY(8px)` for reveals
- No animations exceeding 400ms
- Never rotate, scale beyond 1.02, or use bounce easing

---

## 8. Writing Style

| Principle | Do | Don't |
|-----------|-----|-------|
| Direct | "Save" | "Save changes" |
| Precise | "32 items" | "Many items" |
| Active voice | "Delete file" | "File will be deleted" |
| No filler | "Continue" | "Click here to continue" |
| Button labels | Verb + noun: "Learn from corrections" | "SUBMIT", "OK" |
| Confirmations | "Done — 3 rules updated" | "Your changes have been saved successfully!" |

**Labels:** uppercase, short, noun-based — `STATUS`, `DATE`, `SOURCE`

**Headings:** sentence case — `"Transaction detail"`, not `"Transaction Detail"`

---

## 9. Do's and Don'ts

### Do
- Use whitespace to create hierarchy
- Apply the accent color (`#D4A017`) exactly once per viewport
- Make every interactive state explicit (hover, focus, active, disabled)
- Use `DM Mono` for numbers in data tables
- Prefer borders over shadows for structure
- Keep button labels in sentence case

### Don't
- Use more than two typeface weights on a single view
- Use gradients anywhere
- Use `border-radius > 6px` on content containers
- Use color as the sole indicator of status — always pair with text
- Show more than one primary/accent action per context
- Use uppercase for body text or button labels
- Add box shadows to non-floating elements

---

## 10. Full Token Reference

```python
# Streamlit implementation — paste into C dict in app.py
C = {
    "bg":          "#EDEBE6",   # main background
    "surface":     "#F5F4F0",   # card / widget background
    "surface_alt": "#E2E0DA",   # sidebar / inset background
    "border":      "#C8C5BC",   # all borders
    "text":        "#1A1916",   # primary text
    "text_sub":    "#5C5A55",   # secondary text
    "mid":         "#8C8982",   # muted labels
    "black":       "#0F0E0C",   # headings, key UI
    "accent":      "#D4A017",   # ONE per view
    "success":     "#3A6B45",
    "error":       "#8B2E2E",
    "disabled":    "#BFBDB8",
    "row_human":   "#EBF2EC",
    "row_rule":    "#E8E6E0",
    "row_llm_hi":  "#FAF3DC",
    "row_llm_lo":  "#F5EAEA",
}
```

```toml
# .streamlit/config.toml
[theme]
primaryColor            = "#D4A017"
backgroundColor         = "#EDEBE6"
secondaryBackgroundColor = "#E2E0DA"
textColor               = "#1A1916"
font                    = "sans serif"
```

---

*This system is complete. Add only what function demands. Remove everything else.*
