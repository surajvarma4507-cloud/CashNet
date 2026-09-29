# CASHNET Frontend Design System & UI/UX Specification

> **Smart India Hackathon (SIH26184)**  
> **AI-Powered Cybercrime Cash-Out Prediction & Investigator Decision-Support Platform**  
> **Documentation Version**: 2.0  
> **Design Theme**: Calm, Precise, Human-Centered (Light Theme Default)

---

## 1. Design Concept & Architectural Rationale

CASHNET is an investigator decision-support tool engineered for cybercrime police officers, intelligence analysts, and bank nodal officers. In high-pressure investigative environments, interface clarity, cognitive load reduction, and forensic precision are paramount.

### Core Philosophy: "Calm, Precise, Human-Centered"
1. **Calm**: A clean, light-theme canvas using soft off-white surfaces (`#F8FAFC`, `#FFFFFF`), fine 1px slate borders (`#E2E8F0`), and restrained elevation shadows. Avoids distracting neon glows or dark cyberpunk aesthetics.
2. **Precise**: High data density with tabular alignment, clear mono-spaced numbers for financial figures (e.g. `₹75,000.00`), explicit timestamp provenance, and strict visual distinction between empirical facts and probabilistic ML predictions.
3. **Human-Centered**: All automated outputs are presented with transparent explanations, observable risk/protective factors, and clear disclaimers that tactical interventions require human authorization.

---

## 2. Color Palette & Semantic Tokens

### 2.1 Base Canvas & Surface Colors
| Token | Hex Value | Purpose |
|---|---|---|
| `bg-app` | `#F8FAFC` (Slate 50) | Main application background |
| `surface-card` | `#FFFFFF` (Pure White) | Primary card and table container surface |
| `surface-subtle` | `#F1F5F9` (Slate 100) | Secondary panels, table headers, drawer backgrounds |
| `border-subtle` | `#E2E8F0` (Slate 200) | Standard borders, divider lines |
| `border-strong` | `#CBD5E1` (Slate 300) | Active inputs, selected node borders |

### 2.2 Text & Content Colors
| Token | Hex Value | Purpose | Contrast Ratio vs White |
|---|---|---|:---:|
| `text-primary` | `#0F172A` (Slate 900) | Headings, primary labels, table data | 15.8:1 (AAA) |
| `text-secondary` | `#475569` (Slate 600) | Subtitles, field labels, metadata | 7.0:1 (AAA) |
| `text-muted` | `#64748B` (Slate 500) | Helper text, secondary timestamps | 4.6:1 (AA) |
| `text-disabled` | `#94A3B8` (Slate 400) | Inactive placeholders, disabled states | 3.0:1 |

### 2.3 Distinctive Brand & Accent Colors
| Token | Hex Value | Purpose |
|---|---|---|
| `accent-primary` | `#0D9488` (Teal 600) | Brand mark, primary action buttons, active navigation tab |
| `accent-hover` | `#0F766E` (Teal 700) | Hover state for primary buttons |
| `accent-light` | `#CCFBF1` (Teal 100) | Active tab highlights, badge backgrounds |
| `accent-ring` | `#14B8A6` (Teal 500) | Keyboard focus rings |

### 2.4 Semantic Data Distinction Tokens (The 5 Layers)
To prevent confusion between observed facts, derived metrics, predictions, and actions, distinct semantic color accents are assigned:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. OBSERVED EVIDENCE (Slate / Blue)                                        │
│    - Badge: bg-slate-100 text-slate-800 border-slate-300                   │
│    - Role: Primary victim accounts, confirmed completed transactions       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. DERIVED GRAPH TOPOLOGY (Indigo / Purple)                                │
│    - Badge: bg-indigo-50 text-indigo-700 border-indigo-200                 │
│    - Role: Hop depths, branching factor, cycle alerts, syndicate clusters  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. MODEL PREDICTIONS (Amber / Teal / Rose by Risk Tier)                    │
│    - Critical Risk (>=0.85): bg-rose-50 text-rose-700 border-rose-200     │
│    - High Risk (0.60-0.85):  bg-amber-50 text-amber-700 border-amber-200   │
│    - Moderate (0.30-0.60):   bg-sky-50 text-sky-700 border-sky-200         │
│    - Low Risk (<0.30):       bg-emerald-50 text-emerald-700 border-emerald │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. SYNTHETIC PROTOTYPE DISCLAIMER (Orange / Amber Strip)                   │
│    - Badge: bg-amber-50 text-amber-800 border-amber-300                    │
│    - Text: "SYNTHETIC PROTOTYPE — NOT REAL CITIZEN DATA"                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. INVESTIGATOR ACTIONS (Emerald / Forest Green)                           │
│    - Badge: bg-emerald-50 text-emerald-800 border-emerald-300              │
│    - Role: Frozen accounts, dispatched alerts, audit timeline entries      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Typography Choices & Scale

- **Primary UI Font**: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
- **Monospace Font**: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace (Used for Account IDs, Case IDs, Transaction Hashes, Amounts, and Coordinates)

### Type Hierarchy
| Level | Font Size | Line Height | Weight | Usage |
|---|---|---|---|---|
| Display / H1 | 24px (1.5rem) | 32px | 700 (Bold) | Dashboard & Case Dossier titles |
| Section / H2 | 18px (1.125rem) | 24px | 600 (Semibold) | Panel headers, card titles |
| Card / H3 | 15px (0.9375rem) | 20px | 600 (Semibold) | Subsection titles, modal headers |
| Body Regular | 14px (0.875rem) | 20px | 400 (Regular) | Table contents, narrative body text |
| Body Medium | 14px (0.875rem) | 20px | 500 (Medium) | Table headers, button text, badges |
| Caption / Meta | 12px (0.75rem) | 16px | 400/500 | Timestamps, micro-labels, disclaimers |

---

## 4. Spacing, Borders, Radius & Shadows

- **Grid System**: 8px baseline grid (4px, 8px, 12px, 16px, 20px, 24px, 32px, 48px).
- **Border Radius**:
  - `rounded-sm`: 4px (Badges, small tags)
  - `rounded-md`: 6px (Input fields, buttons, table rows)
  - `rounded-lg`: 8px (Cards, modal dialogs, map containers)
  - `rounded-xl`: 12px (Main content panels)
- **Borders**: 1px solid `#E2E8F0` on all cards and tables.
- **Shadows**:
  - `shadow-subtle`: `0 1px 2px 0 rgba(0, 0, 0, 0.05)`
  - `shadow-card`: `0 1px 3px 0 rgba(0, 0, 0, 0.08), 0 1px 2px -1px rgba(0, 0, 0, 0.05)`
  - `shadow-modal`: `0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.05)`

---

## 5. Component Styling Principles

1. **Information Density**: Compact padding (`py-2.5 px-3` for table cells) allowing investigators to view multiple rows without excessive scrolling.
2. **Accessible Form Controls**: Clear focus rings (`ring-2 ring-teal-500 ring-offset-1`), high-contrast placeholder text, and explicit error states.
3. **Empty & Loading States**: Every table, graph, and list must have tailored skeleton loaders and helpful empty states explaining why no data was returned (e.g. "No cases match current filter criteria").
4. **Stateful Feedback**: Interactive elements provide immediate tactile feedback (hover background transitions, button loading spinners, toast notifications for logged actions).

---

## 6. Accessibility & Keyboard Navigation (WCAG 2.1 AA)

1. **Color Independence**: Every risk badge or status chip includes text labels and distinct icons (not color alone).
2. **Keyboard Focus**: Full keyboard navigation across tabs, modals, pagination, and action forms.
3. **Reduced Motion**: All animations (spinners, fade-ins) respect `@media (prefers-reduced-motion: reduce)`.
4. **Screen Reader Support**: Semantic HTML (`<main>`, `<nav>`, `<article>`, `<table>`, `<button>`) with `aria-label` attributes on icon-only buttons.

---

**Last Updated**: 2026-09-28  
**Documentation Version**: 2.0  
**Status**: Design System Formally Specified
