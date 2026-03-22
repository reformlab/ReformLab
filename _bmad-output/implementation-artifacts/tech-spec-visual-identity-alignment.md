---
title: 'Visual Identity Alignment Across All Surfaces'
slug: 'visual-identity-alignment'
created: '2026-03-22'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['tailwind-v4', 'astro-5.7', 'react-19', 'vite', 'css-custom-properties', 'fontsource-variable']
files_to_modify:
  - '_bmad-output/branding/theme.css'
  - 'frontend/vite.config.ts'
  - 'frontend/package.json'
  - 'frontend/src/index.css'
  - 'frontend/src/lib/brand-tokens.ts (new)'
  - 'frontend/src/components/simulation/chart-theme.ts'
  - 'website/astro.config.mjs'
  - 'website/package.json'
  - 'website/src/styles/global.css'
  - 'website/src/components/Nav.astro'
  - 'website/src/components/Hero.astro'
  - 'website/src/components/Problem.astro'
  - 'website/src/components/HowItWorks.astro'
  - 'website/src/components/Features.astro'
  - 'website/src/components/BeforeAfter.astro'
  - 'website/src/components/UseCases.astro'
  - 'website/src/components/Comparison.astro'
  - 'website/src/components/WhyNow.astro'
  - 'website/src/components/FAQ.astro'
  - 'website/src/components/Closing.astro'
  - 'website/src/components/Footer.astro'
  - '_bmad/_config/agents/cis-presentation-master.customize.yaml'
  - '_bmad-output/planning-artifacts/ux-design-specification.md'
  - 'docs/ux-design-specification.md'
code_patterns: ['tailwind-v4-theme', 'css-custom-properties', 'fontsource-variable', 'vite-alias', 'shadcn-ui']
test_patterns: ['npm-run-build', 'npm-run-typecheck', 'npm-run-lint', 'visual-spot-check']
---

# Tech-Spec: Visual Identity Alignment Across All Surfaces

**Created:** 2026-03-22

## Overview

### Problem Statement

ReformLab has a comprehensive visual identity guide but it's not enforced. The frontend app, marketing website, and BMAD presentation agent each define their own colors and fonts independently, leading to brand fragmentation. The website is the most divergent — using serif fonts (Playfair Display), different accent colors (amber/teal), and a custom "Ink & Paper" palette instead of the canonical slate system with Inter.

### Solution

Wire a shared `theme.css` (already created at `_bmad-output/branding/theme.css`) into both Tailwind v4 projects via CSS import. Align the website's fonts and palette to the brand guide while preserving marketing-appropriate expression (emerald-led accents, bolder typography, warm touches). Configure the BMAD presentation agent to load the visual identity guide as default context.

### Scope

**In Scope:**
- Frontend app: import shared theme, remove duplicate tokens, fix hardcoded hex values
- Website: switch fonts to Inter/IBM Plex Mono, replace amber/teal palette with brand palette (emerald-led for marketing), import shared theme
- Website: update all 12 Astro components to use new color tokens
- BMAD: configure presentation-master agent customization file
- Verify both projects build and render correctly

**Out of Scope:**
- Redesigning website layout or content
- Mobile/responsive changes
- Creating a npm package or build pipeline for tokens
- Changing the frontend app's blue-led accent strategy
- Logo or imagery changes

## Context for Development

### Codebase Patterns

- Both projects use Tailwind v4 with `@theme` blocks in CSS (CSS-first, no JS config)
- Frontend uses Google Fonts CDN (`@import url(...)` in index.css line 1) for Inter + IBM Plex Mono
- Website uses `@fontsource-variable` packages (devDependencies) for Playfair Display + Source Sans 3
- Website components use CSS custom property references for fonts: `font-[family-name:var(--font-display)]` — no inline `font-family: "Playfair"` found (good — swap is clean)
- Website has ~60 `amber` references and ~20 `teal` references across 12 components
- Frontend chart-theme.ts already uses CSS custom properties for chart colors (`var(--chart-baseline)`, etc.) — only 3 hardcoded hex values remain (lines 47, 53, 59)
- Frontend `src/lib/` directory exists with `utils.ts` — ready for `brand-tokens.ts`
- Frontend Vite config has existing `resolve.alias` at lines 8-12 (currently just `@` → `./src`)
- Website Astro config has `vite: { plugins: [tailwindcss()] }` at lines 5-7 — no `resolve` section yet
- UX design spec duplicated identically in both `_bmad-output/planning-artifacts/` and `docs/` (1405 lines each); visual specs at lines 430-616

### Files to Reference

| File | Purpose | Key Anchors |
| ---- | ------- | ----------- |
| `_bmad-output/branding/theme.css` | Shared theme (source of truth) | `@theme` block + `:root` chart vars |
| `_bmad-output/branding/visual-identity-guide.md` | Full brand specification | Canonical visual identity |
| `frontend/vite.config.ts` | Add `@brand` alias | Lines 8-12: `resolve.alias` |
| `frontend/package.json` | Add @fontsource deps | No @fontsource packages yet |
| `frontend/src/index.css` | Frontend entry CSS | Line 1: Google Fonts import; Lines 4-12: `@theme`; Lines 14-23: `:root` |
| `frontend/src/lib/utils.ts` | Existing lib dir | Dir ready for `brand-tokens.ts` |
| `frontend/src/components/simulation/chart-theme.ts` | Hardcoded chart hex values | Lines 47, 53, 59: `#e2e8f0`, `#64748b` |
| `website/astro.config.mjs` | Add `@brand` alias (Vite) | Lines 5-7: vite config (no resolve yet) |
| `website/package.json` | Font deps to swap | Lines 19-20: playfair + source-sans-3 |
| `website/src/styles/global.css` | Website entry CSS | Lines 1-3: font imports; Lines 5-38: `@theme` |
| `website/src/components/*.astro` | All 12 components | ~85 color/font references total |
| `_bmad/_config/agents/cis-presentation-master.customize.yaml` | Agent config | Currently blank template (42 lines) |
| `_bmad-output/planning-artifacts/ux-design-specification.md` | Duplicate visual specs | Lines 430-616: Color, Typography, Direction |
| `docs/ux-design-specification.md` | Identical copy | Same as planning artifacts version |

### Technical Decisions

1. **Same palette, different lead color per surface:** Website leads with emerald (brand mark color) for CTAs and accents. App continues leading with blue (interactivity/focus). Both draw from the same Tailwind slate + brand palette.

2. **Same font family, different expression:** Both surfaces use Inter + IBM Plex Mono. Website uses Inter at larger sizes and heavier weights (600–700) for marketing impact — **cap at 700, never 800/900** (Inter gets chunky). App uses Inter at standard UI weights (400-600) for data density.

3. **Font loading: standardize on @fontsource:** Both projects switch to `@fontsource-variable/inter` and `@fontsource-variable/ibm-plex-mono` for consistency, performance (self-hosted, no external CDN), and offline support.

4. **Website keeps warm background:** The off-white paper background (`#faf8f5`) is retained as a website-specific surface color — it adds marketing warmth without conflicting with the brand palette. Defined in website's `global.css`, not in shared theme.

5. **Website keeps dark hero sections:** Dark surfaces (`#0f172a`) with mesh gradients are retained — they work well for marketing. Accent colors within them change from amber to emerald/blue. **Use emerald-400 (`#34D399`) for CTAs on dark backgrounds** — brighter and more energetic than emerald-500 on dark. Mesh gradient needs visual testing: emerald + slate-blue blend, ensure it doesn't feel cold.

6. **Shared theme stays lean:** Only brand-universal tokens (semantic colors, chart palette, font families) live in `theme.css`. Surface-specific styling (website paper background, button animations, hero gradients) stays in each project's own CSS.

7. **Vite alias for import paths:** Both projects add a `@brand` alias pointing to `_bmad-output/branding/` in their Vite config. Imports become `@import "@brand/theme.css"` instead of fragile relative paths. One line per project.

8. **@theme ordering rule:** The shared theme provides `--font-sans` and `--font-mono`. Local `@theme` blocks in each project must NOT redeclare these — only add surface-specific tokens. Tailwind v4 processes `@theme` blocks in import order; last declaration wins.

9. **TypeScript brand tokens:** Create `frontend/src/lib/brand-tokens.ts` exporting hex constants that match theme.css. `chart-theme.ts` and any future TS consumers import from there instead of hardcoding hex values. No runtime CSS lookups — just a single-source TS file.

## Implementation Plan

### Tasks

> Tasks are ordered by dependency: infrastructure first, then frontend, then website, then docs/config, then verification.

#### Task 1: Add Vite aliases and verify shared theme

**File:** `frontend/vite.config.ts`

Add alias so `@brand` resolves to `_bmad-output/branding/`:
```ts
resolve: {
  alias: {
    '@brand': path.resolve(__dirname, '../_bmad-output/branding'),
  }
}
```

**File:** `website/astro.config.mjs`

Add alias in the Vite config section:
```js
vite: {
  resolve: {
    alias: {
      '@brand': new URL('./_bmad-output/branding', import.meta.url).pathname,
    }
  }
}
```
Note: Astro's project root may require `../_bmad-output/branding` depending on config — verify the path resolves correctly.

**File:** `_bmad-output/branding/theme.css`

No changes needed — already declares `--font-sans` and `--font-mono` correctly.

#### Task 2: Wire theme into frontend app

**File:** `frontend/src/index.css`

1. Replace Google Fonts `@import url(...)` with `@fontsource-variable` imports:
   ```css
   @import "@fontsource-variable/inter";
   @import "@fontsource-variable/ibm-plex-mono" layer(base);
   ```
2. Add `@import "@brand/theme.css";` after font imports, before `@import "tailwindcss"`
3. Remove the duplicate `@theme { ... }` block (semantic colors now come from theme.css)
4. Remove the duplicate `:root { --chart-* }` block (chart tokens now come from theme.css)
5. Keep the `body`, `html`, `#root`, and `.data-mono` rules (app-specific)

**File:** `frontend/package.json`

Add dependencies:

```
@fontsource-variable/inter
@fontsource-variable/ibm-plex-mono
```

Remove: nothing (Google Fonts import is just a CSS line, no package)

#### Task 3: Create brand-tokens.ts and fix frontend hardcoded hex values

**New file:** `frontend/src/lib/brand-tokens.ts`

Create a TypeScript file exporting hex constants that mirror theme.css:

```ts
/** Brand tokens — must match _bmad-output/branding/theme.css */
export const brand = {
  slate200: '#e2e8f0',
  slate400: '#94a3b8',
  slate500: '#64748b',
  blue500: '#3b82f6',
  violet500: '#8b5cf6',
  emerald500: '#10b981',
  amber500: '#f59e0b',
  red500: '#ef4444',
} as const;
```

**File:** `frontend/src/components/simulation/chart-theme.ts`

Replace hardcoded hex values with imports from `brand-tokens.ts`:
- `#e2e8f0` → `brand.slate200` (grid stroke)
- `#64748b` → `brand.slate500` (axis tick)

Grep for any other hardcoded hex values in `frontend/src/` that match brand palette colors and update them to import from `brand-tokens.ts`.

#### Task 4: Swap website fonts

**File:** `website/package.json`

Remove:
```
@fontsource-variable/playfair-display
@fontsource-variable/source-sans-3
```

Add:
```
@fontsource-variable/inter
@fontsource-variable/ibm-plex-mono
```

**File:** `website/src/styles/global.css`

1. Replace font imports:
   ```css
   @import "@fontsource-variable/inter";
   @import "@fontsource-variable/ibm-plex-mono";
   ```
2. Add `@import "@brand/theme.css";` after font imports, before `@import "tailwindcss"`
3. Replace `@theme` block: remove all custom ink/paper/amber/teal tokens. Do NOT redeclare `--font-sans` or `--font-mono` (shared theme owns those). Add website-specific tokens only:

   ```css
   @theme {
     /* Website-specific surfaces (marketing warmth) */
     --color-paper: #faf8f5;
     --color-paper-warm: #f5f0ea;

     /* Website accent: emerald leads for brand continuity */
     --color-cta: var(--color-emerald-500);
     --color-cta-hover: var(--color-emerald-400);
     --color-cta-glow: rgba(16, 185, 129, 0.3);
     --color-cta-dark: var(--color-emerald-400); /* brighter on dark bg */
     --color-secondary-accent: var(--color-blue-500);
   }
   ```

4. Update `body` rule: `font-family: var(--font-sans)` (from shared theme)
5. Update heading rule: `font-family: var(--font-sans)` with `font-weight: 700` (bold Inter for marketing headings — **never 800/900**, Inter gets chunky)
6. Update `.btn-primary`: background from `var(--color-amber)` to `var(--color-cta)`. On dark sections (`.mesh-gradient .btn-primary`), use `var(--color-cta-dark)` for extra brightness
7. Update `.btn-primary:hover`: shadow color from amber rgba to emerald rgba
8. Update `.mesh-gradient`: replace amber/teal radial gradients with emerald/blue-slate. **Visually test** — pure emerald+blue can feel cold; consider adding a subtle warm tone to the gradient mix
9. Update `::selection`: from amber-soft to emerald-soft
10. **Pre-flight check:** Grep all website components for inline `font-family: "Playfair Display"` or `font-family: "Source Sans"` — any inline style referencing removed fonts will silently fail to render

#### Task 5: Update all 12 website Astro components

For each component, perform these color substitutions:

| Old Token (Tailwind class) | New Token (Tailwind class) | Rationale |
| --- | --- | --- |
| `bg-amber` | `bg-cta` | Primary CTA / accent |
| `text-amber` | `text-cta` | Primary accent text |
| `text-amber-glow` | `text-emerald-400` | Bright accent (hover/glow) |
| `bg-amber-soft` | `bg-emerald-500/12` | Soft accent background |
| `border-amber` / `border-amber/20` | `border-cta` / `border-emerald-500/20` | Accent borders |
| `ring-amber` | `ring-emerald-500` | Focus rings |
| `bg-teal` | `bg-secondary-accent` | Secondary accent |
| `text-teal` | `text-secondary-accent` | Secondary accent text |
| `bg-teal-soft` | `bg-blue-500/10` | Soft secondary background |
| `border-teal` | `border-blue-500` | Secondary borders |
| `font-[family-name:var(--font-display)]` | `font-sans font-bold` | Headings: bold Inter (700) |
| `font-[family-name:var(--font-body)]` | `font-sans` | Body: regular Inter |

Components to update (all in `website/src/components/`):
1. Nav.astro
2. Hero.astro
3. Problem.astro
4. HowItWorks.astro
5. Features.astro
6. BeforeAfter.astro
7. UseCases.astro
8. Comparison.astro
9. WhyNow.astro
10. FAQ.astro
11. Closing.astro
12. Footer.astro

#### Task 6: Configure BMAD presentation agent

**File:** `_bmad/_config/agents/cis-presentation-master.customize.yaml`

Add configuration to always load the visual identity guide:
```yaml
context_files:
  - _bmad-output/branding/visual-identity-guide.md
instructions: |
  Always apply the ReformLab visual identity guide when creating
  presentations. Use the presentation chart color order (emerald leads).
  Fonts: Inter (headings/body) + IBM Plex Mono (data/code).
  No serif fonts. No gradients. No photography.
```

#### Task 7: Remove duplicate visual specs from other documents

The visual identity guide at `_bmad-output/branding/visual-identity-guide.md` is the single source of truth. Other documents contain outdated duplicate styling sections that must be replaced with pointers.

**File:** `_bmad-output/planning-artifacts/ux-design-specification.md`

Replace the "Color System", "Typography System", and "Design Direction Decision" sections (approx. lines 430–615) with a reference block:

```markdown
### Visual Identity

> For the complete color system, typography, chart palette, and visual style rules,
> see the canonical source: `_bmad-output/branding/visual-identity-guide.md`
>
> This UX spec covers component behavior and interaction patterns only.
> All visual styling decisions are maintained in the visual identity guide.
```

**File:** `docs/ux-design-specification.md`

Same change — this is an identical copy of the planning artifacts version.

**Note:** Story files (e.g. `18-8-chart-polish-and-color-palette-refinement.md`) contain implementation-specific color references that are acceptable — they're scoped to a task, not a competing source of truth.

#### Task 8: Verify builds and visual check

1. `cd frontend && npm install && npm run build` — must succeed
2. `cd website && npm install && npm run build` — must succeed
3. Visual spot-check both dev servers:
   - Fonts: Inter everywhere, no serif remnants
   - Colors: emerald CTAs on website, blue CTAs in app, no amber/teal
   - Dark sections: emerald-400 CTAs readable and energetic on dark backgrounds
   - Nav scroll transitions: verify nav background change feels coherent with new palette
   - Charts: colors match theme tokens

### Acceptance Criteria

**AC1: Shared theme is consumed by both projects**
- Given the frontend app is built
- When I inspect the CSS output
- Then semantic tokens (--color-validated, --chart-reform-a, etc.) resolve to the values defined in theme.css

**AC2: Frontend uses @fontsource instead of Google Fonts CDN**
- Given the frontend app loads
- When I inspect network requests
- Then no requests are made to fonts.googleapis.com
- And Inter and IBM Plex Mono render correctly

**AC3: Website uses Inter + IBM Plex Mono**
- Given the website is built
- When I view any page
- Then all headings use Inter (bold/semibold)
- And body text uses Inter (regular)
- And no serif fonts appear anywhere

**AC4: Website accent colors use brand palette**
- Given the website is rendered
- When I inspect CTAs and accent elements
- Then primary accent is emerald-500 (#10B981)
- And secondary accent is blue-500 (#3B82F6)
- And no amber (#d97706) or teal (#0d9488) colors remain

**AC5: Frontend tokens are not duplicated**
- Given frontend/src/index.css
- When I read the file
- Then there is no `@theme` block (tokens come from imported theme.css)
- And there is no `:root { --chart-* }` block (chart tokens come from theme.css)

**AC6: Both projects build without errors**
- Given all changes are applied
- When `npm run build` is run in frontend/ and website/
- Then both succeed with exit code 0

**AC7: BMAD presentation agent has brand context**
- Given cis-presentation-master.customize.yaml is configured
- When the presentation-master agent is invoked
- Then the visual identity guide is loaded as context

**AC8: No duplicate visual specs remain in other documents**
- Given the UX design specs in `_bmad-output/planning-artifacts/` and `docs/`
- When I read the "Color System", "Typography System", and "Design Direction" sections
- Then they contain only a reference pointer to `_bmad-output/branding/visual-identity-guide.md`
- And no inline hex values, font names, or palette definitions remain in those sections

**AC9: No removed font references remain in website**
- Given the website is built
- When I grep all `website/src/` files for "Playfair", "Source Sans", "font-display", "font-body"
- Then zero matches are found

## Additional Context

### Dependencies

- `@fontsource-variable/inter` — add to both frontend/ and website/
- `@fontsource-variable/ibm-plex-mono` — add to both frontend/ and website/
- `@fontsource-variable/playfair-display` — remove from website/
- `@fontsource-variable/source-sans-3` — remove from website/

### Testing Strategy

- **Build verification:** Both `npm run build` must pass
- **Lint:** `npm run lint` in frontend/ must pass (no new warnings)
- **Type check:** `npm run typecheck` in frontend/ must pass
- **Visual:** Manual spot-check of both dev servers — fonts, colors, buttons, charts, dark sections

### Notes

- The website's warm paper background (#faf8f5) is intentionally kept as a website-specific surface — it doesn't conflict with the brand palette and adds marketing warmth.
- `brand-tokens.ts` is a static mirror of theme.css for TypeScript consumption — no runtime CSS lookups. If theme.css changes, brand-tokens.ts must be updated manually. Keep the `/** must match theme.css */` comment as a reminder.
- The presentation chart order (emerald leads) differs from the app chart order (blue leads) — this is by design per the visual identity guide.
- **High-risk item:** The mesh gradient color swap (amber/teal → emerald/blue) may feel visually cold. Visual testing is required — may need a warm tone added to the gradient mix.
- **High-risk item:** Website visual regression across 12 components — do a full scroll-through after Task 5 before proceeding to Task 6.
