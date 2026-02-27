# Story 4.6: Implement Custom Derived Indicator Formulas

Status: ready-for-dev

## Story

As a **policy analyst or researcher**,
I want **to define custom indicators as derived formulas over run outputs**,
so that **I can compute domain-specific metrics (e.g., carbon intensity ratios, welfare-to-cost ratios, custom thresholds) without modifying the core indicator computation code**.

## Acceptance Criteria

From backlog (BKL-406), aligned with FR23.

Scope note: This story extends the Indicator Engine layer with user-defined derived formulas. Custom indicators operate on existing indicator results (from Stories 4-1 through 4-5) and produce new computed columns/metrics without requiring code changes. This is the final story in Epic 4.

1. **AC-1: Define custom indicator formula schema**
   - Given a formula definition specifying input fields, operation, and output field name
   - When the formula is validated
   - Then the schema accepts valid expressions (arithmetic operations, field references, constants)
   - And rejects invalid formulas with clear error messages identifying the specific issue

2. **AC-2: Apply custom formula to IndicatorResult**
   - Given a valid custom formula and an `IndicatorResult` from any indicator type (distributional, geographic, welfare, fiscal)
   - When `apply_custom_formula()` is invoked
   - Then a new `IndicatorResult` is returned with the derived field added to each indicator row
   - And the original indicator values are preserved unchanged

3. **AC-3: Support arithmetic operations**
   - Given custom formulas using arithmetic operators (+, -, *, /)
   - When applied to indicator results
   - Then the operations are computed correctly using PyArrow compute functions
   - And division by zero produces null values (not errors)

4. **AC-4: Support field references**
   - Given a custom formula referencing existing indicator fields (e.g., `revenue`, `cost`, `mean`, `sum`)
   - When applied to indicator results
   - Then the referenced fields are correctly resolved from the indicator table
   - And missing field references raise a clear `ValueError` listing available fields

5. **AC-5: Support constants**
   - Given a custom formula including numeric constants (e.g., `carbon_tax_rate * 0.85`)
   - When applied to indicator results
   - Then constants are correctly incorporated into the computation
   - And the formula parser handles both integers and floating-point constants

6. **AC-6: Chain multiple custom formulas**
   - Given multiple custom formulas to be applied sequentially
   - When `apply_custom_formulas()` is invoked with a list of formulas
   - Then each formula is applied in order, with later formulas able to reference fields created by earlier formulas
   - And the final result contains all derived fields

7. **AC-7: Custom formula metadata tracking**
   - Given a custom formula applied to an indicator result
   - When the result is inspected
   - Then the formula definition, input fields, and output field name are recorded in `IndicatorResult.metadata`
   - And the metadata supports downstream governance (audit trail of derived calculations)

8. **AC-8: Custom formula in comparison context**
   - Given custom formulas applied to multiple scenario indicator results
   - When `compare_scenarios()` is invoked on the results
   - Then the derived fields are included in the comparison table
   - And delta columns are computed for derived fields just like native fields

9. **AC-9: Validation of formula syntax**
   - Given a formula with invalid syntax (unbalanced parentheses, unknown operators, invalid field names)
   - When the formula is parsed
   - Then a clear `FormulaValidationError` is raised with the specific syntax issue and position
   - And suggested corrections are provided where possible

10. **AC-10: Safe expression evaluation**
    - Given any custom formula input
    - When the formula is evaluated
    - Then no arbitrary code execution is possible (no dynamic evaluation of untrusted strings)
    - And only whitelisted operations and field references are permitted

## Tasks / Subtasks

- [ ] Task 0: Confirm prerequisites and review prior patterns (AC: dependency check)
  - [ ] 0.1 Verify Stories 4-1 through 4-5 are `done` in `sprint-status.yaml`
  - [ ] 0.2 Review `IndicatorResult.to_table()` output schemas from `src/reformlab/indicators/types.py`
  - [ ] 0.3 Review comparison module patterns from `src/reformlab/indicators/comparison.py`
  - [ ] 0.4 Identify available PyArrow compute functions for formula operations

- [ ] Task 1: Design custom formula schema and types (AC: #1, #9)
  - [ ] 1.1 Create `src/reformlab/indicators/custom.py` module
  - [ ] 1.2 Define `CustomFormulaConfig` dataclass with output_field, expression, description
  - [ ] 1.3 Define `FormulaValidationError` exception class with position and suggestion fields
  - [ ] 1.4 Define `CustomIndicatorResult` wrapper or extend `IndicatorResult` for derived fields

- [ ] Task 2: Implement formula parser (AC: #1, #3, #4, #5, #9, #10)
  - [ ] 2.1 Implement `_parse_formula()` to tokenize formula expressions
  - [ ] 2.2 Support operators: +, -, *, /, parentheses
  - [ ] 2.3 Support field references: alphanumeric identifiers (e.g., `revenue`, `cost`, `mean`)
  - [ ] 2.4 Support numeric constants: integers and floats (e.g., `100`, `0.85`, `-1.5`)
  - [ ] 2.5 Implement syntax validation with clear error messages
  - [ ] 2.6 Ensure no arbitrary code execution (whitelist approach)

- [ ] Task 3: Implement formula evaluation engine (AC: #2, #3, #4, #5)
  - [ ] 3.1 Implement `_evaluate_formula()` using PyArrow compute functions
  - [ ] 3.2 Map parsed operations to PyArrow: pc.add, pc.subtract, pc.multiply, pc.divide
  - [ ] 3.3 Handle division by zero: use pc.if_else to produce null instead of error
  - [ ] 3.4 Resolve field references from indicator table columns
  - [ ] 3.5 Handle constants as PyArrow scalars

- [ ] Task 4: Implement single formula application (AC: #2, #7)
  - [ ] 4.1 Implement `apply_custom_formula(result: IndicatorResult, formula: CustomFormulaConfig)` function
  - [ ] 4.2 Convert indicator result to table via `to_table()`
  - [ ] 4.3 Evaluate formula and add derived column to table
  - [ ] 4.4 Create new `IndicatorResult` with extended metadata tracking the formula
  - [ ] 4.5 Preserve all original indicator values

- [ ] Task 5: Implement chained formula application (AC: #6)
  - [ ] 5.1 Implement `apply_custom_formulas(result: IndicatorResult, formulas: list[CustomFormulaConfig])` function
  - [ ] 5.2 Apply formulas in sequence, allowing later formulas to reference earlier derived fields
  - [ ] 5.3 Track all applied formulas in metadata
  - [ ] 5.4 Validate formula order dependencies and provide warnings if out of order

- [ ] Task 6: Integration with comparison module (AC: #8)
  - [ ] 6.1 Verify derived fields flow through `compare_scenarios()` correctly
  - [ ] 6.2 Ensure delta computation works on derived fields
  - [ ] 6.3 Add integration test: custom formula → comparison → delta verification

- [ ] Task 7: Add focused tests and quality gates (AC: all)
  - [ ] 7.1 Create `tests/indicators/test_custom.py`
  - [ ] 7.2 Test formula parsing: valid expressions, invalid syntax, edge cases
  - [ ] 7.3 Test arithmetic operations: +, -, *, /, parentheses precedence
  - [ ] 7.4 Test field reference resolution and error messages for missing fields
  - [ ] 7.5 Test constants: integers, floats, negative values
  - [ ] 7.6 Test division by zero handling (null result)
  - [ ] 7.7 Test chained formula application with dependencies
  - [ ] 7.8 Test metadata tracking for governance
  - [ ] 7.9 Test security: ensure no code injection possible
  - [ ] 7.10 Test integration with comparison module
  - [ ] 7.11 Run `ruff check src/reformlab/indicators tests/indicators`
  - [ ] 7.12 Run `mypy src/reformlab/indicators`
  - [ ] 7.13 Run `pytest tests/indicators/test_custom.py -v`

- [ ] Task 8: Module exports and API surface (AC: #1)
  - [ ] 8.1 Export `apply_custom_formula`, `apply_custom_formulas`, `CustomFormulaConfig`, `FormulaValidationError` from `src/reformlab/indicators/__init__.py`
  - [ ] 8.2 Add concise docstrings for public custom formula functions/classes
  - [ ] 8.3 Update module docstring to include Story 4.6

## Dependencies

- **Required prior stories:**
  - Story 4-1 (BKL-401): Distributional indicators — provides `IndicatorResult`, `DecileIndicators`
  - Story 4-2 (BKL-402): Geographic aggregation — provides `RegionIndicators`
  - Story 4-3 (BKL-403): Welfare indicators — provides `WelfareIndicators`
  - Story 4-4 (BKL-404): Fiscal indicators — provides `FiscalIndicators`
  - Story 4-5 (BKL-405): Scenario comparison tables — provides `compare_scenarios()`, `ComparisonResult`

- **Current prerequisite status (from sprint-status.yaml):**
  - `4-1-implement-distributional-indicators`: `done`
  - `4-2-implement-geographic-aggregation-indicators`: `done`
  - `4-3-implement-welfare-indicators`: `done`
  - `4-4-implement-fiscal-indicators`: `done`
  - `4-5-implement-scenario-comparison-tables`: `done`
  - All prerequisites met. Story 4-6 is ready for implementation.

- **Follow-on stories:**
  - Story 5-1 (BKL-501): Immutable run manifest schema (may consume custom formula metadata)
  - Story 6-1 (BKL-601): Stable Python API for run orchestration (will expose custom formula API)
  - Epic 4 Retrospective: After this story completes, Epic 4 is done

## Dev Notes

### Architecture Patterns

This story completes the Indicator Engine layer by adding custom derived formulas:

```
+-------------------------------------------------+
|  Indicator Engine (distributional/welfare/fiscal)|
|  ├── compute_distributional_indicators()        |
|  ├── compute_geographic_indicators()            |
|  ├── compute_welfare_indicators()               |
|  ├── compute_fiscal_indicators()                |
|  ├── compare_scenarios()                        |
|  └── apply_custom_formula()  <- Story 4-6 adds  |
+-------------------------------------------------+
|  Governance (manifests, assumptions, lineage)    |
+-------------------------------------------------+
```

Custom formulas provide analyst extensibility without code changes, supporting:
- Domain-specific ratios (e.g., `carbon_intensity = emissions / income`)
- Normalized metrics (e.g., `cost_per_household = total_cost / count`)
- Policy-specific thresholds (e.g., `above_poverty = income > 12000`)
- Composite indicators (e.g., `welfare_efficiency = net_change / cost`)

### Data Flow

```
IndicatorResult (from 4-1, 4-2, 4-3, 4-4)
         |
         v
CustomFormulaConfig (output_field, expression)
         |
         v
apply_custom_formula(result, formula)
         |
         v
Parse and validate formula expression
         |
         v
Evaluate formula using PyArrow compute
         |
         v
IndicatorResult (with derived field added)
         |
         +---> to_table() includes derived column
         +---> metadata includes formula audit trail
         +---> compare_scenarios() works with derived fields
```

### Technical Stack

- **PyArrow** for all data manipulation (consistent with existing codebase)
- **PyArrow compute (pc)** for arithmetic operations: `pc.add`, `pc.subtract`, `pc.multiply`, `pc.divide`
- **No dynamic code evaluation** — safe expression parsing only
- Follow existing patterns from `src/reformlab/indicators/` modules

### Key Implementation Details

1. **CustomFormulaConfig Dataclass:**
   ```python
   @dataclass
   class CustomFormulaConfig:
       """Configuration for a custom derived indicator formula.

       Attributes:
           output_field: Name of the derived field to create.
           expression: Formula expression string (e.g., "revenue - cost").
           description: Human-readable description for documentation/governance.
       """
       output_field: str
       expression: str
       description: str = ""
   ```

2. **FormulaValidationError Exception:**
   ```python
   class FormulaValidationError(ValueError):
       """Raised when a custom formula has invalid syntax or references.

       Attributes:
           message: Error description.
           position: Character position of the error in the expression.
           suggestion: Optional suggested correction.
       """
       def __init__(
           self,
           message: str,
           position: int | None = None,
           suggestion: str | None = None,
       ):
           self.position = position
           self.suggestion = suggestion
           super().__init__(message)
   ```

3. **Formula Parser Approach:**
   Use a simple recursive descent parser or shunting-yard algorithm for safe expression parsing:
   - Tokenize: split into numbers, identifiers, operators, parentheses
   - Parse: build expression tree respecting operator precedence
   - Validate: check all identifiers exist in available fields
   - Evaluate: convert tree to PyArrow compute operations

4. **Operator Precedence:**
   - `*`, `/`: higher precedence
   - `+`, `-`: lower precedence
   - Parentheses override precedence

5. **Division by Zero Handling:**
   ```python
   def _safe_divide(numerator: pa.Array, denominator: pa.Array) -> pa.Array:
       """Divide with null for zero denominator."""
       is_zero = pc.equal(denominator, 0.0)
       result = pc.divide(numerator, denominator)
       return pc.if_else(is_zero, pa.scalar(None, type=pa.float64()), result)
   ```

6. **Field Resolution:**
   ```python
   def _resolve_field(table: pa.Table, field_name: str) -> pa.Array:
       """Resolve field name to PyArrow array from table."""
       if field_name not in table.column_names:
           available = ", ".join(sorted(table.column_names))
           msg = f"Field '{field_name}' not found. Available: {available}"
           raise FormulaValidationError(msg)
       return table[field_name]
   ```

### Security Considerations

**CRITICAL: No arbitrary code execution.**

The formula engine must:
- Parse expressions into a safe AST (no Python dynamic evaluation)
- Whitelist allowed operations: +, -, *, /
- Whitelist allowed identifiers: column names only
- Reject any input containing dangerous patterns
- Use PyArrow compute functions exclusively for evaluation

### Code Patterns from Previous Stories to Reuse

From `src/reformlab/indicators/types.py`:
- `IndicatorResult` dataclass pattern for result containers
- Metadata dictionary structure for governance
- `to_table()` method pattern for stable table output

From `src/reformlab/indicators/comparison.py`:
- Error message formatting with available options
- Warning emission pattern
- Metadata preservation pattern
- PyArrow table manipulation patterns

From `src/reformlab/indicators/fiscal.py`:
- Config-driven computation pattern
- Field validation with clear error messages

### Example Use Cases

1. **Carbon Intensity Ratio:**
   ```python
   formula = CustomFormulaConfig(
       output_field="carbon_intensity",
       expression="emissions / income",
       description="Carbon emissions per unit of income"
   )
   result = apply_custom_formula(distributional_result, formula)
   ```

2. **Cost Per Household:**
   ```python
   formula = CustomFormulaConfig(
       output_field="cost_per_household",
       expression="sum / count",
       description="Average cost per household in group"
   )
   ```

3. **Welfare Efficiency:**
   ```python
   formulas = [
       CustomFormulaConfig("abs_cost", "total_loss * -1"),
       CustomFormulaConfig("welfare_efficiency", "net_change / abs_cost"),
   ]
   result = apply_custom_formulas(welfare_result, formulas)
   ```

4. **Threshold Indicator (future extension):**
   ```python
   # Note: comparison operators may be Phase 2
   formula = CustomFormulaConfig(
       output_field="above_median",
       expression="mean > 50000",  # Requires comparison ops
   )
   ```

### Scope Guardrails

- **In scope:**
  - Arithmetic operations: +, -, *, /
  - Parentheses for precedence
  - Field references to existing indicator columns
  - Numeric constants (int, float)
  - Chained formula application
  - Metadata tracking for governance
  - Integration with comparison module

- **Out of scope (potential Phase 2):**
  - Comparison operators (>, <, >=, <=, ==, !=)
  - Logical operators (and, or, not)
  - Conditional expressions (if-else)
  - Aggregate functions (sum, avg, count over groups)
  - String operations
  - Date/time operations
  - User-defined functions
  - External data lookups

### File Structure

```
src/reformlab/indicators/
|-- __init__.py           # Public exports (add custom formula exports)
|-- types.py              # Existing indicator types
|-- deciles.py            # [existing]
|-- distributional.py     # [existing]
|-- geographic.py         # [existing]
|-- welfare.py            # [existing]
|-- fiscal.py             # [existing]
|-- comparison.py         # [existing]
+-- custom.py             # NEW: apply_custom_formula(), CustomFormulaConfig, etc.
```

### Testing Standards

- Use pytest with fixtures following existing patterns in `tests/indicators/`
- Create test fixtures with known indicator values for predictable formula results
- Test edge cases:
  - Simple arithmetic: `a + b`, `a - b`, `a * b`, `a / b`
  - Precedence: `a + b * c` vs `(a + b) * c`
  - Nested parentheses: `((a + b) * c) / d`
  - Division by zero: null result, no exception
  - Missing field references: clear error with available fields
  - Invalid syntax: unbalanced parens, unknown operators
  - Security: injection attempts rejected
  - Chained formulas with dependencies
  - Metadata tracking verification
  - Comparison integration

### Performance Considerations

- Vectorized PyArrow operations (not row-by-row Python loops) per NFR2
- Formula parsing happens once per formula, not per row
- Evaluation uses PyArrow native compute (optimized C++)
- No Python loops in the hot path

### UX Context (from UX Design Specification)

Custom formulas support the analyst workflows:
- **Sophie (Policy Analyst):** Defines domain-specific ratios without coding
- **Marco (Researcher):** Creates custom metrics for journal appendices
- Formula definitions become part of the run manifest for reproducibility

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems] - Indicator layer definition
- [Source: _bmad-output/planning-artifacts/prd.md#FR23] - FR23: Analyst can define custom indicators as derived formulas over run outputs
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-406] - Story in backlog
- [Source: src/reformlab/indicators/types.py] - IndicatorResult, config patterns
- [Source: src/reformlab/indicators/comparison.py] - Comparison patterns, error handling
- [Source: src/reformlab/indicators/__init__.py] - Current indicator module exports
- [Source: _bmad-output/implementation-artifacts/4-5-implement-scenario-comparison-tables.md] - Previous story patterns

### Project Structure Notes

- New module `custom.py` follows established pattern in `src/reformlab/indicators/`
- Export new types from `__init__.py` consistent with existing indicator exports
- Formula validation error extends ValueError for consistency with existing error patterns

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
