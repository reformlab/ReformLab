# Acceptance Auditor Review Prompt

Review the implementation against the approved spec and context documents. You have read-only project access.

Inputs:
- Diff file: `_bmad-output/implementation-artifacts/review-diff-fix-passive-policy-set-autoload-for-non-portfolio-references.patch`
- Spec file: `_bmad-output/implementation-artifacts/spec-fix-passive-policy-set-autoload-for-non-portfolio-references.md`
- Context files:
  - `_bmad-output/project-context.md`
  - `_bmad-output/implementation-artifacts/24-1-publish-canonical-catalog-and-api-exposure-for-already-modeled-hidden-policy-packs.md`
  - `_bmad-output/implementation-artifacts/spec-establish-appcontext-integration-testing.md`

Audit goals:
- Check that the implementation satisfies the acceptance criteria in the spec.
- Check that passive autoload now ignores non-portfolio references without suppressing explicit user-facing load failures.
- Check that the implementation does not violate the AppContext compatibility constraint.
- Check whether the verification evidence is sufficient, noting that local Vitest execution is blocked by the current Node runtime.

Output format:
1. Findings first, ordered by severity.
2. For each finding: title, severity, violated acceptance criterion or rule, file/path, and smallest corrective action.
3. If no findings, say `No findings` and list any residual validation gaps briefly.
