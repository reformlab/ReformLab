"""Shared fixtures for calibration subsystem tests — Story 15.1 / AC: all."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from reformlab.calibration.types import CalibrationTarget, CalibrationTargetSet

# ============================== Fixture directory ==============================

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "calibration"


# ============================== Target building helpers ==============================


def make_target(
    domain: str = "vehicle",
    period: int = 2022,
    from_state: str = "petrol",
    to_state: str = "buy_electric",
    observed_rate: float = 0.03,
    source_label: str = "test source",
) -> CalibrationTarget:
    """Build a CalibrationTarget with sensible defaults for tests."""
    return CalibrationTarget(
        domain=domain,
        period=period,
        from_state=from_state,
        to_state=to_state,
        observed_rate=observed_rate,
        source_label=source_label,
    )


def make_vehicle_set() -> CalibrationTargetSet:
    """Build a valid single-domain CalibrationTargetSet for vehicle domain."""
    return CalibrationTargetSet(
        targets=(
            make_target(to_state="buy_electric", observed_rate=0.03),
            make_target(to_state="keep_current", observed_rate=0.85),
            make_target(to_state="buy_hybrid", observed_rate=0.05),
            make_target(to_state="buy_diesel", observed_rate=0.02),
        )
    )


def make_multi_domain_set() -> CalibrationTargetSet:
    """Build a valid multi-domain CalibrationTargetSet."""
    return CalibrationTargetSet(
        targets=(
            make_target(domain="vehicle", to_state="buy_electric", observed_rate=0.03),
            make_target(domain="vehicle", to_state="keep_current", observed_rate=0.85),
            make_target(
                domain="heating",
                from_state="gas",
                to_state="heat_pump",
                observed_rate=0.05,
                source_label="ADEME 2022",
            ),
            make_target(
                domain="heating",
                from_state="gas",
                to_state="keep_current",
                observed_rate=0.90,
                source_label="ADEME 2022",
            ),
        )
    )


# ============================== File fixtures ==============================


@pytest.fixture()
def fixture_dir() -> Path:
    """Return the calibration fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture()
def valid_vehicle_csv(fixture_dir: Path) -> Path:
    """Path to the valid vehicle targets CSV fixture."""
    return fixture_dir / "valid_vehicle_targets.csv"


@pytest.fixture()
def valid_heating_csv(fixture_dir: Path) -> Path:
    """Path to the valid heating targets CSV fixture."""
    return fixture_dir / "valid_heating_targets.csv"


@pytest.fixture()
def valid_multi_domain_yaml(fixture_dir: Path) -> Path:
    """Path to the valid multi-domain YAML fixture."""
    return fixture_dir / "valid_multi_domain_targets.yaml"


@pytest.fixture()
def invalid_missing_field_csv(fixture_dir: Path) -> Path:
    """Path to the CSV fixture with a missing required column."""
    return fixture_dir / "invalid_missing_field.csv"


@pytest.fixture()
def invalid_rate_sum_yaml(fixture_dir: Path) -> Path:
    """Path to the YAML fixture with rates summing > 1.0."""
    return fixture_dir / "invalid_rate_sum.yaml"


@pytest.fixture()
def valid_vehicle_parquet(tmp_path: Path) -> Path:
    """Create a valid vehicle targets Parquet file in tmp_path."""
    table = pa.table(
        {
            "domain": pa.array(["vehicle", "vehicle", "vehicle", "vehicle"], pa.utf8()),
            "period": pa.array([2022, 2022, 2022, 2022], pa.int64()),
            "from_state": pa.array(["petrol", "petrol", "petrol", "petrol"], pa.utf8()),
            "to_state": pa.array(
                ["buy_electric", "keep_current", "buy_hybrid", "buy_diesel"], pa.utf8()
            ),
            "observed_rate": pa.array([0.03, 0.85, 0.05, 0.02], pa.float64()),
            "source_label": pa.array(
                ["SDES 2022", "SDES 2022", "SDES 2022", "SDES 2022"], pa.utf8()
            ),
        }
    )
    path = tmp_path / "valid_vehicle_targets.parquet"
    pq.write_table(table, path)
    return path


@pytest.fixture()
def malformed_rate_csv(tmp_path: Path) -> Path:
    """Create a CSV with a non-numeric value in the observed_rate column."""
    content = (
        "domain,period,from_state,to_state,observed_rate,source_label\n"
        "vehicle,2022,petrol,buy_electric,not_a_number,SDES 2022\n"
    )
    path = tmp_path / "malformed_rate.csv"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def duplicate_rows_csv(tmp_path: Path) -> Path:
    """Create a CSV with a duplicate (domain, period, from_state, to_state) row."""
    content = (
        "domain,period,from_state,to_state,observed_rate,source_label\n"
        "vehicle,2022,petrol,buy_electric,0.03,SDES 2022\n"
        "vehicle,2022,petrol,buy_electric,0.05,SDES 2022\n"
    )
    path = tmp_path / "duplicate_rows.csv"
    path.write_text(content, encoding="utf-8")
    return path
