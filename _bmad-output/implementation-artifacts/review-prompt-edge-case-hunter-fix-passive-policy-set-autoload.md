# Edge Case Hunter Review Prompt

Use the `bmad-review-edge-case-hunter` skill.

You receive a diff and read-only project access. Review for missed boundary conditions, stale-state bugs, loading races, repeated-effect behavior, and hidden workflow regressions.

Inputs:
- Diff file: `_bmad-output/implementation-artifacts/review-diff-fix-passive-policy-set-autoload-for-non-portfolio-references.patch`
- Project root: current repository

Focus areas:
- Passive policy-set autoload behavior when portfolio lists are empty, loading, stale, or updated after mount
- Interaction between `activeScenario.portfolioName`, `loadedPortfolioRef`, and explicit load-dialog flows
- Test coverage gaps relative to the changed behavior
- Compatibility with the existing uncommitted `AppContext` integration work

Output format:
1. Findings first, ordered by severity.
2. For each finding: title, severity, file/path, scenario that triggers it, and smallest corrective action.
3. If no findings, say `No findings` and list residual edge-case risks briefly.
