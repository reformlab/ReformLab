# Extending ReformLab

**How to read this document:** Each section covers one extension point. For each, you'll find: *what problem it solves*, *what protocol to implement*, *a concrete example*, and *where to register it*.

---

## 1. Adding a Computation Backend

**Problem:** You want to use a different tax-benefit engine instead of OpenFisca (or a mock for testing).

**Protocol:** `ComputationAdapter` (`src/reformlab/computation/adapter.py`)

```python
from typing import runtime_checkable, Protocol
from reformlab.computation.types import PopulationData, PolicyConfig, ComputationResult

@runtime_checkable
class ComputationAdapter(Protocol):
    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult: ...

    def version(self) -> str: ...
```

**How to implement:** Create a class with `compute()` and `version()` methods. No inheritance required — Python's structural typing (duck typing) handles it.

```python
import pyarrow as pa
from reformlab.computation.types import PopulationData, PolicyConfig, ComputationResult

class MyCustomAdapter:
    """A custom computation backend."""

    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult:
        # Your computation logic here
        table = population.tables["default"]
        output = table  # transform as needed
        return ComputationResult(
            output_fields=output,
            adapter_version=self.version(),
            period=period,
            metadata={"engine": "custom"},
        )

    def version(self) -> str:
        return "custom-1.0.0"
```

**Where to register:** The adapter is injected via `get_adapter()` in `src/reformlab/server/dependencies.py`. For server use, modify `_create_adapter()`. For Python API use, pass it to `run_scenario(config, adapter=my_adapter)`.

**Existing implementations:**
- `OpenFiscaAdapter` — Full OpenFisca integration (`src/reformlab/computation/openfisca_adapter.py`)
- `MockAdapter` — Deterministic mock for testing (`src/reformlab/computation/mock_adapter.py`)

---

## 2. Adding an Orchestrator Step

**Problem:** You want to add a new processing step to the yearly simulation loop (e.g., a new behavioral model, data transformation, or logging step).

**Protocol:** `OrchestratorStep` (`src/reformlab/orchestrator/step.py`)

```python
@runtime_checkable
class OrchestratorStep(Protocol):
    @property
    def name(self) -> str: ...

    def execute(self, year: int, state: YearState) -> YearState: ...

    # Optional:
    @property
    def depends_on(self) -> tuple[str, ...]: ...

    @property
    def description(self) -> str: ...
```

**Option A — Class-based step:**

```python
from reformlab.orchestrator.types import YearState

class CarbonAccountingStep:
    """Compute per-household carbon footprint after policy application."""

    @property
    def name(self) -> str:
        return "carbon_accounting"

    @property
    def depends_on(self) -> tuple[str, ...]:
        return ("computation",)  # runs after the computation step

    @property
    def description(self) -> str:
        return "Calculate household carbon footprints"

    def execute(self, year: int, state: YearState) -> YearState:
        # Access population and results from state
        table = state.population.tables["default"]
        # ... compute carbon footprint ...
        return YearState(
            year=state.year,
            population=state.population,
            policy=state.policy,
            results={**state.results, "carbon_footprint": footprint_data},
            metadata=state.metadata,
        )
```

**Option B — Function-based step using the `@step()` decorator:**

```python
from reformlab.orchestrator import step, YearState

@step(name="carbon_accounting", depends_on=("computation",))
def carbon_accounting(year: int, state: YearState) -> YearState:
    # ... same logic ...
    return state
```

**Option C — Bare callable (simplest, no dependencies):**

```python
def my_logger(year: int, state: YearState) -> YearState:
    print(f"Year {year}: {state.population.row_count} rows")
    return state  # pass-through
```

**Where to register:** Add steps to a `StepRegistry`, which handles topological sorting based on `depends_on` declarations:

```python
from reformlab.orchestrator.step import StepRegistry

registry = StepRegistry()
registry.register(CarbonAccountingStep())
pipeline = registry.build_pipeline()  # topologically sorted
```

The orchestrator detects circular dependencies and raises an error at build time.

**Built-in steps:**
- `computation_step` — Runs the ComputationAdapter
- `carry_forward_step` — Carries state between years
- `portfolio_step` — Handles portfolio policy combination
- `VintageTransitionStep` — Ages capital stock
- `DiscreteChoiceStep` / `LogitChoiceStep` — Behavioral decisions

---

## 3. Adding a New Policy Type

**Problem:** The built-in types (`carbon_tax`, `subsidy`, `rebate`, `feebate`) don't cover your policy design.

**Registration functions:** `src/reformlab/templates/schema.py`

```python
from reformlab.templates.schema import (
    register_policy_type,
    register_custom_template,
    PolicyParameters,
)
from dataclasses import dataclass

# Step 1: Register the new type
my_type = register_policy_type("congestion_charge")

# Step 2: Define its parameters
@dataclass(frozen=True)
class CongestionChargeParameters(PolicyParameters):
    zone_radius_km: float = 5.0
    peak_multiplier: float = 2.0
    exempt_vehicles: tuple[str, ...] = ("ev", "hybrid")

# Step 3: Link them
register_custom_template(my_type, CongestionChargeParameters)
```

After registration, the new type works everywhere: scenarios, portfolios, templates, and the API.

**Lookup functions:**
- `get_policy_type("congestion_charge")` — Returns the `CustomPolicyType`
- `infer_policy_type(params_instance)` — Returns the type from a parameters instance

---

## 4. Adding a Data Source Loader

**Problem:** You want to load population data from a new institutional source (e.g., a national statistics office).

**Protocol:** `DataSourceLoader` (`src/reformlab/population/loaders/base.py`)

```python
@runtime_checkable
class DataSourceLoader(Protocol):
    def download(self, config: SourceConfig) -> pa.Table: ...
    def status(self, config: SourceConfig) -> CacheStatus: ...
    def schema(self) -> pa.Schema: ...
```

**Recommended approach:** Subclass `CachedLoader` for automatic caching:

```python
from reformlab.population.loaders.base import CachedLoader, SourceConfig
import pyarrow as pa

class StatCanLoader(CachedLoader):
    """Loader for Statistics Canada datasets."""

    def _fetch(self, config: SourceConfig) -> pa.Table:
        # Download and parse data from StatCan
        # Return as a PyArrow Table
        ...

    def schema(self) -> pa.Schema:
        return pa.schema([
            ("household_id", pa.int64()),
            ("income", pa.float64()),
            ("province", pa.string()),
            ...
        ])
```

`CachedLoader` handles the download lifecycle: check cache → fetch if stale → store locally → return table.

**Existing loaders:**
- `INSEELoader` — French census/fiscal data
- `EurostatLoader` — European statistics
- `ADEMELoader` — Emissions factors
- `SDESLoader` — Vehicle/transport data

**Catalog registration:** Each loader has a catalog dict mapping dataset IDs to metadata. Register yours in `src/reformlab/population/__init__.py`.

---

## 5. Adding a Merge Method

**Problem:** The built-in merge methods (`uniform`, `ipf`, `conditional`) don't match your statistical assumptions about how datasets should be combined.

**Protocol:** `MergeMethod` (`src/reformlab/population/methods/base.py`)

```python
@runtime_checkable
class MergeMethod(Protocol):
    @property
    def name(self) -> str: ...

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult: ...
```

**Example:**

```python
from reformlab.population.methods.base import MergeConfig, MergeResult, MergeAssumption
import pyarrow as pa

class NearestNeighborMethod:
    """Match households by similarity in shared variables."""

    @property
    def name(self) -> str:
        return "nearest_neighbor"

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult:
        # Your matching logic here
        merged_table = ...
        return MergeResult(
            table=merged_table,
            assumption=MergeAssumption(
                method="nearest_neighbor",
                description=(
                    "Matched households by Euclidean distance in shared "
                    "variable space. Assumes similarity in observed variables "
                    "implies similarity in unobserved variables."
                ),
            ),
        )
```

**Important:** Every merge method must produce a `MergeAssumption` that documents its statistical assumptions in plain language. This is a non-optional governance requirement (FR39).

**Existing methods:**
- `UniformMergeMethod` — Independent random matching
- `IPFMergeMethod` — Iterative Proportional Fitting with marginal constraints
- `ConditionalSamplingMethod` — Stratified random matching

---

## 6. Adding a Discrete Choice Domain

**Problem:** You want to model a new household decision (beyond vehicle and heating choices).

**Protocol:** `DecisionDomain` (`src/reformlab/discrete_choice/domain.py`)

```python
@runtime_checkable
class DecisionDomain(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def alternatives(self) -> tuple[Alternative, ...]: ...

    @property
    def cost_column(self) -> str: ...

    def apply_alternative(
        self, table: pa.Table, alternative: Alternative
    ) -> pa.Table: ...
```

**Example:**

```python
from reformlab.discrete_choice.types import Alternative

class DietDomain:
    """Model household dietary transition decisions."""

    @property
    def name(self) -> str:
        return "diet"

    @property
    def alternatives(self) -> tuple[Alternative, ...]:
        return (
            Alternative(id="current", label="Current Diet",
                       attributes={"cost": 0.0, "emissions": 1.0}),
            Alternative(id="flexitarian", label="Flexitarian",
                       attributes={"cost": -0.05, "emissions": 0.6}),
            Alternative(id="vegetarian", label="Vegetarian",
                       attributes={"cost": -0.15, "emissions": 0.4}),
        )

    @property
    def cost_column(self) -> str:
        return "diet_annual_cost"

    def apply_alternative(
        self, table: pa.Table, alternative: Alternative
    ) -> pa.Table:
        # Modify the population table based on the chosen alternative
        # e.g., adjust food expenditure and emissions columns
        ...
```

**Integration:** Create a `DiscreteChoiceStep` or `LogitChoiceStep` with your domain and register it as an orchestrator step.

**Existing domains:**
- Vehicle domain — `keep_current`, `buy_petrol`, `buy_diesel`, `buy_hybrid`, `buy_ev`, `buy_no_vehicle`
- Heating domain — `keep_current`, `gas_boiler`, `heat_pump`, `electric`, `wood_pellet`

---

## 7. Adding a New Indicator

**Problem:** You want to compute a new type of analysis from simulation results.

**Pattern:** Add a compute function and register it in the indicators module.

```python
import pyarrow as pa
from reformlab.indicators.types import IndicatorResult

def compute_energy_poverty(
    panel: pa.Table,
    *,
    energy_field: str = "energy_expenditure",
    income_field: str = "income",
    threshold: float = 0.10,
    by_year: bool = False,
) -> IndicatorResult:
    """Compute energy poverty indicators.

    A household is energy-poor if energy expenditure exceeds
    the threshold fraction of income.
    """
    # Your computation logic using PyArrow compute
    ...
    return IndicatorResult(
        indicator_type="energy_poverty",
        data=result_data,
        metadata={"threshold": threshold},
        warnings=[],
        excluded_count=0,
    )
```

**Where to register:** Add to `src/reformlab/indicators/__init__.py` and update the `VALID_INDICATOR_TYPES` set in `src/reformlab/server/routes/indicators.py` if you want API access.

---

## Summary of Extension Points

| Extension | Protocol / Pattern | Location | Registration |
|-----------|-------------------|----------|--------------|
| Computation backend | `ComputationAdapter` | `computation/adapter.py` | `dependencies.py` or `run_scenario(adapter=)` |
| Orchestrator step | `OrchestratorStep` or `@step()` | `orchestrator/step.py` | `StepRegistry.register()` |
| Policy type | `register_policy_type()` | `templates/schema.py` | Module-level call |
| Data source | `DataSourceLoader` / `CachedLoader` | `population/loaders/base.py` | `population/__init__.py` |
| Merge method | `MergeMethod` | `population/methods/base.py` | Pipeline configuration |
| Decision domain | `DecisionDomain` | `discrete_choice/domain.py` | `DiscreteChoiceStep` constructor |
| Indicator | Function returning `IndicatorResult` | `indicators/` | `__init__.py` + route registration |

All protocols use `@runtime_checkable` and structural typing — no inheritance required.
