# ReformLab Visual Identity Guide

**Version:** 1.0
**Date:** 2026-02-25
**Author:** Lucas
**Status:** Canonical Reference

> This document is the single authoritative source for ReformLab's visual identity across all touchpoints: website, application UI, presentations, communications, branding, and marketing materials. When in doubt, this guide takes precedence over any other document.

---

## Table of Contents

1. [Brand Overview](#1-brand-overview)
2. [Logo](#2-logo)
3. [Color System](#3-color-system)
4. [Typography](#4-typography)
5. [Visual Style Principles](#5-visual-style-principles)
6. [Icons and Imagery](#6-icons-and-imagery)
7. [Layout Principles](#7-layout-principles)
8. [Chart and Data Visualization](#8-chart-and-data-visualization)
9. [Brand Voice and Tone](#9-brand-voice-and-tone)
10. [Canonical Copy](#10-canonical-copy)
11. [Application UI Guidelines](#11-application-ui-guidelines)
12. [Presentation Guidelines](#12-presentation-guidelines)
13. [Appendix A: Generation Prompts](#appendix-a-generation-prompts)
14. [Appendix B: Source File Reference](#appendix-b-source-file-reference)

---

## 1. Brand Overview

### Mission

ReformLab is an open-source policy impact modeling platform for European administrations. It connects open data to policy models so analysts can assess distributional impact themselves — without coding, without waiting for external teams.

### Positioning

- **OpenFisca-first:** OpenFisca handles policy calculations; ReformLab handles everything above that — data preparation, scenario management, dynamic projections, indicators, governance, and user interfaces.
- **Open-data-first:** Works out of the box with public data (INSEE, Eurostat, EU-SILC). Custom data optional.
- **France and Europe:** Initial focus on French household carbon-tax and redistribution scenarios, with European expansion planned.
- **Two-act product:** Simple mode (clear reports, executive summaries) gets you in the door. Advanced mode (multi-scenario comparison, budget-constrained optimization) creates retention.

### Brand Personality

**Pragmatic optimism.** Don't oversell. Don't claim to save the world. Claim to make one specific thing work better. The bigger picture (better policies, distributive justice, informed voting) is a *consequence*, not a pitch.

The visual language says "this is a precision instrument" — not "this is a friendly app." When an analyst presents results to their director, the interface should look like a tool a professional would trust.

Key traits:
- **Confident, not boastful** — "This helps" not "this changes everything"
- **Precise, not cold** — Data-forward but warm enough to be approachable
- **Minimal, not bare** — Every visual element communicates information; nothing is decorative
- **Scientific, not academic** — Professional and modern, not dry or dated

### Core Taglines

| Context | Copy |
|---------|------|
| **Primary tagline** | See the impact before the vote. |
| **Hero headline (website)** | See who your policy actually helps. |
| **Primary subheadline** | Connect open data to policy models. See distributional impact. No coding, no waiting. |
| **Closing statement** | The next time someone asks "who does this policy actually help?" — they'll be able to answer. |
| **Short alt** | Make impact visible. |
| **Values statement** | Open-source. Open-data-first. France and Europe. |

---

## 2. Logo

### Concept

The logo is a bimodal dot histogram — a simplified version of the classic economic distribution chart, reimagined as a brand mark.

- **Dots** = individuals in a population
- **Bimodal curve** = distributional impact of a reform (two distinct groups affected differently)
- **Mixed slate/emerald colors** = two overlapping policy outcomes visible simultaneously
- **Histogram shape** = the signature visual of microsimulation and distributional analysis

### Icon Mark

A histogram made of stacked circles (dots) forming a smooth bimodal distribution — two gentle bumps of unequal height (left bump smaller, right bump larger), connected by a graceful valley. Approximately 11 columns for shape smoothness. Column heights follow a smooth continuous curve with no jagged transitions — each column differs from its neighbor by at most one dot.

Each dot is independently colored either **Slate** (`#334155`) or **Emerald** (`#10B981`), mixed throughout the distribution. No pattern — the mix is organic.

Style: flat vector, uniform dot size, consistent horizontal and vertical spacing, white background. No effects, no shadows, no gradients.

### Wordmark

"**ReformLab**" in Inter (semibold, 600 weight), Slate `#334155`, placed below the icon mark. Clean, no effects.

### Logo Colors

The logo uses exactly two colors:

| Color | Name | Hex | Tailwind |
|-------|------|-----|----------|
| Dark | Slate 700 | `#334155` | `slate-700` |
| Accent | Emerald 500 | `#10B981` | `emerald-500` |

These are **brand mark colors** — fixed and non-negotiable. They do not change across touchpoints.

Note: the logo's Emerald 500 also serves as the "success/validated" semantic color across the application and presentations, creating a natural link between the brand mark and the product's visual language.

### Usage Rules

- **Background:** White only (for now). Do not place on colored or photographic backgrounds.
- **Minimum clear space:** Equal to the height of one dot in the histogram on all sides.
- **Minimum size:** Icon mark should not be rendered smaller than 24px in height for digital, 10mm for print.
- **Do not:** Rotate, skew, apply effects (shadow, glow, outline), substitute colors, add a background shape, stretch/distort, or rearrange the dots.

### Generation Prompt (Ideogram)

See [Appendix A](#appendix-a-generation-prompts) for the full generation prompt.

---

## 3. Color System

### Palette Philosophy

Confidence through clarity. Colors serve as a functional language — they communicate data state, not decoration. The palette is deliberately restrained to let data speak.

### Complete Palette Reference

| Name | Hex | RGB | Tailwind | Primary Role |
|------|-----|-----|----------|-------------|
| White | `#FFFFFF` | 255, 255, 255 | `white` | Primary background, content areas |
| Slate 50 | `#F8FAFC` | 248, 250, 252 | `slate-50` | Panel chrome, card backgrounds, secondary surfaces |
| Slate 100 | `#F1F5F9` | 241, 245, 249 | `slate-100` | Collapsed panel rails |
| Slate 200 | `#E2E8F0` | 226, 232, 240 | `slate-200` | Borders (panels, containers) |
| Slate 300 | `#CBD5E1` | 203, 213, 225 | `slate-300` | Interactive borders (inputs, selects), flow connectors |
| Slate 400 | `#94A3B8` | 148, 163, 184 | `slate-400` | Neutral/baseline data in charts |
| Slate 500 | `#64748B` | 100, 116, 139 | `slate-500` | Secondary text, labels, panel headers, icon default color |
| Slate 700 | `#334155` | 51, 65, 85 | `slate-700` | Logo color, medium emphasis text |
| Slate 900 | `#0F172A` | 15, 23, 42 | `slate-900` | Primary text, titles |
| Blue 50 | `#EFF6FF` | 239, 246, 255 | `blue-50` | Selection highlight background |
| Blue 500 | `#3B82F6` | 59, 130, 246 | `blue-500` | Primary accent, CTAs, Reform A, focus, information |
| Blue 600 | `#2563EB` | 37, 99, 235 | `blue-600` | Primary button fill |
| Violet 500 | `#8B5CF6` | 139, 92, 246 | `violet-500` | Secondary accent, Reform B, lineage highlight |
| Emerald 500 | `#10B981` | 16, 185, 129 | `emerald-500` | Success, validated, Reform C, logo accent |
| Amber 500 | `#F59E0B` | 245, 158, 11 | `amber-500` | Warning, caution, Reform D |
| Red 500 | `#EF4444` | 239, 68, 68 | `red-500` | Error, failure, negative outcomes |

### Semantic Color Tokens (Application UI)

These tokens define what colors *mean* in the application context:

| Token | Role | Usage |
|-------|------|-------|
| `slate` (all shades) | Neutral UI chrome | Backgrounds, borders, text — workspace scaffolding |
| `emerald` | Validated / success | Validated configs, passing checks, completed runs, baseline values |
| `amber` | Actionable warning | Stale cache, boundary values, requires attention |
| `stone-400` + icon | Unreviewed defaults | Default assumptions not yet confirmed — normal, not alarming |
| `red` | Error / failure | Failed runs, validation errors, broken lineage |
| `blue` | Information / selection | Selected items, focus, information callouts |
| `blue` + focus ring | Active editing | `ring-2 ring-blue-500` on parameter fields in edit mode |
| `violet` | Lineage highlight | Upstream dependency chain, reform-diff indicators |
| `sky` | Reform / delta | Reform scenario overlay, parameter-differs-from-baseline |

### Chart Color Palette

When showing scenario comparisons or multi-series data, use the context-appropriate color order:

**Application UI chart color order:**

| Position | Scenario | Color | Hex |
|----------|----------|-------|-----|
| 1 | Baseline | Slate 400 | `#94A3B8` |
| 2 | Reform A | Blue 500 | `#3B82F6` |
| 3 | Reform B | Violet 500 | `#8B5CF6` |
| 4 | Reform C | Emerald 500 | `#10B981` |
| 5 | Reform D | Amber 500 | `#F59E0B` |

**Presentation chart color order:**

| Position | Scenario | Color | Hex |
|----------|----------|-------|-----|
| 1 | Baseline | Slate 400 | `#94A3B8` |
| 2 | Reform A | Emerald 500 | `#10B981` |
| 3 | Reform B | Blue 500 | `#3B82F6` |
| 4 | Reform C | Violet 500 | `#8B5CF6` |
| 5 | Reform D | Amber 500 | `#F59E0B` |

**Rationale:** In presentations, Emerald 500 leads as the primary reform accent to maintain visual continuity with the brand mark (logo). In the application UI, Blue 500 leads because it signals interactivity and focus. Both orders keep Slate 400 as baseline and Amber 500 as the final position.

Maximum 5 scenarios overlaid before visual degradation — enforced by the UI.

**CSS custom properties (application):**

```css
:root {
  --chart-baseline: #94A3B8;  /* slate-400 */
  --chart-reform-a: #3B82F6;  /* blue-500 */
  --chart-reform-b: #8B5CF6;  /* violet-500 */
  --chart-reform-c: #10B981;  /* emerald-500 */
  --chart-reform-d: #F59E0B;  /* amber-500 */
}
```

### Color Usage Rules

- **No gradients.** Anywhere. Ever.
- **No textures or patterns** on backgrounds.
- **No information conveyed by color alone.** Every state uses color + icon or color + label (WCAG 2.1 AA).
- **Contrast:** All text meets 4.5:1 minimum on its background. Tailwind 500–900 range for text on light backgrounds.
- Highlight cells in tables: Emerald for positive outcomes, Red for negative, Amber for neutral/cautionary.

---

## 4. Typography

### Font Stack

| Font | Role | Characteristics |
|------|------|----------------|
| **Inter** | All UI text, headings, labels, body copy | Proportional sans-serif, screen-optimized, professional. Excellent at small sizes for dense data interfaces. |
| **IBM Plex Mono** | All numeric data, parameter values, code, IDs, hashes | Monospace. Tabular figures for column alignment. No ligatures that confuse numeric expressions (`>=`, `!=`). Designed for data-heavy enterprise interfaces. |

**No serif fonts.** The interface is functional, not editorial. This applies to all touchpoints.

### Application UI Type Scale

| Level | Size | Tailwind | Weight | Font | Usage |
|-------|------|----------|--------|------|-------|
| Page title | 20px | `text-xl` | Semibold (600) | Inter | Scenario name, workspace title |
| Section header | 18px | `text-lg` | Semibold (600) | Inter | Panel headers |
| Subsection | 16px | `text-base` | Medium (500) | Inter | Parameter group names, chart titles |
| Body / labels | 14px | `text-sm` | Normal (400) | Inter | Labels, descriptions, axis labels |
| Data values | 14px | `text-sm` | Medium (500) | IBM Plex Mono | Parameter values, indicator numbers, table cells |
| Metadata | 12px | `text-xs` | Normal (400) | Inter or Mono | Timestamps, version IDs, run hashes |

### Presentation Type Scale

| Level | Size | Weight | Font | Usage |
|-------|------|--------|------|-------|
| Slide title | 28–32pt | Semibold (600) | Inter | One per slide, top-left or top-center |
| Subtitle / tagline | 18–20pt | Normal (400) | Inter | Below title when needed |
| Body / labels | 16–18pt | Normal (400) | Inter | Bullet points, descriptions |
| Data values | 16–18pt | Medium (500) | IBM Plex Mono | Numbers, metrics, code snippets |
| Minimum allowed | 14pt | — | — | Absolute floor — nothing smaller |

### Data Hierarchy Convention

This convention applies everywhere — application UI, presentations, tables, charts:

- **Labels** use `font-normal` (400 weight) — they describe what something is
- **Data values** use `font-medium` (500 weight) — they show what the value is

This consistent weight difference creates a scannable rhythm: the eye instantly distinguishes "what is this" from "what is the value."

### Line Height

- **Tight** (`leading-tight` / 1.25): data tables, parameter panels, dense content
- **Normal** (`leading-normal` / 1.5): descriptive text, help content, long-form copy

### Font Fallbacks

| Context | Primary | Fallback |
|---------|---------|----------|
| Application (web) | Inter | System sans-serif (`-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif`) |
| Application (mono) | IBM Plex Mono | `Consolas, Monaco, monospace` |
| Presentations (PPTX) | Inter | Calibri |
| Presentations (mono) | IBM Plex Mono | Consolas |

### Typography Rules

- **Minimum font size in presentations:** 14pt. If content doesn't fit at 14pt, reduce the content, never the font size.
- **Minimum font size in application:** 12px — metadata only. All functional text is 14px+.
- **Numbers always in monospace.** In every context: tables, charts, parameter displays, badges, indicators.
- **No decorative typography.** No letter-spacing effects, no all-caps body text. Panel headers use `uppercase tracking-wide` as a subtle structural signal — this is the only exception.

---

## 5. Visual Style Principles

### Design Direction

**"Dense Terminal with selective softening."** The workspace is a professional instrument optimized for sustained analytical sessions. Visual decoration is minimized to maximize data visibility. The overall feel is closer to VS Code or dbt Cloud than to Notion or Linear.

### What We Do

- Flat vector graphics and clean illustrations
- White or Slate 50 backgrounds — clean, breathable
- Functional 1px borders (`border-slate-200`) to define structure
- Line-style icons with consistent stroke weight
- Data-first layouts where charts and tables dominate
- Monospace font for all numbers and data values
- Generous margins in presentations (0.5" minimum)
- Slight rounding on interactive components (`rounded-md`) for approachability

### What We Do NOT Do

- No photography — this is a data product
- No gradients, textures, or patterns
- No decorative elements — no swooshes, geometric shapes for decoration, background graphics
- No shadows on static layout elements (shadows are reserved for floating elements only)
- No filled/solid icons — line-style only
- No custom animations beyond functional chart transitions
- No brand logo or marketing elements inside the application workspace
- No 3D effects on charts or illustrations

### Borders and Surfaces

| Element | Style |
|---------|-------|
| Panel containers | 1px `border-slate-200`, square corners |
| Interactive components (buttons, inputs, cards) | `rounded-md` (Shadcn/ui default), 1px `border-slate-300` |
| Slide frames | Square corners |
| Cards/panels in presentations | 4–8px radius |

### Background Hierarchy

| Surface | Color | Meaning |
|---------|-------|---------|
| Active content | White (`bg-white`) | "This is content you work with" |
| Chrome / sidebars | Slate 50 (`bg-slate-50`) | "This is navigation or context" |
| Collapsed panel rails | Slate 100 (`bg-slate-100`) | "This is minimized structure" |
| Presentation accent panels | Slate 50 (`bg-slate-50`) | Card backgrounds, sidebar areas |

### Shadows

- **Dropdowns, popovers:** `shadow-md`
- **Modals, dialogs:** `shadow-lg`
- **Everything else:** No shadow. Never on static layout elements, cards, or panels.

### Motion and Animation

- Chart transitions: **150ms ease-out** — fast enough to feel instant, slow enough to show what changed
- All animations respect `prefers-reduced-motion` media query
- No custom page transitions, no loading animations beyond skeleton placeholders
- No animated backgrounds, no parallax, no scroll-triggered effects

---

## 6. Icons and Imagery

### Icon Set

**Lucide** — the default icon set for Shadcn/ui. No other icon sets in the product. No custom icons in MVP.

### Icon Style Rules

- **Line-style only** — never filled or solid icons
- **Consistent stroke weight** across all icons
- **Colors:** Slate 500 by default, or accent colors when communicating semantic state
- **Size:** Match the surrounding text size. No oversized decorative icons.

### State Indicators

Every semantic state uses color + icon — never color alone:

| State | Color | Icon |
|-------|-------|------|
| Validated / success | Emerald | Checkmark |
| Actionable warning | Amber | Triangle |
| Unreviewed default | Stone 400 | Clock or eye |
| Error / failure | Red | X |
| Active lineage | Violet | Solid border (not just color) |
| Active editing | Blue | Focus ring + border change |

### Imagery Philosophy

- **No photography.** Anywhere. Not on the website, not in presentations, not in the product.
- **No stock illustrations** or decorative graphics.
- **Diagrams and charts only** — every visual element communicates information.
- **Abstract illustrations** are acceptable only when they represent data concepts (e.g., a stylized before/after showing households, a pipeline diagram).

---

## 7. Layout Principles

### Spacing System

**Base unit:** 4px (`space-1` in Tailwind). All spacing uses multiples of 4px.

| Context | Token | Value |
|---------|-------|-------|
| Between panels | `gap-1` | 4px |
| Within panels — section gap | `gap-4` | 16px |
| Within sections — item gap | `gap-2` | 8px |
| Parameter rows | `py-1.5` | 6px vertical padding |
| Card padding | `p-3` | 12px (tighter than Shadcn default) |

### Application Layout

**Three-column workspace:**

| Column | Width | Purpose |
|--------|-------|---------|
| Left panel | 280–320px | Parameters, scenario selector, model config |
| Main content | Flexible (fill remaining) | Charts, comparison views, lineage DAG |
| Right panel | 280–360px | Context, metadata, lineage details |

Side panels collapse to 48px icon rails at narrow viewports. Hover or click to expand.

### Density Philosophy

This is a data-dense analytical tool. Default density is tighter than typical Shadcn/ui — closer to VS Code or Bloomberg Terminal than to Notion. White space separates semantic groups, not fills screen space.

### Breakpoints

Desktop-first. No mobile or tablet layouts.

| Viewport | Width | Behavior |
|----------|-------|----------|
| Large desktop | 1920px+ | All three columns, generous spacing |
| Standard desktop | 1440–1919px | All three columns, comfortable density |
| Laptop | 1366–1439px | Side panels auto-collapse to icon rails |
| Small laptop | 1280–1365px | Panels collapsed by default |
| Below 1280px | — | Not supported (warning shown) |

### Presentation Layout

- **Aspect ratio:** 16:9 widescreen
- **Format:** PPTX
- **Margins:** 0.5 inch minimum on all sides. Content never extends to slide edges.
- **Slide dimensions:** 13.333 x 7.5 inches

---

## 8. Chart and Data Visualization

### Chart Color Order

Always use this order when showing scenarios:

1. **Baseline:** Slate 400 (`#94A3B8`) — neutral, recedes visually
2. **Reform A:** Blue 500 (`#3B82F6`) — primary comparison
3. **Reform B:** Violet 500 (`#8B5CF6`) — secondary comparison
4. **Reform C:** Emerald 500 (`#10B981`) — tertiary
5. **Reform D:** Amber 500 (`#F59E0B`) — quaternary

Maximum 5 scenarios. This order is the same across application UI, presentations, and any other data visualization context.

### Chart Typography

- **All numbers** in IBM Plex Mono (monospace), `font-medium` (500)
- **Axis labels** in Inter, `text-sm`, `font-normal` (400)
- **Chart titles** in Inter, `text-base`, `font-medium` (500)
- **Legends** in Inter, `text-sm`, `font-normal` (400)

### Chart Style Rules

- No 3D effects — ever
- No decorative gridlines — functional gridlines only, in Slate 200
- No chart borders or outer frames
- Highlight cells in data tables: Emerald for positive, Red for negative, Amber for neutral
- Positive contributions in charts: Emerald. Negative contributions: Red.
- Connectors and flow arrows: Slate 300, simple straight or curved lines. Not decorative.

### Data Table Styling

| Element | Style |
|---------|-------|
| Header row | Slate 50 background, `font-semibold` |
| Body rows | White background |
| Borders | 1px Slate 200 |
| Numbers | Monospace, right-aligned |
| Highlight cells | Accent colors (Emerald/Red/Amber) |

### Chart Rendering (Application)

- **Primary:** Recharts (SVG) for distributional bar charts, waterfall charts, line charts with < 5,000 data points
- **Fallback:** Nivo (canvas) for scatter plots and large datasets
- Both consume the same CSS custom property tokens for color consistency

---

## 9. Brand Voice and Tone

### Tone Philosophy

**Pragmatic optimism.** Don't oversell. Don't claim to save the world. Claim to make one specific thing work better.

- The bigger picture (better policies, distributive justice) is a *consequence*, not a pitch
- "This helps" — not "this changes everything"
- The emotional high point is practical: someone does their job better. A policy gets assessed that wouldn't have been. That's enough. That's real.

### Audience-Specific Voice

| Audience | Tone | Approach |
|----------|------|----------|
| **Expert / Institutional** | Peer-to-peer, technically credible, visionary | "You know this problem. Here's what's finally possible." Technical terms welcome. Don't over-explain the problem — spend more time on the solution. |
| **General Public** | Personal, warm, concrete | Lucas explaining to family why this matters. No jargon. Concrete examples. "Let me show you what I'm building and why." |
| **Investor** | Confident, opportunity-focused, evidence-backed | "Here's a gap no one has filled in Europe." Quiet urgency, not hype. |

### Terminology Conventions

| Term | When to use | When NOT to use |
|------|------------|-----------------|
| Microsimulation | Expert/institutional audience only | Public or investor contexts |
| Policy impact modeling | Public, investor, and general contexts | — |
| OpenFisca | Expert audience, technical docs | Public-facing copy (say "proven modeling engines" instead) |

**The canonical metaphor:** "OpenFisca is the engine. ReformLab is the car — dashboard, navigation, and all."

### Writing Style Rules

- First person (Lucas speaking) for emails and personal outreach
- Warm but professional — never overly casual, never corporate
- No time estimates for delivery or development in any external communication
- No jargon in public-facing copy; technical terms welcome in expert contexts
- Respect the audience's competence — frame as making existing work easier, not fixing something broken
- Short sentences. Clear structure. No fluff.

---

## 10. Canonical Copy

### Recommended Final Selections

| Element | Selected Copy |
|---------|--------------|
| **Hero headline** | See who your policy actually helps. |
| **Subheadline** | Connect open data to policy models. See distributional impact. No coding, no waiting. |
| **Problem header** | The data is there. The tooling isn't. |
| **Solution header** | How it works |
| **Audience header** | Built for the people closest to policy |
| **Transformation header** | From months to minutes |
| **Why now header** | Why now |
| **Comparison header** | Nothing like this exists in Europe |
| **About header** | Why this exists |
| **Hero CTA (primary)** | Get Started |
| **Hero CTA (secondary)** | See How It Works |
| **Closing CTA (primary)** | Start Your First Analysis |
| **Closing CTA (secondary)** | View on GitHub |
| **Pre-launch CTA** | Get Early Access |
| **Closing statement** | The next time someone asks "who does this policy actually help?" — they'll be able to answer. |

### Alternate Headlines

For A/B testing or different contexts:

- "Billions spent. Nobody checked." (provocative)
- "You designed the policy. You should be able to assess it." (empowerment)
- "The data is public. The answers shouldn't take months." (frustration-to-solution)

### Alternate Subheadlines

- "From raw public data to who-wins-who-loses reports — in minutes, not months."
- "Built for policy analysts who shouldn't need to become data engineers."

### Alternate Closing Statements

- "Make impact visible." (three words, memorable)
- "Open-source. Open-data-first. France and Europe." (identity statement)

---

## 11. Application UI Guidelines

### Technology Stack

- **React 18+** with TypeScript
- **Shadcn/ui** — copy-paste component library built on Radix UI primitives
- **Tailwind CSS v4** — utility-first styling with design tokens
- **Radix UI** — accessible primitive layer (used by Shadcn/ui internally)
- **Lucide** — icon set

Design-in-code workflow: no Figma. Components live in the project source. Iterate in the browser.

### Standard Shadcn/ui Components (used as-is)

Button, Input, Select, Slider, Switch, Dialog, Popover, Tooltip, Card, Table, Tabs, Badge, Collapsible, Sheet, Separator, ScrollArea, ResizablePanel, Command.

No customization beyond design tokens.

### Button Hierarchy

| Level | Style | Usage |
|-------|-------|-------|
| Primary | `bg-blue-600 text-white` (filled) | Single most important action per view (Run, Export, Validate) |
| Secondary | `border-slate-300 text-slate-700` (outline) | Supporting actions (Clone, Compare, Add) |
| Tertiary | `text-slate-500` (ghost) | Navigation, Cancel, Collapse |
| Destructive | `border-red-300 text-red-600` (outline) | Delete, Remove, Reset — always require confirmation |
| Icon-only | Ghost + Lucide icon + tooltip | Dense areas: row actions, card actions |

**Rule:** Never show two filled (primary) buttons in the same view.

### Component Customizations from Shadcn/ui Defaults

| Change | Default | ReformLab |
|--------|---------|-----------|
| Card shadow | `shadow-sm` | `shadow-none` |
| Card padding | `p-4` | `p-3` |
| Density | Standard | Tighter than default |

Everything else (buttons, inputs, selects, dialogs) keeps Shadcn/ui defaults.

### Tailwind Token Extensions

Extend the default Tailwind theme with:

- **Confidence-palette colors:** emerald for validated, amber for warnings, blue for information
- **Simulation-state colors:** sky for reform/delta, violet for lineage, stone for unreviewed
- **Data-quality indicators:** using the semantic tokens defined in the Color System section

### Styling Rules

- **Tailwind-only.** No CSS modules, no styled-components, no inline styles.
- **Panel headers:** `text-sm font-semibold uppercase tracking-wide text-slate-500` — subtle, receding, letting content dominate. No background fills or accent colors on headers.
- **No brand logo or marketing elements** inside the application workspace.
- **No onboarding overlays or tooltips** — the template-first approach teaches by doing.

---

## 12. Presentation Guidelines

### Format

- **Aspect ratio:** 16:9 widescreen
- **File format:** PPTX (PowerPoint)
- **Slide margins:** 0.5 inch minimum on all sides
- **Content:** Never extends to slide edges

### Presentation Accent Color

**Emerald 500 (`#10B981`) is the primary accent color in all presentations.** This aligns the presentation visual identity with the brand mark (logo), creating immediate recognition.

- **Primary accent / Reform A highlight:** Emerald 500 (`#10B981`)
- **Secondary accent (when needed):** Blue 500 (`#3B82F6`)
- **Positive outcomes in data:** Emerald 500
- **Negative outcomes in data:** Red 500 (`#EF4444`)
- **Neutral/cautionary:** Amber 500 (`#F59E0B`)

This differs from the application UI, where Blue 500 is the primary accent (signaling interactivity). In presentations, the goal is brand cohesion, not interactivity — so the logo's Emerald leads.

### Hard Constraints (Non-Negotiable)

1. **Minimum font size: 14pt.** Nothing smaller — if content doesn't fit, reduce the content.
2. **Everything is graphical.** No slide may be a wall of text. Visuals are primary communication.
3. **Slide titles carry meaning.** Never generic ("Problem", "Solution"). Every title communicates the takeaway.
4. **Maximum 6 text elements per slide.** More than 6 → split into two slides or convert to visual.
5. **No paragraphs.** No element exceeds 2 lines of text.

### Slide Title Examples

| Generic (never use) | Meaningful (always use) |
|---------------------|------------------------|
| "The Problem" | "Every policy assessment starts from scratch" |
| "Our Solution" | "End-to-end assessment — no code required" |
| "Features" | "What makes ReformLab different" |
| "Target Audience" | "Three groups need fast, rigorous answers" |
| "Competition" | "The field is clearing — and no one occupies this space" |

### Layout Patterns

**Pattern 1 — Statement + Visual:** Title as full sentence. One large visual (60–70% of slide). Optional supporting line below.

**Pattern 2 — Comparison Grid:** Title. 2–4 columns with icon + label + short description each. Consistent alignment.

**Pattern 3 — Before/After Split:** Left half = "before" (Slate 50 bg, Slate 500 text). Right half = "after" (White bg, Emerald 500 accents). Title spans full width.

**Pattern 4 — Data Table:** Title. Clean table: Slate 50 header, White body, 1px Slate 200 borders. Accent colors for highlight cells. Numbers in monospace.

**Pattern 5 — Flow/Process:** Title. 3–5 steps, horizontal or vertical. Icon + label + optional description per step. Slate 300 arrow connectors.

**Pattern 6 — Quote/Testimonial:** Large quote (20–24pt, Slate 700). Emerald 500 quotation marks. Slate 50 background with Emerald 500 left border.

**Pattern 7 — Positioning Map:** Title. 2x2 quadrant with labeled axes. ReformLab highlighted in Emerald 500. Its quadrant subtly highlighted with Emerald 50 background.

### Speaker Notes

Every slide includes:
- Key talking point (what to say)
- Emotional beat (what the audience should feel)
- Transition phrase to the next slide

### Quality Checklist

- [ ] Title communicates the slide's takeaway
- [ ] No text smaller than 14pt
- [ ] No more than 6 text elements
- [ ] No text block exceeds 2 lines
- [ ] Primary communication is visual
- [ ] Colors match the palette
- [ ] Numbers use monospace font
- [ ] Chart colors follow the defined order
- [ ] Speaker notes included
- [ ] No decorative elements

---

## Appendix A: Generation Prompts

### Logo Generation Prompt (Ideogram)

#### Icon Only (No Text)

```
Minimal geometric logo icon. A histogram made of stacked circles (dots) forming a smooth bimodal distribution — two gentle bumps of unequal height (left bump smaller, right bump larger), connected by a graceful valley between them. Column heights follow a smooth continuous curve with no jagged transitions — each column differs from its neighbor by at most one dot. Each dot is independently colored either slate-gray (#334155) or emerald-green (#10B981), mixed throughout the distribution. Approximately 11 columns for smoother shape. Flat vector, uniform dot size, consistent horizontal and vertical spacing, no text, white background. Elegant, scientific, minimal, modern.
```

#### With Wordmark

Same icon concept, with "ReformLab" wordmark below in Inter (semibold), slate-gray (`#334155`).

### Presentation Design Prompt

The full presentation design prompt is maintained at:
`_bmad-output/presentations/presentation-design-prompt.md`

Feed this file to an AI assistant alongside a slide content file to generate presentations. The design prompt contains the complete visual identity rules, layout patterns, and quality checklist for PPTX generation.

**Usage prompt (copy-paste to start a presentation session):**

> I need you to create a PowerPoint presentation (PPTX file) for my product ReformLab. I'm going to give you two files: 1. A design prompt with hard constraints, visual identity, layout patterns, and quality rules. 2. The slide-by-slide content for the deck. Read both files completely before generating anything. The design prompt overrides any default presentation habits — follow it exactly.

### Python Generator Constants

For programmatic PPTX generation, the canonical color and font constants:

```python
# Colors
WHITE      = (0xFF, 0xFF, 0xFF)  # #FFFFFF
SLATE_50   = (0xF8, 0xFA, 0xFC)  # #F8FAFC
SLATE_200  = (0xE2, 0xE8, 0xF0)  # #E2E8F0
SLATE_300  = (0xCB, 0xD5, 0xE1)  # #CBD5E1
SLATE_400  = (0x94, 0xA3, 0xB8)  # #94A3B8
SLATE_500  = (0x64, 0x74, 0x8B)  # #64748B
SLATE_700  = (0x33, 0x41, 0x55)  # #334155
SLATE_900  = (0x0F, 0x17, 0x2A)  # #0F172A
BLUE_50    = (0xEF, 0xF6, 0xFF)  # #EFF6FF
BLUE_500   = (0x3B, 0x82, 0xF6)  # #3B82F6
VIOLET_500 = (0x8B, 0x5C, 0xF6)  # #8B5CF6
EMERALD_500= (0x10, 0xB9, 0x81)  # #10B981
AMBER_500  = (0xF5, 0x9E, 0x0B)  # #F59E0B
RED_500    = (0xEF, 0x44, 0x44)  # #EF4444

# Fonts (PPTX fallbacks — canonical fonts are Inter and IBM Plex Mono)
FONT_HEADING = "Calibri"   # Fallback for Inter
FONT_BODY    = "Calibri"   # Fallback for Inter
FONT_MONO    = "Consolas"  # Fallback for IBM Plex Mono

# Slide dimensions (16:9)
SLIDE_WIDTH  = 13.333  # inches
SLIDE_HEIGHT = 7.5     # inches
MARGIN       = 0.6     # inches
```

---

## Appendix B: Source File Reference

This guide was synthesized from the following source files. This guide is the canonical reference — in case of any discrepancy, this document takes precedence.

| Source File | Contributed To |
|-------------|---------------|
| `_bmad-output/branding/logo-prompt.md` | Section 2 (Logo), Appendix A |
| `_bmad-output/presentations/presentation-design-prompt.md` | Sections 3, 4, 5, 8, 12, Appendix A |
| `_bmad-output/presentations/generate_pitch_deck.py` | Sections 3, 4, Appendix A (Python constants) |
| `_bmad-output/planning-artifacts/ux-design-specification.md` | Sections 3, 4, 5, 6, 7, 8, 11 |
| `_bmad-output/communication/audience-narratives-2026-02-25.md` | Sections 1, 9 |
| `_bmad-output/website-content/copy-variations-2026-02-25.md` | Sections 1, 10 |
| `_bmad-output/website-content/homepage-narrative-2026-02-25.md` | Sections 1, 10 |

### Resolved Discrepancies

1. **Chart baseline color:** The UX spec used `slate-500` in CSS custom properties while the presentation spec used Slate 400 (`#94A3B8`). This guide standardizes on **Slate 400 (`#94A3B8`)** as the chart baseline across all touchpoints — it was the deliberate choice in the more recent presentation spec and provides better visual recession for baseline data.

2. **Logo colors vs. UI accent vs. presentation accent:** The logo uses Slate 700 + Emerald 500 (brand mark colors, fixed). The application UI uses Blue 500 as primary accent (signals interactivity). Presentations use Emerald 500 as primary accent (brand cohesion with logo). Three contexts, one clear rule each — see Section 8 (Chart Color Palette) and Section 12 (Presentation Accent Color) for the full specification.

3. **Wordmark font:** The logo prompt said "Inter or similar." This guide canonizes **Inter** as the wordmark font.

4. **Font fallbacks:** Inter and IBM Plex Mono are canonical. Calibri and Consolas are PPTX-specific fallbacks for environments where the canonical fonts are not installed.
