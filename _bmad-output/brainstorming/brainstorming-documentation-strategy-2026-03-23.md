---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Documentation hosting and content strategy for open-source readiness'
session_goals: 'Decide hosting approach (GitHub Pages vs integrated), modern OSS docs standards, lean and authentic content — no AI bloat'
selected_approach: 'ai-recommended'
techniques_used: ['First Principles Thinking', 'Six Thinking Hats', 'Constraint Mapping']
ideas_generated: [18]
context_file: ''
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** Lucas
**Date:** 2026-03-23

## Session Overview

**Topic:** Documentation hosting and content strategy for open-source readiness
**Goals:** Decide hosting approach (GitHub Pages vs. integrated), ensure modern OSS docs standards, keep it lean and authentic

### Context Guidance

- MkDocs Material already configured but never deployed
- Separate Astro website at reform-lab.eu (Kamal/Hetzner)
- docs/ has ~20 files mixing internal planning artifacts with developer docs
- Constraint: PRD, architecture, UX spec, epics must stay in docs/ for BMAD module — but excluded from public site
- Swimm considered for architecture walkthroughs
- README, CONTRIBUTING, LICENSE, CITATION.cff already at root

### Session Setup

Decision-oriented brainstorming focused on practical outcomes: what to host, where, and how to keep docs concise for an open-source audience.

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** Documentation strategy with focus on practical decision-making under constraints

**Recommended Techniques:**

- **First Principles Thinking:** Strip assumptions — what does an OSS visitor actually need?
- **Six Thinking Hats:** Evaluate hosting/tooling from six angles (facts, risks, creativity, emotion, benefits, process)
- **Constraint Mapping:** Stress-test the plan against every real constraint

## Technique Execution Results

### First Principles Thinking

**Key Principles Established:**

1. **Show, Don't Document** — The live demo is the primary documentation. Use case gallery is the second front door. Written docs are tertiary. Inverts the typical OSS docs hierarchy.
2. **Two-Beat Audience Journey** — Beat 1 = desire ("what can I get?"), Beat 2 = understanding ("how do the pieces fit?"). The administration persona — not the developer — drives both beats.
3. **Domain Model as Documentation** — 5-6 core objects (Population, Policy, Engine, Simulation, Results) and their relationships, explained visually and interactively, not in prose.
4. **Minimal Public Docs Surface** — GitHub Pages should be small. Internal BMAD artifacts stay internal. Resist the OSS instinct to publish everything.

**Critical Insight:** Primary audience is a civil servant or policy advisor who needs to see that ReformLab can model their scenario. A live demo with clear use cases is worth more than 50 pages of documentation.

### Six Thinking Hats

**White Hat (Facts):**
- MkDocs Material configured but never deployed; Astro website at reform-lab.eu; live app already deployed
- Modern tooling landscape: Starlight (Astro-native docs), Mintlify, Docusaurus, Fumadocs
- Starlight is zero new framework to learn since project already uses Astro

**Red Hat (Gut Feel):**
- Target feel: "warm and inviting like a product tour" — not cold API docs

**Yellow Hat (Benefits):**
- Starlight + MDX supports embedded React components inside static pages
- Guided tour libraries (driver.js, shepherd.js) add product-tour feel for free
- Use case gallery is just content — cheap to build, high impact
- Live demo already deployed — docs just link into it at the right moments

**Black Hat (Risks):**
- Three frontends to maintain (commercial site, docs, app) — mitigated by AI-assisted maintenance
- Interactive domain diagram is custom work — scoped to v2 to avoid blocking launch
- Content bloat creep — mitigated by 5-sentence rule
- Staleness risk — mitigated by linking to demo rather than replicating it

**Green Hat (Creative Ideas):**
- Clickable flowchart / animated walkthrough for domain model (v2)
- Card grid for use cases (App Store card style)
- 5-sentence rule: no page exceeds 5 sentences before a visual or interactive element
- Progressive disclosure: landing page nearly empty, depth one click away
- Expandable "How it works in code" sections — admin never sees code unless they choose to

**Blue Hat (Process Decision):**
- GitHub Pages + Astro Starlight, themed to brand, `docs.reform-lab.eu`
- 6-page public site; BMAD artifacts excluded
- Three separate surfaces: reform-lab.eu (sell) / docs (use) / app (try)

### Constraint Mapping

| Constraint | Resolution |
|---|---|
| BMAD files stay in `docs/` | Starlight lives in its own directory, separate from `docs/` |
| Free or near-free | GitHub Pages + Starlight + OSS libs = $0 |
| Visual identity | Brand guide + theme.css map directly to Starlight custom CSS |
| Concise, no AI bloat | 6 pages max, 5-sentence rule, progressive disclosure |
| One person + AI maintenance | Markdown/MDX files, auto-deploy on push, minimal custom code |
| Build it now | Structure + content first, interactive diagram is v2 |
| Admin persona first | Use case cards + domain model + demo link = front door |
| Code depth on demand | Expandable "How it works" sections, hidden by default |
| `docs.reform-lab.eu` | Custom domain on GitHub Pages, DNS already owned |

## Idea Organization and Prioritization

### Theme 1: Information Architecture — "Show, Don't Document"

- Live demo is the primary front door, not written docs
- Use case card grid (title, one-liner, thumbnail, "Try it") replaces long explanations
- 5-sentence rule enforces brevity on every page
- Progressive disclosure: landing page nearly empty, depth is one click away

### Theme 2: Audience-First Design — "The Admin Persona"

- Primary audience is administration/policy people, not developers
- Two-beat journey: desire then understanding
- Domain model as visual concept map of core objects
- Technical code details hidden by default, expandable on demand

### Theme 3: Tooling & Hosting — "Starlight on GitHub Pages"

- Astro Starlight: known framework, MDX support, easy theming, GitHub Pages deploy
- `docs.reform-lab.eu` custom domain (DNS owned)
- Brand identity from theme.css: Inter + IBM Plex Mono, Blue 600 accent, Emerald 500 brand, Slate surfaces
- Three separate surfaces with distinct purposes

### Theme 4: Scope Control — "6 Pages, No More"

1. **Landing/home** — tagline, domain model visual, "Try the demo" CTA
2. **Use cases** — card grid, 4-6 cards to start
3. **Getting started** — 4-step path (population, policy, engine, simulate)
4. **Domain model** — each object in 5 sentences max, expandable code sections
5. **Contributing** — dev setup, architecture overview, link to CONTRIBUTING.md
6. **API reference** — condensed, expandable, developer-only

### Breakthrough Concept: Interactive Domain Model (v2)

- Clickable flowchart or animated walkthrough of the 5 core objects
- Guided product-tour feel via driver.js/shepherd.js
- Not day-one scope — structure first, interactivity second

## Action Plan

### Priority 1 — Scaffold Starlight site

- Init Starlight in a new directory (e.g. `docs-site/`)
- Apply brand theme (colors, fonts from theme.css)
- Set up GitHub Actions for GitHub Pages deploy
- Configure `docs.reform-lab.eu` custom domain

### Priority 2 — Create the 6 content pages

- Landing page with tagline + domain model diagram (Mermaid v1) + demo CTA
- Getting started: 4-step easy path
- Domain model reference: 5 sentences per object, expandable code sections
- Use case cards: 4-6 to start
- Contributing page
- API reference (condensed)

### Priority 3 — Polish & connect

- Link to live demo from every relevant page
- Ensure warm product-tour tone matches brand voice ("pragmatic optimism")
- Verify dark/light mode works with brand colors

### Priority 4 (v2) — Interactive domain model

- Replace static Mermaid with clickable React/MDX component
- Add guided tour (driver.js or similar)

## Session Summary

**Key Decisions Made:**
- Astro Starlight on GitHub Pages at `docs.reform-lab.eu`
- 6-page public site, BMAD artifacts excluded
- Admin persona is primary audience; developer docs secondary
- Live demo is the real front door; docs support it
- 5-sentence rule and progressive disclosure enforce conciseness
- Brand identity carried through via existing theme.css
- Interactive domain model is v2; Mermaid diagram for v1

**Session Insight:** The most important realization was that the primary docs audience isn't technical — it's an administration person asking "can this answer my policy question?" This inverts the typical OSS documentation approach and keeps the scope naturally small.
