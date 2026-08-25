# PHARMAGUARD — COMPLETE DASHBOARD UI/UX REFINEMENT

Repository:

https://github.com/Krishna200608/PharmaGuard

Tech stack:
- Python
- Streamlit
- Existing custom CSS/design system
- Google Material Icons

Attached screenshots represent the CURRENT visual state of the dashboard in:

- Dark mode — Overview
- Dark mode — Per-Pair Evaluation
- Dark mode — Disagreement Spotlight
- Dark mode — Baseline Comparison
- Light mode — Overview
- Light mode — Per-Pair Evaluation
- Light mode — Disagreement Spotlight
- Light mode — Baseline Comparison

Your task is to perform a **repository-aware, whole-dashboard UI/UX refinement**.

This is NOT a request to rewrite the application.

This is NOT a request to change the research methodology.

This is NOT a request to alter the underlying evaluation results.

The goal is:

> Transform the existing PharmaGuard Streamlit dashboard into a polished, coherent, publication/demo-quality academic research interface while preserving all current functionality and data.

---

# 1. START WITH REPOSITORY INSPECTION

Before modifying anything, inspect the existing implementation carefully.

The dashboard styling/components are already organized around:

```text
scripts/
└── dashboard_modules/
    ├── components.py
    ├── data_loader.py
    ├── styles.py
    └── views/
        ├── overview.py
        ├── per_pair.py
        ├── disagreements.py
        └── baseline.py
```

Use the existing architecture rather than creating a parallel UI framework.

First inspect:

```text
scripts/dashboard_modules/styles.py
scripts/dashboard_modules/components.py
scripts/dashboard_modules/views/overview.py
scripts/dashboard_modules/views/per_pair.py
scripts/dashboard_modules/views/disagreements.py
scripts/dashboard_modules/views/baseline.py
```

Also locate:

- Streamlit entry point.
- Theme-selection logic.
- Navigation implementation.
- Google Material Icon implementation.
- Any global CSS injection.
- Any additional dashboard-specific styling.
- Any page configuration.
- Any CSS selectors currently targeting Streamlit DOM elements.

Understand the current styling architecture before changing it.

---

# 2. CORE RULE — PRESERVE THE APPLICATION

Do NOT modify:

- research methodology
- calculations
- metrics
- evaluation logic
- dataset
- expected labels
- actual outputs
- evidence content
- benchmark values
- confidence calculations
- filtering semantics
- navigation semantics
- session-state behavior

Do NOT change any numerical result.

Do NOT fabricate data.

Do NOT rewrite scientific explanations merely for styling purposes.

The UI must become better while the application behaves exactly as before.

---

# 3. USE THE SCREENSHOTS AS VISUAL REFERENCES

Treat the attached screenshots as the current baseline.

The current design already has good fundamentals:

- clear research-oriented content
- strong metric hierarchy
- dark/light support
- semantic status badges
- evidence panels
- comparison tables
- consistent four-page structure

Do not destroy these strengths.

Instead, refine them.

Target design:

> Premium academic analytics dashboard + clinical/research evaluation interface.

The finished UI should look appropriate for:

- B.Tech capstone demonstration
- faculty evaluation
- research presentation
- paper/report screenshots
- technical demo
- GitHub project showcase

It must NOT look like:

- a default Streamlit app
- a generic admin panel
- an overly flashy AI startup
- a gaming interface
- a neon dashboard

---

# 4. IMPORTANT VISUAL PROBLEMS TO FIX

The screenshots reveal several specific issues.

## A. DARK MODE NAVIGATION CONTRAST

Inactive navigation items are currently too dark.

They visually disappear against the dark background.

Fix this.

Inactive items must have clearly readable secondary text.

Recommended Dark Mode:

```text
Inactive navigation:
#9AA5B5

Hover:
#D5DBE5

Active:
Primary accent
```

Active navigation should retain the red/accent identity but become more refined.

Do NOT make inactive tabs nearly black.

---

# 5. REMOVE THE LARGE BLUE VIEWPORT GLOW

The screenshots show a strong blue/blue-white glow around the outer viewport edges.

This currently looks decorative rather than intentional.

REMOVE it.

Do not leave a large:

- `box-shadow`
- radial glow
- outer border glow
- pseudo-element halo
- body-level blue aura

around the entire application.

The page should terminate cleanly at the edges.

A very subtle ambient accent is acceptable only when it is genuinely part of a component.

The application should NOT look like it is surrounded by a neon frame.

---

# 6. GLOBAL DESIGN TOKENS

Refactor the existing style system so the visual language is centralized.

Prefer modifying the existing:

```text
scripts/dashboard_modules/styles.py
```

rather than creating unrelated style files.

Use CSS custom properties / shared theme tokens wherever practical.

## DARK

```text
--bg:
#080D16

--surface:
#101824

--surface-2:
#121B29

--surface-elevated:
#151F2E

--border:
#263245

--divider:
#182230

--text:
#F3F6FA

--text-secondary:
#A8B3C3

--text-muted:
#738096

--primary:
#6672FF

--primary-hover:
#7B84FF

--success:
#22C77A

--warning:
#F2B84B

--danger:
#FF4D4D

--info:
#4EA1FF
```

## LIGHT

```text
--bg:
#F7F9FC

--surface:
#FFFFFF

--surface-2:
#F2F5F9

--surface-elevated:
#FFFFFF

--border:
#D9E1EA

--divider:
#E4E9F0

--text:
#172033

--text-secondary:
#53657D

--text-muted:
#7C8A9D

--primary:
#4F46E5

--primary-hover:
#4338CA

--success:
#168A55

--warning:
#A96F00

--danger:
#D92D20

--info:
#1769AA
```

Do not blindly replace every existing color with these values.

Adapt them to the current implementation where needed.

The goal is consistency.

---

# 7. RED MUST BECOME SEMANTIC

Do NOT use red as the dashboard's universal branding color.

Red should mean something.

Use:

```text
Red:
danger / disagreement / negative outcome

Green:
success / correct escalation / favorable outcome

Amber:
warning / uncertainty / caution

Blue/Indigo:
primary UI / navigation / neutral emphasis

Gray:
neutral information
```

This is especially important because PharmaGuard is a pharmacovigilance evaluation system.

The visual language should communicate meaning.

---

# 8. GOOGLE MATERIAL ICONS

The project already uses Google Material Icons.

Preserve that approach.

Do NOT:

- replace the icons with emojis
- introduce random icon libraries
- mix unrelated icon styles
- replace the PharmaGuard logo/icon

Use Material Icons consistently for:

- Light
- Dark
- System
- filters
- status indicators
- navigation where appropriate
- UI affordances

Icon sizes should be standardized.

Recommended approximate sizing:

```text
Navigation icon:
16–18px

Compact control:
16–18px

Primary visual icon:
20–24px
```

Icons should align optically with their text.

---

# 9. THEME SWITCHER — MAJOR REFINEMENT

Current screenshots show:

```text
Light | Dark | System
```

with an overly prominent red outline around the active item.

Improve the existing implementation instead of replacing it with an unrelated control.

Target:

```text
┌──────────────────────────────────────┐
│  ☼ Light    ◐ Dark    ▣ System       │
└──────────────────────────────────────┘
```

Requirements:

- compact segmented control
- rounded outer container: ~10–12px
- subtle border
- balanced horizontal padding
- equal visual weight for all 3 choices
- active state visually obvious
- inactive states readable
- no thick red rectangular border
- no excessive shadow
- no glow
- icons vertically centered
- labels vertically centered

Dark active:

```text
background:
rgba(102,114,255,0.12)

text/icon:
primary accent
```

Light active should follow the same visual language.

System active should use exactly the same component behavior.

The theme selector should look like part of the product design system rather than a default Streamlit segmented control.

---

# 10. GLOBAL NAVIGATION

Refine the existing navigation.

There are four pages:

```text
Overview
Per-Pair Table
Disagreement Spotlight
Baseline Comparison
```

Requirements:

### Active tab

Use:

- strong readable accent
- slightly increased font weight
- subtle active background OR restrained underline
- 2–3px indicator
- smooth hover transition

### Inactive tab

Must remain clearly readable in both themes.

Dark:

```text
#9AA5B5
```

Light:

```text
#526176
```

### Hover

Use a subtle surface/accent tint.

Do not introduce animated sliding indicators.

Do not make tabs giant pills.

The visual language should remain academic and restrained.

---

# 11. GLOBAL LAYOUT

Standardize all four pages.

Use one coherent content container.

Target approximately:

```text
max-width:
1200–1280px
```

Keep content horizontally centered.

Standardize:

- left/right margins
- page heading position
- subtitle spacing
- section spacing
- card spacing
- divider spacing

Do not allow individual pages to drift into unrelated layouts.

---

# 12. TYPOGRAPHY SYSTEM

Refactor typography into shared styles.

Approximate hierarchy:

```text
Page title:
30–34px / 700

Page subtitle:
15–17px / 400–500

Section heading:
14–16px / 650–700

Metric hero:
48–64px / 700–800

Metric value:
28–36px / 700–800

Body:
14–16px

Helper text:
12–14px

Labels:
12–13px / 600–700
```

Important:

- improve line-height
- avoid ultra-thin text
- maintain readable evidence paragraphs
- preserve strong numerical hierarchy
- keep numerical values visually aligned

Use one consistent type scale across all pages.

---

# 13. CARDS

The dashboard currently has many cards.

Unify them into a coherent component system.

Standardize:

```text
radius:
10–14px

border:
1px solid theme border

padding:
20–28px

surface:
theme surface

shadow:
very subtle
```

Do not use strong shadows.

Do not use bright glowing borders.

Do not create arbitrary card styles per page.

The card hierarchy should come from:

- size
- spacing
- typography
- semantic accent
- surface contrast

rather than decoration.

---

# 14. OVERVIEW PAGE

Target file:

```text
scripts/dashboard_modules/views/overview.py
```

Preserve the existing information structure.

Current hierarchy:

1. PharmaGuard — Evaluation Overview
2. Strict Recall
3. Over-Caution Rate
4. Spurious False Alarms
5. Strict Evaluation Metrics

Improve the visual hierarchy.

## Header

Make:

**PharmaGuard — Evaluation Overview**

the dominant heading.

Use the existing PharmaGuard icon.

Improve:

- icon-to-title spacing
- vertical alignment
- subtitle spacing
- heading weight

Do not redesign the logo.

## Hero metric

The:

```text
0.857
```

Strict Recall value should remain the main visual result.

Make the hero card clearly primary.

But avoid making it excessively huge.

Supporting text should be easy to scan.

## Supporting metric card

The Over-Caution Rate / Spurious False Alarm card should visually support the hero metric.

Do not make it compete with the hero.

## Lower metric grid

These four cards:

- Strict Precision
- Strict Specificity
- Strict F1
- Pairs Evaluated

must have:

- equal visual weight
- consistent height
- consistent internal padding
- consistent label styling
- consistent numeric typography

Avoid one card looking different because its text wraps differently.

---

# 15. PER-PAIR PAGE

Target file:

```text
scripts/dashboard_modules/views/per_pair.py
```

This is the most data-dense page.

Optimize for readability.

## Filters

The two selectors and:

```text
Disagreements only
```

should form a cohesive filter toolbar.

Standardize:

- height
- border
- radius
- typography
- spacing
- checkbox alignment
- focus state

## Table

This is a critical component.

Improve:

### Header

Stronger contrast than current dark mode.

Use uppercase/small-label styling if already present.

### Body

Increase row readability.

Maintain sufficient vertical padding.

### Numeric columns

Keep confidence and counts aligned.

### Status badges

Use the unified badge system.

### Row hover

Add a very subtle hover surface.

### Overflow

The current screenshot shows the rightmost table content becoming clipped.

Fix this structurally.

Requirements:

- no viewport-level horizontal overflow
- no inaccessible final columns
- no destroying readability by shrinking fonts
- use a controlled horizontal-scroll container if necessary
- preserve minimum useful column widths

The user must be able to inspect the complete table.

---

# 16. DISAGREEMENT SPOTLIGHT

Target file:

```text
scripts/dashboard_modules/views/disagreements.py
```

This page should communicate:

> “These are meaningful disagreements requiring interpretation.”

Do NOT style the entire page as an error state.

## Summary card

Make:

```text
Expected → Got
```

immediately scannable.

Use:

```text
Expected ESCALATE:
success/green

Actual MONITOR:
neutral/amber

Overall disagreement:
accent/danger only where semantically justified
```

Do not turn the entire card red.

## Evidence layout

Maintain the existing structure:

- Epidemiological Evidence
- Mechanistic Plausibility
- PubMed Evidence Summary
- Why Monitor Is Correct Here

Make the two-column layout balanced.

Standardize:

- heading size
- paragraph line-height
- padding
- borders
- callout styling

The green "Why Monitor Is Correct Here" callout should remain green but be restrained.

Use light semantic emphasis rather than a saturated green block.

---

# 17. BASELINE COMPARISON

Target file:

```text
scripts/dashboard_modules/views/baseline.py
```

Preserve the side-by-side model comparison.

Sections:

```text
PharmaGuard · Tool-Grounded
Single-Shot LLM Baseline · No Tools
```

Improve the distinction subtly.

PharmaGuard:

- primary accent emphasis

Baseline:

- neutral secondary emphasis

Do not make one side excessively colorful.

## Comparison table

Standardize:

- header
- row spacing
- numeric alignment
- borders
- typography

Where a meaningful metric difference exists, subtle emphasis is acceptable.

Do NOT turn the table into a colorful heatmap unless the existing research design explicitly calls for it.

---

# 18. BADGE SYSTEM

Create/reuse a shared badge helper.

Important categories:

```text
Confirmed Positive
Genuine Negative

STRONG
MODERATE
HIGH
LOW
NO_SIGNAL

ESCALATE
MONITOR
DO_NOT_ESCALATE

Grade A
Grade B
Grade C
```

Use semantic but restrained styling.

Suggested conceptual mapping:

```text
Confirmed Positive → blue/info
Genuine Negative   → neutral

STRONG             → green
MODERATE           → amber
HIGH               → green
LOW                → muted

ESCALATE           → green
MONITOR            → amber / neutral
DO_NOT_ESCALATE    → muted

Grade A            → blue
Grade B            → neutral
Grade C            → muted
```

Do not make every badge saturated.

Do not rely exclusively on color.

Maintain readable text.

---

# 19. DIVIDERS

The current dividers are stronger than necessary.

Use subtle separators.

Dark:

```text
#182230
```

Light:

```text
#E1E7EF
```

A divider should structure the page, not attract attention.

---

# 20. SPACING SYSTEM

Use a consistent spacing scale.

```text
4px
8px
12px
16px
24px
32px
48px
```

Prefer these tokens instead of arbitrary margin values.

Use consistently between:

- navigation
- headings
- subtitles
- cards
- sections
- evidence blocks
- tables

The interface should feel rhythmically consistent.

---

# 21. RESPONSIVE BEHAVIOR

Test beyond the screenshot width.

At smaller widths:

- metric grids collapse logically
- evidence columns stack
- tables scroll horizontally inside a bounded container
- filters wrap sensibly
- theme selector does not overlap navigation
- page headings do not clip
- subtitles wrap naturally

Do NOT simply reduce every font size.

Do NOT create horizontal page overflow.

---

# 22. LIGHT MODE NEEDS SPECIAL ATTENTION

The current Light screenshots are better than the Dark screenshots in some readability areas, but the visual hierarchy is still somewhat flat.

Improve Light Mode by using:

- white cards against soft #F7F9FC background
- subtle borders
- slightly stronger headings
- clear section separation
- controlled shadows where useful

Avoid:

- excessive gray backgrounds
- washed-out borders
- overly pale secondary text
- pure-white-everything appearance

Light Mode should feel like the same product as Dark Mode.

---

# 23. DARK MODE NEEDS SPECIAL ATTENTION

This is the highest-priority theme to improve.

Fix:

- navigation contrast
- subtitle contrast
- table readability
- card separation
- inactive tabs
- helper text
- selector controls
- outer viewport glow
- borders that disappear into the background

Dark Mode should feel premium and calm, not black-and-red.

---

# 24. STREAMLIT IMPLEMENTATION RULES

Use the existing Streamlit architecture.

Prefer:

- shared helper functions
- shared CSS
- CSS variables
- reusable components
- centralized style injection

Avoid:

- duplicating large CSS blocks
- page-specific hacks
- unnecessary JavaScript
- new frontend frameworks
- React
- Tailwind
- unrelated component libraries

Do NOT turn the application into another stack.

Keep it Streamlit.

---

# 25. IMPORTANT: DO NOT BREAK EXISTING STREAMLIT BEHAVIOR

Before editing CSS selectors, inspect the existing DOM-related selectors.

Do not accidentally break:

- navigation
- controls
- filters
- tables
- checkboxes
- segmented controls
- responsive behavior

Avoid brittle selectors based on generated Streamlit class names where possible.

Prefer stable selectors or controlled wrappers.

---

# 26. DO NOT CREATE UNNECESSARY FILES

Prefer modifying the existing architecture.

Primary targets should likely be:

```text
scripts/dashboard_modules/styles.py
scripts/dashboard_modules/components.py
scripts/dashboard_modules/views/overview.py
scripts/dashboard_modules/views/per_pair.py
scripts/dashboard_modules/views/disagreements.py
scripts/dashboard_modules/views/baseline.py
```

Only add another style/helper file if the existing architecture genuinely benefits from it.

Do not create duplicate design systems.

---

# 27. IMPLEMENTATION ORDER

Follow this order.

## Phase 1
Audit current implementation.

## Phase 2
Refactor the shared design tokens.

## Phase 3
Fix global application shell:

- page background
- content width
- viewport glow
- typography
- navigation
- theme selector

## Phase 4
Refine shared components:

- cards
- badges
- controls
- tables
- callouts
- dividers

## Phase 5
Refine pages:

1. Overview
2. Per-Pair Evaluation
3. Disagreement Spotlight
4. Baseline Comparison

## Phase 6
Validate:

- Dark
- Light
- System
- wide desktop
- narrower desktop

---

# 28. QUALITY BAR

Do not stop at "CSS has been changed."

Actually evaluate the result visually.

Ask:

### Does it look like one product?
Yes.

### Does Dark Mode have readable inactive navigation?
Yes.

### Does Light Mode maintain hierarchy?
Yes.

### Does the theme selector look professionally designed?
Yes.

### Is the outer blue glow gone?
Yes.

### Are cards consistent?
Yes.

### Are tables readable?
Yes.

### Is the right edge of the Per-Pair table accessible?
Yes.

### Are semantic colors meaningful?
Yes.

### Does the dashboard still look academically appropriate?
Yes.

### Is the research data untouched?
Yes.

---

# 29. TESTING

After implementation:

1. Run the Streamlit dashboard.
2. Open Overview.
3. Open Per-Pair Evaluation.
4. Open Disagreement Spotlight.
5. Open Baseline Comparison.
6. Switch to Dark.
7. Switch to Light.
8. Switch to System.
9. Test the Per-Pair filters.
10. Test table scrolling.
11. Resize the viewport.
12. Look for horizontal overflow.
13. Look for text clipping.
14. Look for invisible/inaccessible text.
15. Check all Material Icons.
16. Check browser/runtime errors.

Do not declare success until all four pages render correctly in both major themes.

---

# 30. FINAL IMPLEMENTATION REPORT

At the end, provide:

```text
UI/UX REFINEMENT COMPLETE

Files modified:
...

Global design system:
...

Navigation:
...

Theme selector:
...

Dark mode:
...

Light mode:
...

Overview:
...

Per-Pair Evaluation:
...

Disagreement Spotlight:
...

Baseline Comparison:
...

Responsive behavior:
...

Research/data logic changed:
NO

Functional behavior changed:
NO

Remaining limitations:
...
```

Keep the report concise and factual.

The priority is the actual implementation, not the explanation.

---

# FINAL INSTRUCTION

Treat this as a **whole-dashboard design-system refinement of the existing PharmaGuard repository**, not a generic cosmetic CSS task.

Use the existing codebase intelligently.

Preserve the current scientific/research content.

Preserve the current functionality.

Preserve the PharmaGuard branding and Google Material Icons.

Improve the visual system everywhere consistently.

The final result should look like a **finished research product**, not an unfinished Streamlit prototype.