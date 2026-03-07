"""Tests for panel decision column injection.

Story 14-6: Extend Panel Output and Manifests with Decision Records.
AC-3: Panel decision columns.
AC-4: Parquet export with list columns.
AC-6: Panel schema consistency across years.
AC-7: Edge cases (backward compatibility, single/two domains, empty population).
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from reformlab.computation.types import ComputationResult
from reformlab.discrete_choice.decision_record import (
    DECISION_LOG_KEY,
    DecisionRecord,
)
from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.orchestrator.computation_step import COMPUTATION_RESULT_KEY
from reformlab.orchestrator.panel import PanelOutput
from reformlab.orchestrator.types import OrchestratorResult, YearState

# ============================================================================
# Test helpers
# ============================================================================


def _make_computation_result(
    n: int,
    year: int = 2025,
) -> ComputationResult:
    """Create a minimal ComputationResult with n households."""
    return ComputationResult(
        output_fields=pa.table({
            "household_id": pa.array(range(n), type=pa.int64()),
            "income": pa.array([50000.0 + i * 1000 for i in range(n)]),
        }),
        adapter_version="test-1.0.0",
        period=year,
    )


def _make_decision_record(
    domain_name: str,
    n: int,
    alt_ids: tuple[str, ...] = ("ev", "ice", "keep"),
    seed: int = 42,
    beta_cost: float = -0.01,
) -> DecisionRecord:
    """Build a DecisionRecord for testing panel columns."""
    m = len(alt_ids)
    uniform_prob = 1.0 / m
    return DecisionRecord(
        domain_name=domain_name,
        chosen=pa.array([alt_ids[0]] * n, type=pa.string()),
        probabilities=pa.table({aid: [uniform_prob] * n for aid in alt_ids}),
        utilities=pa.table(
            {aid: [float(-idx - 1)] * n for idx, aid in enumerate(alt_ids)}
        ),
        alternative_ids=alt_ids,
        seed=seed,
        taste_parameters={"beta_cost": beta_cost},
        eligibility_summary=None,
    )


def _make_result_with_decisions(
    years: list[int],
    n: int = 3,
    records_per_year: list[DecisionRecord] | None = None,
    include_decisions_for_years: list[int] | None = None,
) -> OrchestratorResult:
    """Build OrchestratorResult with decision records in yearly states."""
    yearly_states: dict[int, YearState] = {}

    for year in years:
        comp_result = _make_computation_result(n, year)
        data: dict[str, object] = {COMPUTATION_RESULT_KEY: comp_result}

        # Add decision records for specified years (or all years)
        should_add = (
            include_decisions_for_years is None
            or year in include_decisions_for_years
        )
        if should_add and records_per_year is not None:
            data[DECISION_LOG_KEY] = tuple(records_per_year)

        yearly_states[year] = YearState(
            year=year, data=data, seed=42 + year, metadata={}
        )

    return OrchestratorResult(
        success=True,
        yearly_states=yearly_states,
        errors=[],
        metadata={
            "start_year": min(years),
            "end_year": max(years),
            "seed": 42,
            "step_pipeline": ["computation"],
        },
    )


# ============================================================================
# TestPanelWithDecisionRecords — AC-3, AC-7
# ============================================================================


class TestPanelWithDecisionRecords:
    """AC-3: Panel decision columns from decision log."""

    def test_single_domain_adds_domain_prefixed_columns(self) -> None:
        """Single domain produces {domain}_chosen, _probabilities, _utilities."""
        record = _make_decision_record("vehicle", n=3)
        result = _make_result_with_decisions(
            [2025], n=3, records_per_year=[record]
        )

        panel = PanelOutput.from_orchestrator_result(result)

        assert "vehicle_chosen" in panel.table.column_names
        assert "vehicle_probabilities" in panel.table.column_names
        assert "vehicle_utilities" in panel.table.column_names
        assert "decision_domains" in panel.table.column_names

    def test_two_domains_add_two_sets_of_columns(self) -> None:
        """Two domains produce two sets of domain-prefixed columns."""
        vehicle_rec = _make_decision_record("vehicle", n=3, alt_ids=("ev", "ice"))
        heating_rec = _make_decision_record("heating", n=3, alt_ids=("hp", "gas"))
        result = _make_result_with_decisions(
            [2025], n=3, records_per_year=[vehicle_rec, heating_rec]
        )

        panel = PanelOutput.from_orchestrator_result(result)

        for domain in ("vehicle", "heating"):
            assert f"{domain}_chosen" in panel.table.column_names
            assert f"{domain}_probabilities" in panel.table.column_names
            assert f"{domain}_utilities" in panel.table.column_names

    def test_decision_domains_list_column(self) -> None:
        """decision_domains column lists all domain names for that year."""
        vehicle_rec = _make_decision_record("vehicle", n=3)
        heating_rec = _make_decision_record("heating", n=3, alt_ids=("hp", "gas"))
        result = _make_result_with_decisions(
            [2025], n=3, records_per_year=[vehicle_rec, heating_rec]
        )

        panel = PanelOutput.from_orchestrator_result(result)

        domains_col = panel.table.column("decision_domains")
        for row in domains_col.to_pylist():
            assert row == ["vehicle", "heating"]

    def test_probabilities_are_list_float64(self) -> None:
        """Probabilities column has type list<float64>."""
        record = _make_decision_record("vehicle", n=3)
        result = _make_result_with_decisions(
            [2025], n=3, records_per_year=[record]
        )

        panel = PanelOutput.from_orchestrator_result(result)

        prob_field = panel.table.schema.field("vehicle_probabilities")
        assert pa.types.is_list(prob_field.type)
        assert pa.types.is_float64(prob_field.type.value_type)

    def test_utilities_are_list_float64(self) -> None:
        """Utilities column has type list<float64>."""
        record = _make_decision_record("vehicle", n=3)
        result = _make_result_with_decisions(
            [2025], n=3, records_per_year=[record]
        )

        panel = PanelOutput.from_orchestrator_result(result)

        util_field = panel.table.schema.field("vehicle_utilities")
        assert pa.types.is_list(util_field.type)
        assert pa.types.is_float64(util_field.type.value_type)

    def test_panel_metadata_includes_decision_domain_alternatives(self) -> None:
        """Panel metadata includes decision_domain_alternatives mapping."""
        record = _make_decision_record("vehicle", n=3, alt_ids=("ev", "ice", "keep"))
        result = _make_result_with_decisions(
            [2025], n=3, records_per_year=[record]
        )

        panel = PanelOutput.from_orchestrator_result(result)

        assert "decision_domain_alternatives" in panel.metadata
        alts = panel.metadata["decision_domain_alternatives"]
        assert alts == {"vehicle": ["ev", "ice", "keep"]}

    def test_backward_compatibility_no_decision_log(self) -> None:
        """AC-7: No decision log → panel identical to pre-14.6 output."""
        result = _make_result_with_decisions([2025, 2026], n=3)

        panel = PanelOutput.from_orchestrator_result(result)

        # No decision columns
        for col_name in panel.table.column_names:
            assert not col_name.endswith("_chosen")
            assert not col_name.endswith("_probabilities")
            assert not col_name.endswith("_utilities")
        assert "decision_domains" not in panel.table.column_names

    def test_empty_population_decision_columns(self) -> None:
        """AC-7: Empty population (N=0) produces empty decision columns."""
        record = _make_decision_record("vehicle", n=0)
        result = _make_result_with_decisions(
            [2025], n=0, records_per_year=[record]
        )

        panel = PanelOutput.from_orchestrator_result(result)

        assert panel.table.num_rows == 0
        assert "vehicle_chosen" in panel.table.column_names

    def test_chosen_column_values(self) -> None:
        """Golden value test: chosen column contains correct alternative IDs."""
        record = DecisionRecord(
            domain_name="vehicle",
            chosen=pa.array(["ev", "ice", "keep"], type=pa.string()),
            probabilities=pa.table({
                "ev": [0.5, 0.3, 0.2],
                "ice": [0.3, 0.5, 0.3],
                "keep": [0.2, 0.2, 0.5],
            }),
            utilities=pa.table({
                "ev": [-1.0, -2.0, -3.0],
                "ice": [-1.5, -0.5, -2.0],
                "keep": [-2.0, -1.0, -0.5],
            }),
            alternative_ids=("ev", "ice", "keep"),
            seed=42,
            taste_parameters={"beta_cost": -0.01},
            eligibility_summary=None,
        )
        result = _make_result_with_decisions(
            [2025], n=3, records_per_year=[record]
        )

        panel = PanelOutput.from_orchestrator_result(result)

        assert panel.table.column("vehicle_chosen").to_pylist() == [
            "ev", "ice", "keep"
        ]
        # Verify probability list ordering matches alternative_ids
        probs = panel.table.column("vehicle_probabilities").to_pylist()
        assert probs[0] == [0.5, 0.3, 0.2]  # ev, ice, keep for household 0
        assert probs[1] == [0.3, 0.5, 0.2]  # ev, ice, keep for household 1

    def test_duplicate_domain_name_raises_error(self) -> None:
        """AC-7: Duplicate domain names in log raises DiscreteChoiceError."""
        rec1 = _make_decision_record("vehicle", n=3)
        rec2 = _make_decision_record("vehicle", n=3)
        result = _make_result_with_decisions(
            [2025], n=3, records_per_year=[rec1, rec2]
        )

        with pytest.raises(DiscreteChoiceError, match="Duplicate"):
            PanelOutput.from_orchestrator_result(result)


# ============================================================================
# TestPanelDecisionParquet — AC-4
# ============================================================================


class TestPanelDecisionParquet:
    """AC-4: Parquet export with list columns."""

    def test_parquet_roundtrip_list_columns(self, tmp_path: Path) -> None:
        """List columns survive Parquet roundtrip with correct types."""
        record = _make_decision_record("vehicle", n=3)
        result = _make_result_with_decisions(
            [2025], n=3, records_per_year=[record]
        )

        panel = PanelOutput.from_orchestrator_result(result)
        parquet_path = tmp_path / "panel_decision.parquet"
        panel.to_parquet(parquet_path)

        imported = pq.read_table(parquet_path)

        # Verify list column types preserved
        prob_field = imported.schema.field("vehicle_probabilities")
        assert pa.types.is_list(prob_field.type)
        assert pa.types.is_float64(prob_field.type.value_type)

        util_field = imported.schema.field("vehicle_utilities")
        assert pa.types.is_list(util_field.type)
        assert pa.types.is_float64(util_field.type.value_type)

        # Verify domain column names
        assert "vehicle_chosen" in imported.column_names
        assert "vehicle_probabilities" in imported.column_names
        assert "vehicle_utilities" in imported.column_names

    def test_parquet_roundtrip_values(self, tmp_path: Path) -> None:
        """Parquet roundtrip preserves list column values."""
        record = _make_decision_record("vehicle", n=2, alt_ids=("ev", "ice"))
        result = _make_result_with_decisions(
            [2025], n=2, records_per_year=[record]
        )

        panel = PanelOutput.from_orchestrator_result(result)
        parquet_path = tmp_path / "panel.parquet"
        panel.to_parquet(parquet_path)

        imported = pq.read_table(parquet_path)

        orig_probs = panel.table.column("vehicle_probabilities").to_pylist()
        imported_probs = imported.column("vehicle_probabilities").to_pylist()
        assert orig_probs == imported_probs


# ============================================================================
# TestPanelDecisionCSV — AC-4
# ============================================================================


class TestPanelDecisionCSV:
    """AC-4: CSV export with decision columns."""

    def test_csv_export_valid(self, tmp_path: Path) -> None:
        """CSV export with list columns produces a valid file."""
        record = _make_decision_record("vehicle", n=3)
        result = _make_result_with_decisions(
            [2025], n=3, records_per_year=[record]
        )

        panel = PanelOutput.from_orchestrator_result(result)
        csv_path = tmp_path / "panel_decision.csv"
        panel.to_csv(csv_path)

        assert csv_path.exists()
        content = csv_path.read_text()
        assert "vehicle_chosen" in content


# ============================================================================
# TestPanelDecisionSchemaConsistency — AC-6
# ============================================================================


class TestPanelDecisionSchemaConsistency:
    """AC-6: Schema consistency across years."""

    def test_multi_year_same_domains_concat_succeeds(self) -> None:
        """Same decision domains across years → concat succeeds."""
        record = _make_decision_record("vehicle", n=3)
        result = _make_result_with_decisions(
            [2025, 2026], n=3, records_per_year=[record]
        )

        panel = PanelOutput.from_orchestrator_result(result)

        assert panel.table.num_rows == 6  # 3 households × 2 years
        assert "vehicle_chosen" in panel.table.column_names

    def test_partial_decisions_concat_with_promote(self) -> None:
        """AC-6: Partial decisions (Year 1 has, Year 2 doesn't) → concat succeeds."""
        record = _make_decision_record("vehicle", n=3)
        result = _make_result_with_decisions(
            [2025, 2026],
            n=3,
            records_per_year=[record],
            include_decisions_for_years=[2025],
        )

        panel = PanelOutput.from_orchestrator_result(result)

        assert panel.table.num_rows == 6
        # Year 2025 has decision columns, Year 2026 doesn't
        # promote_options="permissive" fills with nulls
        chosen_col = panel.table.column("vehicle_chosen").to_pylist()
        # First 3 rows (2025) have values, next 3 (2026) are null
        assert all(v is not None for v in chosen_col[:3])
        assert all(v is None for v in chosen_col[3:])
