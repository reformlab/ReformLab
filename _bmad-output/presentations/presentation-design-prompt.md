# ReformLab — Presentation Design Prompt

**Purpose:** Instructions for an AI assistant to generate PowerPoint presentations consistent with the ReformLab visual identity.
**Date:** 2026-02-25

---

## How To Use This Prompt

Feed this file to Claude (or any AI assistant capable of generating PPTX) along with a specific pitch deck content file (e.g., `pitch-deck-content-2026-02-25.md`). The content file provides what each slide says. This file provides how every slide should look.

---

## Hard Constraints

These are non-negotiable. Violating any of these makes the presentation unusable.

1. **Minimum font size: 14pt.** Nothing in the presentation — body, labels, captions, footnotes, chart annotations — may be smaller than 14pt. If content doesn't fit at 14pt, reduce the content, never the font size.
2. **Everything is graphical.** No slide may be a wall of text. Every slide uses visual elements as the primary communication: diagrams, icons, charts, comparison layouts, visual metaphors, illustrated workflows. Text supports visuals, never the reverse.
3. **Slide titles carry meaning.** Never use generic titles like "Problem", "Solution", "Audience". Every title is a sentence or phrase that communicates the slide's key takeaway. The audience should understand the point from the title alone before reading anything else.
4. **Maximum 6 text elements per slide.** A "text element" is a bullet point, a label, a short phrase. If a slide has more than 6, split it into two slides or convert text into a visual (diagram, table, icon grid).
5. **No paragraphs on slides.** No element should exceed 2 lines of text. If it takes more than 2 lines to say, it belongs in speaker notes, not on the slide.

---

## Visual Identity

Derived from the ReformLab UX Design Specification. The presentation must feel like it comes from the same product.

### Color Palette

| Role | Color | Hex | Usage in slides |
|------|-------|-----|-----------------|
| Primary background | White | `#FFFFFF` | Slide backgrounds |
| Secondary background | Slate 50 | `#F8FAFC` | Accent panels, sidebar areas, card backgrounds |
| Primary text | Slate 900 | `#0F172A` | Titles, key statements |
| Secondary text | Slate 500 | `#64748B` | Subtitles, descriptions, labels |
| Accent — primary | Blue 500 | `#3B82F6` | Key highlights, Reform A color, CTAs, links |
| Accent — secondary | Violet 500 | `#8B5CF6` | Reform B color, lineage highlights, secondary accents |
| Accent — success | Emerald 500 | `#10B981` | Positive outcomes, validated states, "wins" |
| Accent — warning | Amber 500 | `#F59E0B` | Caution, attention, "costs" |
| Accent — danger | Red 500 | `#EF4444` | Negative outcomes, errors, "losses" |
| Neutral data | Slate 400 | `#94A3B8` | Baseline data, neutral chart elements |

### Chart Colors (in order of use)

When showing scenario comparisons or multi-series data:
- Baseline: Slate 400 (`#94A3B8`) — neutral, recedes
- Reform A: Blue 500 (`#3B82F6`) — primary comparison
- Reform B: Violet 500 (`#8B5CF6`) — secondary comparison
- Reform C: Emerald 500 (`#10B981`) — tertiary
- Reform D: Amber 500 (`#F59E0B`) — quaternary

### Typography

| Level | Font | Size | Weight | Usage |
|-------|------|------|--------|-------|
| Slide title | Inter (or Calibri fallback) | 28-32pt | Semibold (600) | One per slide, top-left or top-center |
| Subtitle / tagline | Inter | 18-20pt | Normal (400) | Below title when needed |
| Body text / labels | Inter | 16-18pt | Normal (400) | Bullet points, descriptions, labels |
| Data values | IBM Plex Mono (or Consolas fallback) | 16-18pt | Medium (500) | Numbers, metrics, code snippets |
| Minimum allowed | Any | 14pt | Any | Absolute floor — nothing smaller |

### Visual Style

- **Borders:** 1px solid, Slate 200 (`#E2E8F0`). Clean, functional. No decorative borders.
- **Corners:** Slightly rounded (4-8px radius) on cards, panels, and containers. Square corners on the slide frame itself.
- **Shadows:** Minimal. Light drop shadow only on floating/overlay elements. Never on flat layout elements.
- **Backgrounds:** Clean white or Slate 50. No gradients, no textures, no patterns.
- **Icons:** Line-style icons (Lucide icon set aesthetic). Consistent stroke weight. Never filled/solid icons. Use Slate 500 or accent colors.
- **Photography:** None. This is a data product — use diagrams, charts, and abstract illustrations instead.
- **Decorative elements:** None. No swooshes, no geometric shapes for decoration, no background graphics. Every visual element communicates information.

---

## Slide Layout Patterns

Use these patterns as the building blocks for every slide. Mix and match as needed.

### Pattern 1: Statement + Visual

- **Top:** Title as a full sentence takeaway (28-32pt, Slate 900)
- **Center:** One large visual element (diagram, chart, illustration) occupying 60-70% of slide area
- **Bottom (optional):** One supporting line of text or a source reference

Use for: Solution slides, "how it works" slides, architecture overviews.

### Pattern 2: Comparison Grid

- **Top:** Title as takeaway
- **Center:** 2-4 columns with icon + label + short description each
- **Consistent alignment:** All icons same size, all labels same weight, all descriptions same size

Use for: Audience segments, differentiators, feature highlights, before/after.

### Pattern 3: Before/After Split

- **Left half:** "Before" state — use Slate 50 background, Slate 500 text, subtle "pain" visual
- **Right half:** "After" state — use White background, Blue 500 accents, clean "solution" visual
- **Title spans full width** above both halves

Use for: Problem → solution transitions, user journey improvements.

### Pattern 4: Data Table

- **Top:** Title as takeaway
- **Center:** Clean table with Slate 50 header row, White body rows, 1px Slate 200 borders
- **Highlight cells:** Use accent colors (Emerald for positive, Red for negative, Amber for neutral)
- **All numbers in monospace font**

Use for: Competitive landscape, feature comparison, gap analysis.

### Pattern 5: Flow / Process

- **Top:** Title as takeaway
- **Center:** Horizontal or vertical flow with 3-5 steps
- **Each step:** Icon + label + optional one-line description
- **Connectors:** Simple arrows or lines in Slate 300, not decorative

Use for: User journey, product workflow, "how it works" sequences.

### Pattern 6: Quote / Testimonial

- **Center:** Large quote in 20-24pt, Slate 700, with quotation marks in Blue 500
- **Below quote:** Attribution line in 16pt Slate 500
- **Background:** Slate 50 with subtle left-border accent in Blue 500

Use for: User persona quotes, emotional hooks, "aha moment" slides.

### Pattern 7: Positioning Map

- **Top:** Title as takeaway
- **Center:** 2x2 quadrant with labeled axes
- **Dots/logos:** Competitors placed in their quadrants, ReformLab highlighted with Blue 500 + label
- **ReformLab's quadrant:** Subtly highlighted with Blue 50 background

Use for: Competitive positioning, market landscape.

---

## Slide Title Examples

These demonstrate the "meaningful title" principle. Never use the left column; always use something like the right column.

| Generic (never use) | Meaningful (always use) |
|---------------------|------------------------|
| "The Problem" | "Every policy assessment starts from scratch" |
| "Our Solution" | "End-to-end assessment — no code required" |
| "Features" | "What makes ReformLab different" |
| "Target Audience" | "Three groups need fast, rigorous answers" |
| "Competition" | "The field is clearing — and no one occupies this space" |
| "Why Now" | "Three forces converging right now" |
| "Next Steps" | "See the impact before the vote" |

---

## Speaker Notes

Every slide should include speaker notes with:
- The key talking point (what to say while showing this slide)
- The emotional beat (what the audience should feel)
- Transition phrase to the next slide

---

## Aspect Ratio and Format

- **Aspect ratio:** 16:9 widescreen
- **Format:** PPTX (PowerPoint)
- **Slide margins:** Generous — at least 0.5 inch on all sides
- **Content area:** Never extend content to slide edges. Maintain breathing room.

---

## Quality Checklist

Before finalizing, verify every slide against this checklist:

- [ ] Title communicates the slide's takeaway as a meaningful phrase
- [ ] No text smaller than 14pt
- [ ] No more than 6 text elements
- [ ] No text block exceeds 2 lines
- [ ] Primary communication is visual, not textual
- [ ] Colors match the palette defined above
- [ ] Numbers use monospace font
- [ ] Chart colors follow the defined order
- [ ] Speaker notes included
- [ ] No generic decorative elements
