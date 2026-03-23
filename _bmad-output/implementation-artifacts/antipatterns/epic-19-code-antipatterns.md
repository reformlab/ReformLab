# Epic 19 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 19-2 (2026-03-23)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `actions/checkout@v6` does not exist (latest is v4); CI fails on every trigger | Changed to `actions/checkout@v4` |
| high | `mermaid` peer dependency is implicit — not listed in `package.json`, only auto-resolved by npm v7+ | Deferred as action item — requires `npm install` which modifies lockfile |
| medium | Missing `contents: read` permission in CI workflow; when `permissions` is set explicitly, defaults are disabled | Added `contents: read` to permissions block |
| medium | Story marked `Status: done` but two Task 4 subtasks (browser preview, SVG verification) are unchecked | Deferred as action item — requires manual browser verification |
| low | AC 4 "Try the Demo" CTA is inline lowercase text, not a visually distinct button/section | Deferred — acceptable for v1; AC 4 wording says "a 'Try the Demo' call-to-action is present" which is satisfied |
| low | JSX `{/* TODO */}` comments stripped from built HTML, reducing discoverability for future devs | Deferred as low-priority action item |
| dismissed | AC8 placeholder annotation format mismatch (`{/* */}` vs `<!-- -->`) | FALSE POSITIVE: The Dev Agent Record explicitly documents this as a deliberate bug fix: "HTML comments (`<!-- -->`) are not valid inside MDX JSX — replaced with JSX comments (`{/* */}`)". MDX does not support HTML comments inside JSX expressions; using `<!-- -->` would cause a build error. The AC was written before this MDX constraint was discovered. The intent (annotate placeholders) is met. |
| dismissed | All six use-case links are "dead" `#` placeholders — called a "navigation bug" | FALSE POSITIVE: AC 8 explicitly allows `#` placeholders: "a `#` placeholder annotated with `<!-- TODO: link to live demo filter -->`". The Dev Notes table shows all link targets as `/use-cases/#`. This is by design — the app doesn't support deep-linking yet. Not a bug. |
| dismissed | Repeated identical CTA text + identical href creates ambiguous navigation/accessibility | FALSE POSITIVE: Each "Explore this scenario →" link is inside a different Card with a unique title and description. Screen readers will read the card title before the link. This is standard card-grid UX pattern used by Starlight's own documentation. Not an accessibility issue in this context. |
| dismissed | Story File List omits substantial changed files (scope transparency failure) | FALSE POSITIVE: The files Reviewer A claims are missing (`.github/workflows/docs.yml`, BMAD workflow files) are from Story 19.1's commit, not Story 19.2. The git diff shows the full epic-19 branch diff against master, not the story-specific commit. Story 19.2's file list accurately reflects its own changes. |
| dismissed | CI lacks AC-level regression checks (Mermaid render/card-link integrity) | FALSE POSITIVE: The story's Testing Strategy explicitly states "No automated tests for static docs." Adding content-level CI assertions (grep for mermaid blocks, card counts) is over-engineering for a documentation site. The build and typecheck provide sufficient CI coverage. |
| dismissed | Dependency drift risk with `^1.3.1` range for `astro-mermaid` | FALSE POSITIVE: The lockfile pins the exact version. Using `^` ranges is standard npm practice; the lockfile ensures reproducibility. The existing `astro` dependency also uses a pinned version but `@astrojs/starlight` uses `^0.37`. This is consistent with the project's existing dependency strategy. Low risk. |
| dismissed | No `engines` field in `package.json` | FALSE POSITIVE: The `.nvmrc` file already specifies the Node version. Adding an `engines` field is a nice-to-have but not a Story 19.2 requirement and adds no meaningful safety beyond what `.nvmrc` + CI's `node-version-file` already provide. |
