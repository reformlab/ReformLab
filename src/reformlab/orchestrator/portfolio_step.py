"""Portfolio computation step for executing multi-policy portfolios.

This module provides:
- PortfolioComputationStep: OrchestratorStep for portfolio execution
- PortfolioComputationStepError: Error during portfolio computation
- PORTFOLIO_METADATA_KEY: Stable key for portfolio metadata in YearState.metadata
- PORTFOLIO_RESULTS_KEY: Stable key for per-policy results in YearState.data

Story 12.3 / FR44: Extend orchestrator to execute policy portfolios.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from reformlab.orchestrator.computation_step import (
    COMPUTATION_METADATA_KEY,
    COMPUTATION_RESULT_KEY,
)

if TYPE_CHECKING:
    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.computation.types import (
        ComputationResult,
        PopulationData,
    )
    from reformlab.computation.types import PolicyConfig as ComputationPolicyConfig
    from reformlab.orchestrator.types import YearState
    from reformlab.templates.portfolios.portfolio import (
        PolicyConfig as PortfolioPolicyConfig,
    )
    from reformlab.templates.portfolios.portfolio import PolicyPortfolio
    from reformlab.templates.schema import CustomPolicyType, PolicyType

logger = logging.getLogger(__name__)


# ============================================================================
# Stable keys for portfolio data in YearState
# ============================================================================

PORTFOLIO_METADATA_KEY = "portfolio_metadata"
PORTFOLIO_RESULTS_KEY = "portfolio_results"


# ============================================================================
# Error class
# ============================================================================


class PortfolioComputationStepError(Exception):
    """Error during portfolio computation step execution.

    Includes policy context (index, name, type), adapter version, year,
    and original error for debugging and governance tracking.
    """

    def __init__(
        self,
        message: str,
        *,
        year: int,
        adapter_version: str,
        policy_index: int,
        policy_name: str,
        policy_type: str,
        original_error: Exception | None = None,
    ) -> None:
        self.year = year
        self.adapter_version = adapter_version
        self.policy_index = policy_index
        self.policy_name = policy_name
        self.policy_type = policy_type
        self.original_error = original_error
        super().__init__(message)


# ============================================================================
# Bridge function
# ============================================================================


def _to_computation_policy(
    policy_config: PortfolioPolicyConfig,
) -> ComputationPolicyConfig:
    """Convert a portfolio PolicyConfig to a computation PolicyConfig.

    Both layers now use typed PolicyParameters objects. The portfolio
    PolicyConfig wraps policy with portfolio metadata; the computation
    PolicyConfig wraps policy with name/description for the adapter.
    """
    from reformlab.computation.types import PolicyConfig as ComputationPolicyConfig

    assert policy_config.policy_type is not None  # guaranteed by __post_init__
    return ComputationPolicyConfig(
        policy=policy_config.policy,
        name=policy_config.name or policy_config.policy_type.value,
        description=f"{policy_config.policy_type.value} policy",
    )


# ============================================================================
# Result merging
# ============================================================================


def _merge_policy_results(
    results: list[ComputationResult],
    portfolio: PolicyPortfolio,
) -> pa.Table:
    """Merge output tables from multiple policies into a single table.

    Strategy: join all output tables on ``household_id``. The first result
    keeps column names as-is. Subsequent results prefix columns with
    ``{policy_type}_`` to avoid collisions. If two policies share the
    same policy_type, ALL are prefixed with ``{policy_type}_{index}_``.

    All policy results must contain identical ``household_id`` sets with
    no duplicates — mismatches raise ``PortfolioComputationStepError``
    per the fail-loud data-contract rule.

    Args:
        results: Ordered list of ComputationResult from each policy.
        portfolio: The portfolio providing policy metadata.

    Returns:
        Merged pa.Table with household_id first, then columns from
        each policy in portfolio order.

    Raises:
        PortfolioComputationStepError: If any result lacks household_id,
            contains duplicate household_ids, or has mismatched id sets.
    """
    if not results:
        return pa.table({"household_id": pa.array([], type=pa.int64())})

    # Validate household_id column presence, uniqueness, and set consistency
    reference_ids: set[Any] | None = None
    for i, result in enumerate(results):
        table = result.output_fields
        policy_cfg = portfolio.policies[i]
        assert policy_cfg.policy_type is not None  # guaranteed by __post_init__
        policy_name = policy_cfg.name or policy_cfg.policy_type.value

        if "household_id" not in table.column_names:
            raise PortfolioComputationStepError(
                f"Policy[{i}] '{policy_name}' "
                f"output_fields missing required 'household_id' column",
                year=result.period,
                adapter_version=result.adapter_version,
                policy_index=i,
                policy_name=policy_name,
                policy_type=policy_cfg.policy_type.value,
            )

        hh_ids = table.column("household_id").to_pylist()
        hh_id_set = set(hh_ids)

        # Check for duplicate household_ids within a single policy result
        if len(hh_ids) != len(hh_id_set):
            raise PortfolioComputationStepError(
                f"Policy[{i}] '{policy_name}' output_fields contains "
                f"duplicate household_id values ({len(hh_ids)} rows, "
                f"{len(hh_id_set)} unique)",
                year=result.period,
                adapter_version=result.adapter_version,
                policy_index=i,
                policy_name=policy_name,
                policy_type=policy_cfg.policy_type.value,
            )

        # Check household_id set consistency across policies
        if reference_ids is None:
            reference_ids = hh_id_set
        elif hh_id_set != reference_ids:
            missing = reference_ids - hh_id_set
            extra = hh_id_set - reference_ids
            raise PortfolioComputationStepError(
                f"Policy[{i}] '{policy_name}' household_id set differs "
                f"from policy[0]: missing={missing}, extra={extra}",
                year=result.period,
                adapter_version=result.adapter_version,
                policy_index=i,
                policy_name=policy_name,
                policy_type=policy_cfg.policy_type.value,
            )

    # Detect duplicate policy types to decide prefixing strategy
    type_counts: dict[str, int] = {}
    for policy_cfg in portfolio.policies:
        assert policy_cfg.policy_type is not None  # guaranteed by __post_init__
        ptype = policy_cfg.policy_type.value
        type_counts[ptype] = type_counts.get(ptype, 0) + 1

    has_duplicate_types = any(count > 1 for count in type_counts.values())

    # Build merged table starting from household_id of first result
    merged = results[0].output_fields.select(["household_id"])

    for i, (result, policy_cfg) in enumerate(
        zip(results, portfolio.policies, strict=True)
    ):
        table = result.output_fields
        assert policy_cfg.policy_type is not None  # guaranteed by __post_init__
        ptype = policy_cfg.policy_type.value
        non_id_cols = [c for c in table.column_names if c != "household_id"]

        # Determine prefix
        if i == 0 and not has_duplicate_types:
            # First policy keeps original names when no type duplicates
            prefix = ""
        elif has_duplicate_types:
            prefix = f"{ptype}_{i}_"
        else:
            prefix = f"{ptype}_"

        # Build renamed table in a single construction
        col_arrays = [table.column("household_id")]
        col_names = ["household_id"]
        for col_name in non_id_cols:
            new_name = f"{prefix}{col_name}" if prefix else col_name
            col_arrays.append(table.column(col_name))
            col_names.append(new_name)
        renamed_table = pa.table(
            dict(zip(col_names, col_arrays, strict=True))
        )

        # Join on household_id
        if i == 0:
            merged = renamed_table
        else:
            # Left outer preserves all households from the base table.
            # Mismatched sets are already caught above, so this is
            # effectively an equi-join with guaranteed full overlap.
            merged = merged.join(
                renamed_table,
                keys="household_id",
                join_type="left outer",
            )

    return merged


# ============================================================================
# PortfolioComputationStep
# ============================================================================


class PortfolioComputationStep:
    """Orchestrator step for executing a policy portfolio.

    Iterates over each policy in the portfolio, invokes the adapter
    for each, merges results into a single ComputationResult stored
    under COMPUTATION_RESULT_KEY for panel compatibility.

    Implements the OrchestratorStep protocol.
    """

    __slots__ = (
        "_adapter",
        "_population",
        "_portfolio",
        "_name",
        "_depends_on",
        "_description",
    )

    def __init__(
        self,
        adapter: ComputationAdapter,
        population: PopulationData,
        portfolio: PolicyPortfolio,
        name: str = "portfolio_computation",
        depends_on: tuple[str, ...] = (),
        description: str | None = None,
    ) -> None:
        """Initialize the portfolio computation step.

        Args:
            adapter: ComputationAdapter to invoke for each policy.
            population: PopulationData to pass to adapter.
            portfolio: PolicyPortfolio with 2+ policies.
            name: Step name for registry.
            depends_on: Names of steps this step depends on.
            description: Optional description.

        Raises:
            PortfolioComputationStepError: If portfolio has < 2 policies
                or contains an invalid policy type.
        """
        self._adapter = adapter
        self._population = population
        self._portfolio = portfolio
        self._name = name
        self._depends_on = depends_on
        self._description = (
            description or "Portfolio computation step for multi-policy execution"
        )

        # Defensive validation (should be guaranteed by PolicyPortfolio.__post_init__)
        if len(portfolio.policies) < 2:
            raise PortfolioComputationStepError(
                f"Portfolio must have at least 2 policies, got {len(portfolio.policies)}",
                year=0,
                adapter_version="<not-started>",
                policy_index=-1,
                policy_name="",
                policy_type="",
            )

        # Validate each policy type at construction time (fail fast)
        for i, policy_cfg in enumerate(portfolio.policies):
            assert policy_cfg.policy_type is not None  # guaranteed by __post_init__
            _validate_policy_type(policy_cfg.policy_type, i, policy_cfg)

    @property
    def name(self) -> str:
        """Unique identifier for this step."""
        return self._name

    @property
    def depends_on(self) -> tuple[str, ...]:
        """Names of steps this step depends on."""
        return self._depends_on

    @property
    def description(self) -> str:
        """Human-readable description of the step."""
        return self._description

    def execute(self, year: int, state: YearState) -> YearState:
        """Execute all portfolio policies for a given year.

        Iterates over policies in tuple order (deterministic), invokes
        the adapter for each, merges results, and stores them in
        YearState for panel compatibility.

        Args:
            year: Current simulation year.
            state: Current year state.

        Returns:
            New YearState with merged computation result and metadata.

        Raises:
            PortfolioComputationStepError: If any policy computation fails.
        """
        # Get adapter version with fallback
        adapter_version = _get_adapter_version(self._adapter, year, self._name)

        # Execute each policy in order
        policy_results: list[ComputationResult] = []
        execution_records: list[dict[str, Any]] = []

        for i, policy_cfg in enumerate(self._portfolio.policies):
            comp_policy = _to_computation_policy(policy_cfg)
            assert policy_cfg.policy_type is not None  # guaranteed by __post_init__
            policy_name = policy_cfg.name or policy_cfg.policy_type.value
            policy_type_value = policy_cfg.policy_type.value

            try:
                result = self._adapter.compute(
                    population=self._population,
                    policy=comp_policy,
                    period=year,
                )
            except Exception as e:
                logger.error(
                    "event=portfolio_computation_error year=%d "
                    "policy_index=%d policy_type=%s adapter_version=%s",
                    year,
                    i,
                    policy_type_value,
                    adapter_version,
                )
                raise PortfolioComputationStepError(
                    f"Portfolio computation failed at year {year}, "
                    f"policy[{i}] '{policy_name}' ({policy_type_value}): "
                    f"{type(e).__name__}: {e}",
                    year=year,
                    adapter_version=adapter_version,
                    policy_index=i,
                    policy_name=policy_name,
                    policy_type=policy_type_value,
                    original_error=e,
                ) from e

            policy_results.append(result)

            row_count = result.output_fields.num_rows
            execution_records.append(
                {
                    "policy_index": i,
                    "policy_type": policy_type_value,
                    "policy_name": policy_name,
                    "adapter_version": adapter_version,
                    "row_count": row_count,
                }
            )

            logger.info(
                "event=portfolio_policy_computed year=%d policy_index=%d "
                "policy_type=%s adapter_version=%s row_count=%d",
                year,
                i,
                policy_type_value,
                adapter_version,
                row_count,
            )

        # Merge all results into a single table
        merged_table = _merge_policy_results(policy_results, self._portfolio)

        # Build merged ComputationResult for panel compatibility
        from reformlab.computation.types import ComputationResult

        merged_result = ComputationResult(
            output_fields=merged_table,
            adapter_version=adapter_version,
            period=year,
            metadata={"source": "portfolio", "policy_count": len(policy_results)},
            entity_tables={},
        )

        # Build portfolio metadata
        portfolio_metadata: dict[str, Any] = {
            "portfolio_name": self._portfolio.name,
            "policy_count": len(policy_results),
            "execution_records": execution_records,
            "execution_order": [
                r["policy_name"] for r in execution_records
            ],
        }

        # Build computation metadata (backward compat with runner.py)
        computation_metadata: dict[str, Any] = {
            "adapter_version": adapter_version,
            "computation_period": year,
            "computation_row_count": merged_table.num_rows,
            "source": "portfolio",
            "policy_count": len(policy_results),
        }

        # Update state immutably
        new_data = dict(state.data)
        new_data[COMPUTATION_RESULT_KEY] = merged_result
        new_data[PORTFOLIO_RESULTS_KEY] = tuple(policy_results)

        new_metadata = dict(state.metadata)
        new_metadata[PORTFOLIO_METADATA_KEY] = portfolio_metadata
        new_metadata[COMPUTATION_METADATA_KEY] = computation_metadata

        logger.info(
            "event=portfolio_computation_complete year=%d portfolio=%s policy_count=%d",
            year,
            self._portfolio.name,
            len(policy_results),
        )

        return replace(state, data=new_data, metadata=new_metadata)


# ============================================================================
# Helpers
# ============================================================================


def _get_adapter_version(
    adapter: ComputationAdapter, year: int, step_name: str
) -> str:
    """Get adapter version with fallback to placeholder."""
    adapter_version = "<version-unavailable>"
    try:
        adapter_version = adapter.version()
    except Exception:
        logger.debug(
            "year=%d step_name=%s adapter_version=%s event=adapter_version_fallback",
            year,
            step_name,
            adapter_version,
        )
    return adapter_version


def _validate_policy_type(
    policy_type: PolicyType | CustomPolicyType,
    index: int,
    policy_cfg: PortfolioPolicyConfig,
) -> None:
    """Validate that a policy type is a valid PolicyType enum value or registered custom type."""
    from reformlab.templates.schema import CustomPolicyType
    from reformlab.templates.schema import PolicyType as PolicyTypeEnum

    if not isinstance(policy_type, (PolicyTypeEnum, CustomPolicyType)):
        raise PortfolioComputationStepError(
            f"Invalid policy_type at index {index}: {policy_type!r}",
            year=0,
            adapter_version="<not-started>",
            policy_index=index,
            policy_name=policy_cfg.name or str(policy_type),
            policy_type=str(policy_type),
        )
