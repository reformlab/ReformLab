# Epic 11 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 11-3 (2026-03-03)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `gzip.BadGzipFile` inherits from `OSError` — triggers wrong stale-cache fallback | Added explicit try/except around `gzip.decompress()` in Eurostat parsing strategy code, re-raising as `DataSourceValidationError`. Added `TestEurostatLoaderFetchBadGzip` test case to Task 6.1. Verified via `python3 -c "import gzip; print(gzip.BadGzipFile.__mro__)"` — confirms `BadGzipFile` → `OSError` → `Exception`. |
| high | `EurostatDataset` missing `encoding`/`separator`/`null_markers` fields | Added `encoding: str = "utf-8"`, `separator: str = ","`, `null_markers: tuple[str, ...] = ("", ":")` to Task 1.2. Updated Eurostat parsing strategy to read from `self._dataset` instead of hardcoding. Consistent with `INSEEDataset`/`ADEMEDataset`/`SDESDataset` pattern. |
| high | Windows-1252 fixture creation ambiguity | Replaced vague fixture creation guidance with explicit `conftest.py` fixture helper using `content.encode("windows-1252")`. Clarified that the `Write` tool cannot create Windows-1252 files and the on-disk fixture must be generated programmatically. |
| high | `AVAILABLE_DATASETS` naming asymmetry in `__init__.py` | Added Task 4.1 specifying rename of `AVAILABLE_DATASETS` → `INSEE_AVAILABLE_DATASETS` with backward-compatible alias. All new providers use prefixed names consistently. |
| medium | Gzip test helper `_make_gzip()` not defined | Added inline code example in Test Pattern section. |
| medium | `SDESDataset.skip_rows` not tested | Added `TestSDESLoaderFetchSkipRows` to Task 6.3 and wiring reminder to Task 3.6. |
| medium | AC#3 "age distribution" ambiguity | Reworded to "vehicle fleet composition data (including vehicle age classification)" — clarifies that age is a field within `vehicle_fleet`, not a separate dataset. |
| medium | SDES URL ambiguity | Changed "Recommendation" to "Decision" and explicitly stated the DiDo URL is "informational only — do not use it in the catalog." |
| medium | Column name verification caveat repeated 3 times | Consolidated ADEME and SDES per-section caveats into one-line references to the "Column Name Verification Strategy" section. |

## Story 11-4 (2026-03-03)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `capture_assumptions()` API mismatch in Downstream Dependencies | Rewrote Story 11.6 description to correctly state that `to_governance_entry()` dicts are appended directly to `RunManifest.assumptions`, NOT passed to `capture_assumptions()`. Verified against `governance/capture.py:19-24` — function takes flat `dict[str, Any]` key-value pairs, incompatible with structured merge assumptions. |
| high | `bool` not rejected in `MergeConfig.seed` validation | Added `isinstance(self.seed, bool)` check to `__post_init__` spec, matching `manifest.py:219` pattern. Updated Task 2.2 description and test spec. |
| high | `**self.details` key collision in `to_governance_entry()` | Reversed dict merge order so `**self.details` unpacks first, then `method`/`statement` override. Updated Task 2.3 to document constraint. |
| high | File count mismatch | Corrected "New files (6)" to "New files (9)" and "Modified files (2)" to "Modified files (1)". |
| high | `from copy import deepcopy` local import | Removed local import from `__post_init__` spec; added import notes section clarifying `deepcopy` must be at module level (following `manifest.py:22`). |
| high | `methods/__init__.py` missing `__all__` | Updated Task 4.1 to require explicit `__all__` definition following `population/loaders/__init__.py` pattern. |
| medium | AC#2 lacks determinism and replacement wording | Amended AC#2 to specify "with replacement, using the provided `MergeConfig.seed` to guarantee reproducibility." |
| medium | Column ordering not documented as contract | Added ordering statement to Algorithm Detail step 3. |
| medium | Import notes for pyarrow runtime vs TYPE_CHECKING | Added import notes section under No New Dependencies. |
