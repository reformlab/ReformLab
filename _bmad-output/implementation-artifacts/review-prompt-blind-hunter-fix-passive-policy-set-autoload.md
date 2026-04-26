# Blind Hunter Review Prompt

Use the `bmad-review-adversarial-general` skill.

You receive only a diff. Do not assume broader project context. Do not inspect the repo. Review the diff adversarially for bugs, regressions, broken assumptions, missing guards, and incorrect behavior changes. Prioritize concrete findings with severity, rationale, and the exact changed file/area implicated by the diff.

Diff input:
- Open `_bmad-output/implementation-artifacts/review-diff-fix-passive-policy-set-autoload-for-non-portfolio-references.patch`
- Review only that patch content.

Output format:
1. Findings first, ordered by severity.
2. For each finding: title, severity, file/path, why it is a problem, and the smallest corrective action.
3. If no findings, say `No findings` and list residual review risks briefly.
