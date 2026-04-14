# Epic 13: Additional Policy Templates + Extensibility

**User outcome:** Analyst can define custom policy templates and use new built-in templates beyond the Phase 1 set, with all templates portfolio-ready.

**Status:** backlog

**Builds on:** EPIC-2 (templates), EPIC-12 (portfolios)

**PRD Refs:** FR46

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-1301 | Story | P0 | 5 | Define custom template authoring API and registration | backlog | FR46 |
| BKL-1302 | Story | P0 | 5 | Implement vehicle malus template (new built-in) | backlog | FR46 |
| BKL-1303 | Story | P0 | 5 | Implement energy poverty aid template (new built-in) | backlog | FR46 |
| BKL-1304 | Story | P0 | 3 | Validate custom templates in portfolios and build notebook demo | backlog | FR46 |

## Epic-Level Acceptance Criteria

- At least 2 new built-in templates are shipped (candidates: vehicle malus, energy poverty aid, building energy performance standards — to be determined during sprint planning).
- Analyst can author a custom template from Python and register it.
- Custom templates participate in portfolios alongside built-in templates.
- Template schema validation accepts custom templates.
- Notebook demo runs end-to-end in CI.

---

## Story 13.1: Define custom template authoring API and registration

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**PRD Refs:** FR46

### Acceptance Criteria

- Given a Python class implementing the template interface (parameters dataclass + apply function), when registered with the template system, then it is available for use in scenarios and portfolios.
- Given a custom template, when validated, then the schema validation accepts it if it conforms to the template protocol.
- Given a custom template with a missing required method, when registered, then a clear error identifies the missing method or signature mismatch.
- Given a registered custom template, when used in a YAML scenario configuration, then it loads and executes like a built-in template.

---

## Story 13.2: Implement vehicle malus template (new built-in)

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 13.1
**PRD Refs:** FR46

### Acceptance Criteria

- Given the vehicle malus template, when applied to a population with vehicle attributes, then a malus (penalty) is computed for high-emission vehicles based on configurable emission thresholds.
- Given the vehicle malus template with year-indexed schedules, when run over 10 years, then malus rates follow the configured yearly schedule.
- Given the vehicle malus template, when composed into a portfolio with a carbon tax and vehicle subsidy, then all three policies apply without conflict.

---

## Story 13.3: Implement energy poverty aid template (new built-in)

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 13.1
**PRD Refs:** FR46

### Acceptance Criteria

- Given the energy poverty aid template, when applied to a population, then households below a configurable income threshold and above a configurable energy expenditure share receive aid.
- Given the template with income-conditioned parameters, when executed, then aid amounts vary by income group and energy burden.
- Given the template, when composed into a portfolio with a carbon tax, then the aid offsets carbon tax burden for eligible households.

---

## Story 13.4: Validate custom templates in portfolios and build notebook demo

**Status:** backlog
**Priority:** P0
**Estimate:** 3

**Dependencies:** Story 13.2, Story 13.3
**PRD Refs:** FR46

### Acceptance Criteria

- Given a custom template authored by an analyst, when added to a portfolio alongside built-in templates, then the portfolio executes correctly with all templates applied.
- Given the notebook demo, when run in CI, then it demonstrates: custom template authoring, registration, portfolio inclusion, execution, and comparison against a portfolio using only built-in templates.
- Given the custom template authoring guide in the notebook, when read by an analyst, then the steps to create and register a new template are clear without consulting external documentation.

## Scope Notes

- **Extensibility is the primary goal** — the template system must be open for analyst-defined policies, not just the shipped templates.
- **New templates should be policy-relevant** to French environmental policy context.

---
