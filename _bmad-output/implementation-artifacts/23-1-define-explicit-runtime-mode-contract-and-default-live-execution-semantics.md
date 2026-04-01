# Story 23.1: Define explicit runtime-mode contract and default-live execution semantics

Status: ready-for-dev

## Story

As a platform developer,
I want an explicit runtime-mode contract that makes live OpenFisca execution the default for web runs while keeping replay as an explicit non-default path,
so that Scenario, run requests, run metadata, and manifests can unambiguously distinguish live runs from replay runs without introducing a frontend runtime selector.

**Epic:** Epic 23 — Live OpenFisca Runtime and Executable Population Alignment
**Priority:** P0
**Estimate:** 5 SP
**Dependencies:** None

## Acceptance Criteria

1. Given a standard web run request, when no special replay path is invoked, then the runtime contract resolves to live OpenFisca execution by default.
2. Given an explicit replay or demo path, when invoked, then the runtime contract records replay mode rather than inheriting the live default implicitly.
3. Given a scenario configured for `annual` or `horizon_step` simulation, when runtime mode is serialized, then the simulation-mode value remains unchanged and separately addressable from runtime mode.
4. Given run metadata or manifests, when inspected, then runtime mode is visible and unambiguous.
5. Given the Scenario-stage UX, when reviewed for this story, then no new frontend runtime selector is introduced.

## Tasks / Subtasks

- [ ] **Backend: Add runtime-mode type and default contract** (AC: 1, 2, 3)
  - [ ] Create `RuntimeMode` literal type in `src/reformlab/computation/types.py` (`"live"` | `"replay"`)
  - [ ] Add `runtime_mode: RuntimeMode` field to `RunRequest` in `src/reformlab/server/models.py` with default `"live"`
  - [ ] Add `runtime_mode: RuntimeMode` field to `RunResponse` in `src/reformlab/server/models.py`
  - [ ] Add `runtime_mode: RuntimeMode` field to `RunConfig` in `src/reformlab/interfaces/api.py` (NOT ScenarioConfig — architecture §5.9 assigns runtime_mode to Run, not Scenario)
  - [ ] Document that `runtime_mode` is separate from `simulation_mode` (which is `annual` or `horizon_step`)

- [ ] **Backend: Record runtime mode in RunManifest** (AC: 4)
  - [ ] Add `runtime_mode: RuntimeMode` field to `RunManifest` dataclass in `src/reformlab/governance/manifest.py`
  - [ ] Add `runtime_mode` to `REQUIRED_JSON_FIELDS` or `OPTIONAL_JSON_FIELDS` as appropriate
  - [ ] Update `to_json()` and `from_json()` methods to handle `runtime_mode` serialization
  - [ ] Update manifest fixtures in `tests/governance/conftest.py` to include `runtime_mode="live"`

- [ ] **Backend: Propagate runtime mode through execution flow** (AC: 1, 2, 4)
  - [ ] Update `run_scenario()` in `src/reformlab/interfaces/api.py` to accept `runtime_mode` from `RunConfig`
  - [ ] Pass `runtime_mode` through to manifest generation in `src/reformlab/interfaces/api.py`
  - [ ] Update `POST /api/runs` route in `src/reformlab/server/routes/runs.py` to handle `runtime_mode` from request body
  - [ ] Update `ResultMetadata` in `src/reformlab/server/result_store.py` to include `runtime_mode` field
  - [ ] Update `ResultDetailResponse` in `src/reformlab/server/models.py` to include `runtime_mode` field

- [ ] **Frontend: Add runtime-mode type to API contracts** (AC: 3, 4, 5)
  - [ ] Add `runtime_mode?: "live" | "replay"` to `RunRequest` interface in `frontend/src/api/types.ts` (optional — omit to let backend default apply)
  - [ ] Add `runtime_mode: "live" | "replay"` to `RunResponse` interface in `frontend/src/api/types.ts`
  - [ ] Add `runtime_mode: "live" | "replay"` to `ResultDetailResponse` interface in `frontend/src/api/types.ts`
  - [ ] Ensure frontend does NOT send `runtime_mode` for standard run requests (rely on backend default; no UI selector)

- [ ] **Tests: Contract serialization tests** (AC: 3, 4)
  - [ ] Add `test_runtime_mode_serialization()` in `tests/server/test_api.py` for request/response round-trip
  - [ ] Add `test_manifest_runtime_mode_field()` in `tests/governance/test_manifest.py`
  - [ ] Add `test_manifest_from_json_with_runtime_mode()` in `tests/governance/test_manifest.py`
  - [ ] Add `test_runtime_mode_default_is_live()` in `tests/server/test_api.py`

- [ ] **Tests: Migration compatibility tests** (AC: 3)
  - [ ] Add `test_legacy_request_without_runtime_mode_defaults_to_live()` in `tests/server/test_api.py`
  - [ ] Add `test_legacy_manifest_deserialization_without_runtime_mode()` in `tests/governance/test_manifest.py`
  - [ ] Add `test_manifest_from_json_with_invalid_runtime_mode_raises()` in `tests/governance/test_manifest.py`
  - [ ] Add `test_result_metadata_without_runtime_mode_fallback()` in `tests/server/test_api.py`
  - [ ] Add `test_legacy_load_then_save_preserves_runtime_mode()` in `tests/server/test_result_store.py`

## Dev Notes

### Architecture Patterns

**Runtime Mode vs Simulation Mode (Critical Distinction)**

From `_bmad-output/planning-artifacts/architecture.md` (Section 5.9 - Server):

> **Mode ownership is explicit:** `Scenario` owns `simulation_mode` (`annual` or `horizon_step`) plus horizon settings and inherited population references. `Run` and its manifest own `runtime_mode` (`live` or explicit `replay`). These fields are intentionally separate: simulation behavior is not the same thing as live-vs-replay execution path.

**Key Design Decisions:**
- `runtime_mode` is an execution path concern (live vs replay), NOT a simulation behavior concern
- `simulation_mode` (annual/horizon_step) remains owned by Scenario and is orthogonal to runtime
- The web default is `live` with no user-facing selector in this story
- Replay remains available only via explicit demo/manual paths
- Frontend should NOT add a runtime selector in this story (AC-5)

### Non-Goals (Out of Scope)

This story defines the contract only. The following are explicitly out of scope:

- **Replay invocation mechanism:** How replay paths are triggered (endpoint, flag, UI action) is deferred to Story 23.4
- **Live execution engine:** Actually executing against live OpenFisca is Stories 23.2–23.3
- **Orchestrator behavior changes:** The orchestrator remains runtime-agnostic; branching on `runtime_mode` happens at the server/interfaces layer
- **Frontend UI changes:** No new components, screens, or selectors

### Source Tree Components

**Backend files to modify:**

| File Path | Purpose | Key Changes |
|-----------|---------|-------------|
| `src/reformlab/computation/types.py` | Add `RuntimeMode` literal type | `RuntimeMode = Literal["live", "replay"]` |
| `src/reformlab/server/models.py` | Pydantic request/response models | Add `runtime_mode` field to `RunRequest`, `RunResponse`, `ResultDetailResponse` |
| `src/reformlab/governance/manifest.py` | Immutable run manifest | Add `runtime_mode` field; update `to_json()` / `from_json()` |
| `src/reformlab/interfaces/api.py` | Python API config types | Add `runtime_mode` to `RunConfig` only (NOT ScenarioConfig); propagate to manifest |
| `src/reformlab/server/routes/runs.py` | Execution route handler | Read `runtime_mode` from request; pass through to `run_scenario()` |
| `src/reformlab/server/result_store.py` | Result metadata persistence | Add `runtime_mode` to `ResultMetadata` dataclass |

**Frontend files to modify:**

| File Path | Purpose | Key Changes |
|-----------|---------|-------------|
| `frontend/src/api/types.ts` | TypeScript API contracts | Add `runtime_mode: "live" \| "replay"` to `RunRequest`, `RunResponse`, `ResultDetailResponse` |

**Test files to modify:**

| File Path | Purpose |
|-----------|---------|
| `tests/governance/test_manifest.py` | Add runtime mode serialization tests |
| `tests/governance/conftest.py` | Update manifest fixtures to include `runtime_mode="live"` |
| `tests/server/test_api.py` | Add request/response contract tests, migration tests |
| `tests/server/conftest.py` | Add runtime mode fixtures for testing |

### Implementation Notes

**1. RuntimeMode Type Definition**

```python
# src/reformlab/computation/types.py

from __future__ import annotations
from typing import Literal

RuntimeMode = Literal["live", "replay"]
```

**2. RunRequest with Default Live**

```python
# src/reformlab/server/models.py

class RunRequest(BaseModel):
    template_name: str | None = None
    policy: dict[str, Any] = {}
    start_year: int = 2025
    end_year: int = 2030
    population_id: str | None = None
    seed: int | None = None
    baseline_id: str | None = None
    portfolio_name: str | None = None
    policy_type: str | None = None
    exogenous_series: list[str] | None = None
    # Story 23.1 / AC-1, AC-2: Runtime mode with live default
    runtime_mode: Literal["live", "replay"] = "live"
```

**3. RunManifest Extension**

```python
# src/reformlab/governance/manifest.py

@dataclass(frozen=True)
class RunManifest:
    # ... existing fields ...
    # Story 23.1 / AC-4: Runtime mode (live or explicit replay)
    runtime_mode: str = "live"  # "live" | "replay"
    integrity_hash: str = ""
```

**4. Manifest Serialization**

Add `runtime_mode` to `REQUIRED_JSON_FIELDS` (or `OPTIONAL_JSON_FIELDS` with a default if migration compatibility is needed). Update `to_json()` and `from_json()` to handle the field.

**5. Migration Compatibility**

For backwards compatibility with existing manifests and requests:

- `RunRequest.runtime_mode` defaults to `"live"` when not provided
- Add `runtime_mode` to `OPTIONAL_JSON_FIELDS` in `manifest.py` (not `REQUIRED_JSON_FIELDS`) so legacy manifests without this field load without error
- `RunManifest.from_json()` should handle missing `runtime_mode` gracefully using `data.get("runtime_mode", "live")`, defaulting to `"live"`
- Update `_dict_to_metadata()` in `result_store.py` to extract `runtime_mode` with a `"live"` fallback: `data.get("runtime_mode", "live")`
- Update `_make_minimal_manifest()` in `result_store.py` to include `runtime_mode="live"`
- `from_json()` MUST validate `runtime_mode` values if present: invalid values (not "live" or "replay") raise `ManifestValidationError`
- Add tests for legacy deserialization paths

**6. No Frontend Runtime Selector (AC-5)**

The frontend should:
- Default to `"live"` for all new run requests
- NOT add any UI selector or toggle in this story
- Preserve the default user journey unchanged
- Only expose runtime selection when explicit replay/demo paths are added in later stories (23.4)

### Testing Standards

**Follow existing patterns from `tests/governance/test_manifest.py`:**

```python
class TestRuntimeModeContract:
    """Story 23.1 / AC-1, AC-2: Runtime mode contract and defaults."""

    def test_live_is_default_runtime_mode(self) -> None:
        """RunRequest defaults to live when runtime_mode not specified."""
        request = RunRequest(template_name="carbon_tax")
        assert request.runtime_mode == "live"

    def test_explicit_replay_mode_accepted(self) -> None:
        """RunRequest accepts explicit replay mode."""
        request = RunRequest(
            template_name="carbon_tax",
            runtime_mode="replay"
        )
        assert request.runtime_mode == "replay"

    def test_runtime_mode_invalid_value_raises(self) -> None:
        """Invalid runtime_mode value raises validation error."""
        with pytest.raises(ValidationError):
            RunRequest(
                template_name="carbon_tax",
                runtime_mode="invalid"
            )
```

**Follow existing patterns from `tests/server/test_api.py`:**

```python
class TestRuntimeModeApiContract:
    """Story 23.1 / AC-3, AC-4: API contract serialization."""

    def test_run_request_runtime_mode_serialization(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """RunRequest runtime_mode field serializes correctly."""
        response = client.post(
            "/api/runs",
            headers=auth_headers,
            json={
                "template_name": "carbon_tax",
                "policy": {"rate_schedule": {"2025": 50.0}},
                "start_year": 2025,
                "end_year": 2030,
                "runtime_mode": "live"
            }
        )
        # ... assert response includes runtime_mode
```

**Migration Compatibility Tests:**

```python
class TestRuntimeModeMigrationCompatibility:
    """Story 23.1 / AC-3: Backward compatibility with legacy data."""

    def test_manifest_from_json_without_runtime_mode_defaults_to_live(self) -> None:
        """Legacy manifest JSON without runtime_mode deserializes with live default."""
        legacy_json = '''
        {
            "manifest_id": "legacy-001",
            "created_at": "2026-03-01T00:00:00Z",
            "engine_version": "0.1.0",
            "openfisca_version": "40.0.0",
            "adapter_version": "1.0.0",
            "scenario_version": "v1.0",
            "integrity_hash": ""
        }
        '''
        manifest = RunManifest.from_json(legacy_json)
        assert manifest.runtime_mode == "live"
```

### Project Structure Notes

**Follow established code patterns:**

- **Literal types:** Use `Literal["value1", "value2"]` for closed enums (e.g., `RuntimeMode`)
- **Type imports:** Import `RuntimeMode` from `reformlab.computation.types` in other modules
- **Frozen dataclasses:** `RunManifest` is frozen; use `dataclasses.replace()` when creating modified copies
- **Protocol compliance:** The `ComputationAdapter` protocol remains unchanged; runtime is an orchestration concern, not an adapter concern
- **Error responses:** Use the `{"what": "...", "why": "...", "fix": "..."}` pattern for validation errors

**No changes to:**

- `src/reformlab/computation/adapter.py` — runtime mode is not an adapter concern
- `src/reformlab/orchestrator/` — orchestrator remains runtime-agnostic in this story
- Frontend screens — no UI changes in this story (AC-5)

### References

- **Epic 23 stories:** `_bmad-output/planning-artifacts/epics.md` (Stories 23.1–23.6)
- **Architecture Section 5.9:** Server mode ownership distinction
  - `_bmad-output/planning-artifacts/architecture.md` lines 472-474
- **PRD FR-RUNTIME-1:** Web runs use live OpenFisca as default execution path
- **PRD FR-RUNTIME-4:** Precomputed mode remains available only for explicit demo or manual replay flows
- **PRD FR-RUNTIME-5:** Live runs return stable app-facing result schema
- **Sprint Change Proposal:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-01.md`
- **Project Context:** `_bmad-output/project-context.md` — Critical rules for frozen dataclasses, literal types, and testing

## Dev Agent Record

### Agent Model Used

glm-4.7 (Claude Opus 4.6 equivalent)

### Debug Log References

None created during story generation.

### Completion Notes List

- Story analysis completed from Epic 23 backlog
- Architecture patterns extracted from planning artifacts and codebase
- Implementation scope defined: add runtime_mode contract across backend and frontend types
- Test patterns identified from existing governance and server test suites
- Ready for dev-story execution with comprehensive context

### File List

*See Source Tree Components table above for primary and test files.*

**Planning artifacts referenced:**

1. `_bmad-output/planning-artifacts/epics.md` — Epic 23 stories
2. `_bmad-output/planning-artifacts/architecture.md` — Section 5.9 (Server mode ownership)
3. `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-01.md` — Sprint context
4. `_bmad-output/project-context.md` — Project rules and patterns
