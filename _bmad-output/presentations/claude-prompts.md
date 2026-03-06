# Claude Prompts — ReformLab Presentations

---

## Phase 1 — Explore Design Directions

Use these prompts to audition different presentation styles before committing to a template.

### Prompt 1a — Generate Style Options

```
I'm designing the presentation template for ReformLab, a policy impact modeling platform.

Attached file:
- _bmad-output/branding/visual-identity-guide.md — brand colors, typography, and voice. Use its color palette and fonts as the foundation.

Generate 3 visually distinct HTML files, each containing the same 3 sample slides:
1. A title slide (product name + tagline)
2. A content slide with a diagram or chart
3. A comparison slide (before/after or grid layout)

Each file should be a complete self-contained HTML presentation (inline CSS/JS, arrow key navigation, fullscreen sections).

The 3 design directions:

Option A — "Minimal Precision": Maximum whitespace, ultra-clean, content floats in space. Think scientific paper meets Apple keynote. Subtle, confident.

Option B — "Data Dashboard": Dense, structured, panel-based layouts with visible grid. Feels like a professional analytics tool turned into slides. Information-rich.

Option C — "Bold Editorial": Strong typographic hierarchy, large statement titles, dramatic use of accent color. High contrast, punchy. Feels like a magazine spread.

Name each file option-a.html, option-b.html, option-c.html.
```

### Prompt 1b — Explore a Direction Further

```
I like Option [X]. Generate 3 variations of it:
- Variation 1: as-is but with [specific tweak — e.g. "darker backgrounds", "more color accents", "tighter spacing"]
- Variation 2: push it further — more extreme version of the same direction
- Variation 3: soften it — more conservative, safer version

Same 3 sample slides. Name files variation-1.html, variation-2.html, variation-3.html.
```

### Prompt 1c — Lock In the Template

```
I'm going with [Option/Variation]. This is now the ReformLab presentation template.

Extract the design system from this file into a reusable CSS block at the top:
- All CSS custom properties (colors, fonts, spacing, transitions)
- Slide layout classes (title-slide, content-slide, comparison-slide, data-slide, flow-slide, quote-slide)
- Typography scale
- Reusable component styles (cards, badges, chart containers, flow arrows)

Output a single clean template.html with placeholder slides demonstrating each layout class.
```

---

## Phase 2 — Generate Presentations

### Prompt 2a — Generate Full Presentation

```
Create an HTML presentation for ReformLab using the locked-in template style.

Attached files:
1. _bmad-output/branding/visual-identity-guide.md — brand identity source of truth.
2. [slide content file — e.g. pitch-deck-content-2026-02-25.md]
3. [template.html if available — use its design system]

Output: single self-contained HTML file. Inline everything.

Technical spec:
- Each slide = one <section>, fullscreen, one visible at a time
- Arrow keys + click to navigate. Slide counter bottom-right
- Speaker notes: hidden <aside class="speaker-notes"> per section, toggle with 'S' key
- @media print: each section on its own page
- Charts/diagrams: inline SVG or CSS only
```

### Prompt 2b — Quality Review

```
Review the HTML against these rules:
- Every title is a meaningful takeaway (never generic like "Problem" or "Solution")
- No text below 14pt equivalent
- Max 6 text elements per slide
- No text block over 2 lines
- Every slide is primarily visual
- Colors and fonts match the brand guide
- Speaker notes on every slide

Fix violations. Output corrected full HTML.
```

---

## Phase 3 — Iterate

### Prompt 3a — Modify Specific Slides

```
Improve these slides. Regenerate only the affected <section>(s), keep the rest untouched.

Changes:
[e.g. "Slide 3: replace bullets with before/after split", "Slide 7: add animated chart reveal"]
```

### Prompt 3b — PPT Export (Optional)

```
Generate a Python script (python-pptx) that recreates this presentation as .pptx.
Match the HTML design as closely as PowerPoint allows. Include speaker notes.
Use color/font constants from the visual identity guide's Appendix A.
```

---

## Tips

- **Phase 1 is fast** — 3 options × 3 sample slides each. Compare in browser, decide quickly.
- **Iterate slide-by-slide** in Phase 3 rather than regenerating everything.
- **Present from HTML** for live demos — it's the better experience.
- **PPT only when required** (investor leave-behind, corporate file sharing).
- **Quick PDF:** Chrome → Print → Save as PDF.
- **Presenter mode:** press 'S' to toggle speaker notes.
