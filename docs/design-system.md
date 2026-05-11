# FinTrack — Design System

> *"Good design is as little design as possible."* — Dieter Rams

Rooted in the Ten Principles of Good Design. Every element must justify its existence.

**Core mandates:**
- Remove before you add
- Every element must earn its place
- Honesty over ornament
- Longevity over trend
- Clarity over cleverness

---

## Color Palette

The palette is deliberately narrow. Neutrals dominate. Accent color is used sparingly.

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
  --color-black:        #0F0E0C;   /* True dark, headers and key UI */

  /* Functional Accent */
  --color-accent:       #D4A017;   /* Warm amber-gold — used < 5% of UI surface */
  --color-accent-alt:   #E8640A;   /* Destructive or alert states */

  /* State Colors */
  --color-success:      #3A6B45;
  --color-error:        #8B2E2E;
  --color-disabled:     #BFBDB8;
}
```

**Rules:**
- `--color-accent` appears on **one element per view** maximum
- Never use gradients. Never use shadows heavier than `0 1px 3px rgba(0,0,0,0.08)`

### Streamlit implementation (current palette)

The Streamlit app uses a compatible earthy palette via `config.toml` and inline CSS:

```python
C = {
    "bg":        "#e8e2cc",
    "surface":   "#f0ead6",
    "text":      "#2c2818",
    "bronze":    "#d4a373",   # primary accent
    "tea_green": "#ccd5ae",   # secondary accent
    "sidebar_bg":"#2c2818",
}
```

Row colour coding (desaturated, readable):
- Human: `#d4edda` (sage green)
- Rule: `#d1e7ff` (soft blue)
- LLM high-conf: `#fff3cd` (warm amber)
- LLM low-conf: `#f8d7da` (soft rose)

---

## Typography

```css
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

:root {
  --font-body: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  --font-mono: 'DM Mono', 'Courier New', monospace;

  /* Type scale (Major Third — 1.250) */
  --text-xs:   0.64rem;   /*  ~10px — labels */
  --text-sm:   0.8rem;    /*  ~13px — captions, meta */
  --text-base: 1rem;      /*   16px — body */
  --text-md:   1.25rem;   /*   20px — subheadings */
  --text-lg:   1.563rem;  /*   25px — section headers */
  --text-xl:   1.953rem;  /*  ~31px — page titles */
}
```

**Rules:**
- Maximum two type sizes on any single view
- Uppercase labels only for organizational labels, never body text
- Measure: 60–72 characters for body text

---

## Spacing System

Based on an 8px base unit. All spacing values are multiples.

```css
:root {
  --space-1:   4px;
  --space-2:   8px;
  --space-3:   12px;
  --space-4:   16px;
  --space-5:   24px;
  --space-6:   32px;
  --space-7:   48px;
  --space-8:   64px;
}
```

---

## Elevation & Depth

```css
:root {
  --shadow-xs: 0 1px 2px  rgba(15, 14, 12, 0.06);
  --shadow-sm: 0 1px 4px  rgba(15, 14, 12, 0.08);
  --shadow-md: 0 2px 8px  rgba(15, 14, 12, 0.10);
}
```

- Default state: no shadow; use border instead
- Shadow only for overlaid/floating elements
- Never stack shadows or use colored shadows

---

## Borders & Radius

```css
:root {
  --radius-sm:   2px;
  --radius-md:   4px;
  --radius-lg:   6px;
  --radius-full: 999px;
}
```

- Prefer `--radius-md` (4px) for all interactive elements
- Never exceed 6px radius on content containers
- Border width: 1px for structure, 1.5px for active/focused states

---

## Motion

Motion communicates state change. Never decorative.

```css
:root {
  --duration-fast:   150ms;
  --duration-normal: 250ms;
  --duration-slow:   400ms;
  --ease-standard:   cubic-bezier(0.2, 0, 0, 1);
}
```

- Maximum transform: `translateY(8px)` for reveals
- Never rotate, scale beyond 1.02, or use bounce easing
- No animations exceeding 400ms

---

## Buttons

Three types only:

| Type | Usage |
|------|-------|
| Primary (dark filled) | Main action per view |
| Secondary (outlined) | Supporting actions |
| Accent (amber) | One signal action per view — e.g. "Learn" |

---

## Writing Style

| Principle | Do | Don't |
|-----------|-----|-------|
| Direct | "Save" | "Save changes" |
| Precise | "32 items" | "Many items" |
| Active voice | "Delete file" | "File will be deleted" |
| No filler | "Continue" | "Click here to continue" |
| Button labels | Verb + noun: "Add item" | "Submit", "OK", "Yes" |

**Labels:** uppercase, short, noun-based — `STATUS`, `DATE`, `TYPE`

---

## Do's and Don'ts

### Do
- Use whitespace to create hierarchy
- Apply the accent color exactly once per viewport
- Make every interactive state explicit (hover, focus, active, disabled)
- Use monospace for numbers in data tables
- Prefer borders over shadows for structure

### Don't
- Use more than two typeface weights on a single view
- Add decorative illustrations or stock imagery
- Use gradients anywhere
- Use `border-radius > 6px` on content containers
- Use color as the sole indicator of status
- Show more than one primary action per context
