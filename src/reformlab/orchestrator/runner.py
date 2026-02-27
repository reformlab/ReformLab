"""Yearly loop orchestrator implementation.

Executes a step pipeline for each year in a projection horizon,
managing deterministic state transitions and seed control.

Story 3-6: Adds structured logging and execution trace metadata.
Story 5-3: Adds automatic lineage capture for parent-child relationships.
"""

from __future__ import annotations

import logging
import uuid
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict, cast

from reformlab.governance.capture import (
    capture_assumptions,
    capture_mappings,
    capture_parameters,
    capture_warnings,
)
from reformlab.governance.hashing import hash_input_artifacts, hash_output_artifacts
from reformlab.orchestrator.errors import OrchestratorError
from reformlab.orchestrator.types import (
    OrchestratorConfig,
    OrchestratorResult,
    YearState,
)

if TYPE_CHECKING:
    from reformlab.computation.mapping import MappingConfig
    from reformlab.orchestrator.types import PipelineStep
    from reformlab.templates.workflow import WorkflowConfig, WorkflowResult

logger = logging.getLogger(__name__)

# Stable metadata keys for execution trace (AC-6)
STEP_EXECUTION_LOG_KEY = "step_execution_log"
SEED_LOG_KEY = "seed_log"


class StepExecutionRecord(TypedDict):
    """Single step execution record for the execution log."""

    year: int
    step_index: int
    step_total: int
    step_name: str
    status: str  # "completed" or "failed"


class Orchestrator:
    """Yearly loop orchestrator with step pipeline execution.

    Executes an ordered step pipeline for each year from start_year
    to end_year (inclusive). Each year receives the output state from
    the previous year as input.

    The orchestrator ensures:
    - Strict year ordering (year t completes before year t+1)
    - Deterministic execution with explicit seed control
    - Clear error context on step failure with partial results
    """

    def __init__(self, config: OrchestratorConfig) -> None:
        """Initialize the orchestrator with configuration.

        Args:
            config: Orchestrator configuration with projection bounds,
                initial state, seed, and step pipeline.
        """
        self.config = config

    def run(self) -> OrchestratorResult:
        """Execute the full projection from start_year to end_year.

        Iterates through each year in the projection range, executing
        the step pipeline for each year. State is carried forward
        between years.

        Returns:
            OrchestratorResult with success status, yearly states,
            and error information if execution failed.
        """
        yearly_states: dict[int, YearState] = {}

        # AC-6: Collect execution trace metadata
        seed_log: dict[int, int | None] = {}
        step_execution_log: list[StepExecutionRecord] = []

        # Initialize state for year before start
        current_state = YearState(
            year=self.config.start_year - 1,
            data=dict(self.config.initial_state),
            seed=self._derive_year_seed(self.config.start_year - 1),
            metadata={},
        )

        logger.info(
            "Starting orchestrator run: years %d-%d with %d steps",
            self.config.start_year,
            self.config.end_year,
            len(self.config.step_pipeline),
        )

        for year in range(self.config.start_year, self.config.end_year + 1):
            logger.debug("Starting year %d", year)

            try:
                current_state, year_step_records = self._run_year(year, current_state)
                yearly_states[year] = current_state
                # AC-6: Collect seed and step execution records
                seed_log[year] = current_state.seed
                step_execution_log.extend(year_step_records)
                logger.debug("Completed year %d", year)

            except OrchestratorError as e:
                if e.step_records:
                    step_execution_log.extend(
                        cast(list[StepExecutionRecord], e.step_records)
                    )
                if e.year_seed is not None or self.config.seed is None:
                    seed_log[year] = e.year_seed
                else:
                    seed_log[year] = self._derive_year_seed(year)

                if not e.partial_states and yearly_states:
                    e.partial_states = dict(yearly_states)

                # Error already has context, just return failure result
                logger.error("Orchestrator failed at year %d: %s", year, e)
                return OrchestratorResult(
                    success=False,
                    yearly_states=yearly_states,
                    errors=[str(e)],
                    failed_year=e.year,
                    failed_step=e.step_name,
                    metadata={
                        "partial": True,
                        "start_year": self.config.start_year,
                        "end_year": self.config.end_year,
                        "seed": self.config.seed,
                        "step_pipeline": _step_pipeline_names(
                            self.config.step_pipeline
                        ),
                        "completed_years": sorted(yearly_states.keys()),
                        # AC-6: Include trace on failure path
                        SEED_LOG_KEY: seed_log,
                        STEP_EXECUTION_LOG_KEY: step_execution_log,
                    },
                )

        logger.info(
            "Orchestrator completed successfully: %d years processed",
            len(yearly_states),
        )

        return OrchestratorResult(
            success=True,
            yearly_states=yearly_states,
            errors=[],
            failed_year=None,
            failed_step=None,
            metadata={
                "start_year": self.config.start_year,
                "end_year": self.config.end_year,
                "seed": self.config.seed,
                "step_pipeline": _step_pipeline_names(self.config.step_pipeline),
                # AC-6: Include trace on success path
                SEED_LOG_KEY: seed_log,
                STEP_EXECUTION_LOG_KEY: step_execution_log,
            },
        )

    def _run_year(
        self, year: int, state: YearState
    ) -> tuple[YearState, list[StepExecutionRecord]]:
        """Execute all steps for a single year.

        Args:
            year: The year to execute.
            state: Input state from previous year.

        Returns:
            Tuple of (updated state after all steps complete, step execution records).

        Raises:
            OrchestratorError: If any step fails.
        """
        # Create state for this year with appropriate seed
        year_seed = self._derive_year_seed(year)
        current = replace(
            state,
            year=year,
            seed=year_seed,
            metadata={"previous_year": state.year},
        )

        # AC-6: Collect step execution records for this year
        step_records: list[StepExecutionRecord] = []

        # AC-1: Emit year-start INFO log with stable markers
        logger.info(
            "year=%d seed=%s master_seed=%s event=year_start",
            year,
            year_seed,
            self.config.seed,
        )
        logger.debug(
            "Year %d initialized with seed=%s (previous_year=%d)",
            year,
            current.seed,
            state.year,
        )

        # Execute empty pipeline gracefully
        step_total = len(self.config.step_pipeline)
        if step_total == 0:
            logger.debug("Year %d: empty pipeline, no steps to execute", year)
            # AC-4: Emit year-complete INFO summary (empty pipeline case)
            logger.info(
                "year=%d steps_executed=0 seed=%s adapter_version=n/a "
                "event=year_complete",
                year,
                year_seed,
            )
            return current, step_records

        # Execute each step in order (AC-2)
        adapter_version: str | None = None
        for step_index, step in enumerate(self.config.step_pipeline, start=1):
            step_name = _extract_step_name(step)
            try:
                current, step_adapter_version = self._execute_step(
                    step, year, current, step_index, step_total
                )
            except OrchestratorError as e:
                step_records.append(
                    StepExecutionRecord(
                        year=year,
                        step_index=step_index,
                        step_total=step_total,
                        step_name=step_name,
                        status="failed",
                    )
                )
                e.year_seed = year_seed
                e.step_records = [dict(record) for record in step_records]
                raise

            # Capture adapter version from computation step if present
            if step_adapter_version is not None:
                adapter_version = step_adapter_version
            # AC-6: Record step execution
            step_records.append(
                StepExecutionRecord(
                    year=year,
                    step_index=step_index,
                    step_total=step_total,
                    step_name=step_name,
                    status="completed",
                )
            )

        # AC-4: Emit year-complete INFO summary
        logger.info(
            "year=%d steps_executed=%d seed=%s adapter_version=%s event=year_complete",
            year,
            step_total,
            year_seed,
            adapter_version or "n/a",
        )

        return current, step_records

    def _execute_step(
        self,
        step: "PipelineStep",
        year: int,
        state: YearState,
        step_index: int,
        step_total: int,
    ) -> tuple[YearState, str | None]:
        """Execute a single step with error handling.

        Supports both protocol-based steps (OrchestratorStep) and
        bare callables (YearStep) for backward compatibility.

        Args:
            step: The step to execute (protocol step or callable).
            year: Current year.
            state: Current state.
            step_index: 1-based index of current step in pipeline.
            step_total: Total number of steps in pipeline.

        Returns:
            Tuple of (updated state from step, adapter_version if computation step).

        Raises:
            OrchestratorError: If step raises an exception.
        """
        # Extract step name: prefer step.name for protocol steps
        step_name = _extract_step_name(step)

        # AC-2: Emit step-start DEBUG log with stable markers
        logger.debug(
            "year=%d step_index=%d step_total=%d step_name=%s event=step_start",
            year,
            step_index,
            step_total,
            step_name,
        )

        try:
            # Dispatch based on step type
            # Protocol steps have execute(), bare callables are directly callable
            if hasattr(step, "execute") and callable(getattr(step, "execute")):
                result = step.execute(year, state)
            else:
                result = step(year, state)  # type: ignore[operator]

            if not isinstance(result, YearState):
                raise TypeError(
                    f"step returned {type(result).__name__}; expected YearState"
                )

            # AC-2: Emit step-end DEBUG log with stable markers
            logger.debug(
                "year=%d step_index=%d step_total=%d step_name=%s event=step_end",
                year,
                step_index,
                step_total,
                step_name,
            )

            # Extract adapter version from computation metadata if present
            adapter_version: str | None = None
            from reformlab.orchestrator.computation_step import COMPUTATION_METADATA_KEY

            computation_meta = result.metadata.get(COMPUTATION_METADATA_KEY)
            if isinstance(computation_meta, dict):
                adapter_version = computation_meta.get("adapter_version")

            return result, adapter_version

        except Exception as e:
            logger.exception("Step %s failed at year %d", step_name, year)

            raise OrchestratorError(
                summary=f"Step '{step_name}' failed",
                reason=f"{type(e).__name__}: {e}",
                year=year,
                step_name=step_name,
                partial_states={},  # Caller will fill this
                original_error=e,
            ) from e

    def _derive_year_seed(self, year: int) -> int | None:
        """Derive a deterministic seed for a specific year.

        If a master seed is configured, derives a year-specific seed
        to ensure reproducibility while allowing year-level variation.

        Args:
            year: The year to derive seed for.

        Returns:
            Year-specific seed, or None if no master seed configured.
        """
        if self.config.seed is None:
            return None

        # Simple deterministic derivation: master_seed XOR year
        # This ensures each year gets a unique but reproducible seed
        return self.config.seed ^ year


def _extract_step_name(step: "PipelineStep") -> str:
    """Extract step name from protocol step or callable.

    Prefers step.name for protocol steps, falls back to __name__ or str.
    """
    if hasattr(step, "name"):
        return step.name
    return getattr(step, "__name__", str(step))


def from_workflow_config(config: "WorkflowConfig") -> OrchestratorConfig:
    """Create OrchestratorConfig from a WorkflowConfig.

    Maps workflow configuration fields to orchestrator parameters:
    - run_config.start_year -> start_year
    - run_config.projection_years -> end_year calculation

    Args:
        config: WorkflowConfig with run_config settings.

    Returns:
        OrchestratorConfig ready for execution.
    """
    start_year = config.run_config.start_year
    projection_years = config.run_config.projection_years
    end_year = _calculate_end_year(
        start_year=start_year,
        projection_years=projection_years,
    )

    return OrchestratorConfig(
        start_year=start_year,
        end_year=end_year,
        initial_state={},
        seed=None,
        step_pipeline=(),
    )


class OrchestratorRunner:
    """Runner adapter for run_workflow() integration.

    Implements the runner interface expected by run_workflow(),
    allowing the orchestrator to be used as a workflow backend.
    """

    def __init__(
        self,
        step_pipeline: tuple["PipelineStep", ...] = (),
        seed: int | None = None,
        initial_state: dict[str, Any] | None = None,
        assumption_defaults: dict[str, Any] | None = None,
        assumption_overrides: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
        mapping_config: MappingConfig | None = None,
        scenario_name: str = "",
        scenario_version: str = "",
        scenario_validated: bool | None = None,
        additional_warnings: list[str] | None = None,
    ) -> None:
        """Initialize the runner with step configuration.

        Args:
            step_pipeline: Ordered steps to execute per year.
            seed: Master random seed for determinism.
            initial_state: Starting state for the projection.
            assumption_defaults: Default assumption values captured in metadata.
            assumption_overrides: Assumption override values captured in metadata.
            parameters: Scenario/template parameters captured in metadata.
            mapping_config: Runtime mapping config captured in metadata.
            scenario_name: Optional scenario identifier for warning capture.
            scenario_version: Optional scenario version for warning capture.
            scenario_validated: Optional validation flag from registry metadata.
            additional_warnings: Optional additional warnings to append.
        """
        self.step_pipeline = step_pipeline
        self.seed = seed
        self.initial_state = initial_state or {}
        self.assumption_defaults = assumption_defaults or {}
        self.assumption_overrides = assumption_overrides or {}
        self.parameters = parameters or {}
        self.mapping_config = mapping_config
        self.scenario_name = scenario_name
        self.scenario_version = scenario_version
        self.scenario_validated = scenario_validated
        self.additional_warnings = list(additional_warnings or [])

    def run(self, request: dict[str, Any]) -> "WorkflowResult":
        """Execute a workflow request using the orchestrator.

        Args:
            request: Workflow request dictionary from prepare_workflow_request().
                Expected keys: run_config.start_year, run_config.projection_years.
                Optional keys: input_paths/output_paths for artifact hashing.

        Returns:
            WorkflowResult with execution outcomes.
        """
        # Import here to avoid circular imports
        from reformlab.templates.workflow import WorkflowResult

        # Extract run configuration
        run_config = request.get("run_config")
        if not isinstance(run_config, dict):
            return WorkflowResult(
                success=False,
                errors=["Invalid request: run_config must be a mapping"],
            )

        try:
            start_year = int(run_config["start_year"])
            projection_years = int(run_config["projection_years"])
            end_year = _calculate_end_year(
                start_year=start_year,
                projection_years=projection_years,
            )
        except KeyError as exc:
            return WorkflowResult(
                success=False,
                errors=[f"Invalid request: missing run_config.{exc.args[0]}"],
            )
        except (TypeError, ValueError) as exc:
            return WorkflowResult(
                success=False,
                errors=[f"Invalid run_config bounds: {exc}"],
            )

        # Story 5-3 AC-5: Generate parent manifest ID once at run start
        parent_manifest_id = str(uuid.uuid4())

        # Build orchestrator config
        config = OrchestratorConfig(
            start_year=start_year,
            end_year=end_year,
            initial_state=dict(self.initial_state),
            seed=self.seed,
            step_pipeline=self.step_pipeline,
        )

        # Execute orchestrator
        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        # Story 5-3 AC-5: Build child lineage map from completed years
        child_manifests: dict[int, str] = {}
        for year in result.yearly_states.keys():
            # Each yearly child gets its own unique manifest ID
            child_manifests[year] = str(uuid.uuid4())

        try:
            input_paths = _coerce_path_map(request.get("input_paths"))
            output_paths = _coerce_path_map(request.get("output_paths"))
        except ValueError as exc:
            return WorkflowResult(
                success=False,
                errors=[f"Invalid artifact paths: {exc}"],
            )

        manifest_capture = self._capture_manifest_fields(
            request,
            parent_manifest_id,
            child_manifests,
            input_paths=input_paths,
            output_paths=output_paths,
        )

        # Convert to WorkflowResult
        metadata: dict[str, Any] = {
            "start_year": start_year,
            "end_year": end_year,
            "failed_year": result.failed_year,
            "failed_step": result.failed_step,
            **result.metadata,
            "assumptions": manifest_capture["assumptions"],
            "mappings": manifest_capture["mappings"],
            "parameters": manifest_capture["parameters"],
            "warnings": manifest_capture["warnings"],
            "parent_manifest_id": manifest_capture["parent_manifest_id"],
            "child_manifests": manifest_capture["child_manifests"],
            "data_hashes": manifest_capture["data_hashes"],
            "output_hashes": manifest_capture["output_hashes"],
        }
        if manifest_capture["scenario_version"]:
            metadata["scenario_version"] = manifest_capture["scenario_version"]

        return WorkflowResult(
            success=result.success,
            outputs={
                "yearly_states": {
                    year: {
                        "year": state.year,
                        "data": state.data,
                        "seed": state.seed,
                        "metadata": state.metadata,
                    }
                    for year, state in result.yearly_states.items()
                },
            },
            errors=result.errors,
            metadata=metadata,
        )

    def _capture_manifest_fields(
        self,
        request: dict[str, Any],
        parent_manifest_id: str,
        child_manifests: dict[int, str],
        input_paths: dict[str, Path] | None = None,
        output_paths: dict[str, Path] | None = None,
    ) -> dict[str, Any]:
        """Capture governance metadata once at runner boundary.

        Story 5-3 AC-5: Includes lineage metadata (parent_manifest_id, child_manifests).
        Story 5-4 AC-5: Hash input/output artifacts when paths provided.
        """
        assumption_defaults = _coerce_dict(
            request.get("assumption_defaults", self.assumption_defaults)
        )
        assumption_overrides = _coerce_dict(
            request.get("assumption_overrides", self.assumption_overrides)
        )
        parameters = capture_parameters(
            _coerce_dict(request.get("parameters", self.parameters))
        )

        mapping_payload = request.get("mapping_config", self.mapping_config)
        mappings: list[dict[str, Any]] = []
        if mapping_payload is not None and hasattr(mapping_payload, "mappings"):
            mappings = capture_mappings(mapping_payload)
        elif isinstance(request.get("mappings"), list):
            mappings = deepcopy(cast(list[dict[str, Any]], request["mappings"]))

        scenario_name, scenario_version = _resolve_scenario_identity(
            request=request,
            fallback_name=self.scenario_name,
            fallback_version=self.scenario_version,
        )
        scenario_validated = _resolve_validation_flag(
            request=request,
            fallback=self.scenario_validated,
        )
        additional_warnings = _resolve_additional_warnings(
            request=request, fallback=self.additional_warnings
        )

        # Story 5-4 AC-5: Hash artifacts if paths provided
        data_hashes: dict[str, str] = {}
        if input_paths:
            data_hashes = hash_input_artifacts(input_paths)

        output_hashes: dict[str, str] = {}
        if output_paths:
            output_hashes = hash_output_artifacts(output_paths)

        return {
            "assumptions": capture_assumptions(
                defaults=assumption_defaults,
                overrides=assumption_overrides,
            ),
            "mappings": mappings,
            "parameters": parameters,
            "warnings": capture_warnings(
                scenario_name=scenario_name,
                scenario_version=scenario_version,
                is_validated=scenario_validated,
                additional_warnings=additional_warnings,
            ),
            "scenario_version": scenario_version,
            "parent_manifest_id": parent_manifest_id,
            "child_manifests": child_manifests,
            "data_hashes": data_hashes,
            "output_hashes": output_hashes,
        }


def _calculate_end_year(*, start_year: int, projection_years: int) -> int:
    """Calculate inclusive end year from start year and horizon length."""
    if projection_years < 1:
        raise ValueError(f"projection_years must be >= 1 (received {projection_years})")
    return start_year + projection_years - 1


def _step_pipeline_names(step_pipeline: tuple["PipelineStep", ...]) -> list[str]:
    """Return stable step names for logging and metadata."""
    return [_extract_step_name(step) for step in step_pipeline]


def _coerce_dict(value: Any) -> dict[str, Any]:
    """Normalize optional payloads to dictionaries."""
    if isinstance(value, dict):
        return value
    return {}


def _coerce_path_map(value: Any) -> dict[str, Path]:
    """Normalize optional key->path mappings from workflow requests."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("expected a mapping of artifact keys to path values")

    normalized: dict[str, Path] = {}
    for key, path_value in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("artifact path map keys must be non-empty strings")
        if isinstance(path_value, Path):
            normalized[key] = path_value
            continue
        if isinstance(path_value, str) and path_value.strip():
            normalized[key] = Path(path_value)
            continue
        raise ValueError(
            f"artifact path for key '{key}' must be a non-empty string or Path"
        )
    return normalized


def _resolve_scenario_identity(
    *,
    request: dict[str, Any],
    fallback_name: str,
    fallback_version: str,
) -> tuple[str, str]:
    """Resolve scenario name/version from request scenarios or explicit metadata."""
    scenario_meta = request.get("scenario_metadata")
    if isinstance(scenario_meta, dict):
        name = scenario_meta.get("name")
        version = scenario_meta.get("version")
        if isinstance(name, str) and isinstance(version, str):
            return name, version

    scenarios = request.get("scenarios")
    if isinstance(scenarios, list):
        for entry in scenarios:
            if not isinstance(entry, dict):
                continue
            reference = entry.get("reference")
            if not isinstance(reference, str) or not reference.strip():
                continue
            if "@" in reference:
                name, version = reference.rsplit("@", 1)
                return name.strip(), version.strip()
            return reference.strip(), ""

    return fallback_name, fallback_version


def _resolve_validation_flag(
    *, request: dict[str, Any], fallback: bool | None
) -> bool | None:
    """Resolve scenario/template validation flag from request metadata."""
    scenario_meta = request.get("scenario_metadata")
    if isinstance(scenario_meta, dict):
        validated = scenario_meta.get("validated")
        if isinstance(validated, bool):
            return validated
    validated = request.get("scenario_validated")
    if isinstance(validated, bool):
        return validated
    return fallback


def _resolve_additional_warnings(
    *, request: dict[str, Any], fallback: list[str]
) -> list[str]:
    """Resolve additional warning messages from request metadata."""
    request_warnings = request.get("additional_warnings")
    if isinstance(request_warnings, list):
        return [warning for warning in request_warnings if isinstance(warning, str)]
    return list(fallback)
