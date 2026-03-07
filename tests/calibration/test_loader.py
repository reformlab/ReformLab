"""Tests for load_calibration_targets() — Story 15.1 / AC-2, AC-3, AC-4."""

from __future__ import annotations

from pathlib import Path

import pytest

from reformlab.calibration.errors import (
    CalibrationTargetLoadError,
    CalibrationTargetValidationError,
)
from reformlab.calibration.loader import load_calibration_targets


class TestCSVLoading:
    """AC-2, AC-4: CSV loading with validation and error reporting."""

    def test_valid_csv_loads_correctly(self, valid_vehicle_csv: Path) -> None:
        """Given a valid vehicle CSV, when loaded, then returns correct CalibrationTargetSet."""
        target_set = load_calibration_targets(valid_vehicle_csv)

        assert len(target_set.targets) == 6
        domains = {t.domain for t in target_set.targets}
        assert domains == {"vehicle"}

    def test_valid_csv_target_fields_are_correct(self, valid_vehicle_csv: Path) -> None:
        """Given a valid CSV, when loaded, then target fields match CSV values."""
        target_set = load_calibration_targets(valid_vehicle_csv)
        first = target_set.targets[0]

        assert first.domain == "vehicle"
        assert first.period == 2022
        assert first.from_state == "petrol"
        assert first.to_state == "buy_electric"
        assert first.observed_rate == pytest.approx(0.03)
        assert first.source_label == "SDES vehicle fleet 2022"

    def test_valid_heating_csv_loads(self, valid_heating_csv: Path) -> None:
        """Given a valid heating CSV, when loaded, then returns heating targets."""
        target_set = load_calibration_targets(valid_heating_csv)

        assert len(target_set.targets) == 5
        assert all(t.domain == "heating" for t in target_set.targets)

    def test_missing_column_raises_with_column_name(
        self, invalid_missing_field_csv: Path
    ) -> None:
        """Given CSV missing source_label column, when loaded, then raises with column name in message.

        AC-4: Error identifies the field name.
        """
        with pytest.raises(CalibrationTargetLoadError, match="source_label"):
            load_calibration_targets(invalid_missing_field_csv)

    def test_missing_column_raises_load_error(
        self, invalid_missing_field_csv: Path
    ) -> None:
        """Given CSV missing a required column, when loaded, then raises CalibrationTargetLoadError."""
        with pytest.raises(CalibrationTargetLoadError):
            load_calibration_targets(invalid_missing_field_csv)

    def test_malformed_rate_raises_with_row_location(
        self, malformed_rate_csv: Path
    ) -> None:
        """Given CSV with non-numeric observed_rate, when loaded, then raises with row=N in message.

        AC-4: Error identifies record location.
        """
        with pytest.raises(CalibrationTargetLoadError, match=r"row"):
            load_calibration_targets(malformed_rate_csv)

    def test_duplicate_rows_raise_load_error(self, duplicate_rows_csv: Path) -> None:
        """Given CSV with duplicate (domain, period, from_state, to_state), when loaded, then raises."""
        with pytest.raises(CalibrationTargetLoadError, match="duplicate"):
            load_calibration_targets(duplicate_rows_csv)

    def test_rate_sum_violation_raises_validation_error(self, tmp_path: Path) -> None:
        """Given CSV where rates sum > 1.0 for a group, when loaded, then raises validation error."""
        content = (
            "domain,period,from_state,to_state,observed_rate,source_label\n"
            "vehicle,2022,petrol,buy_electric,0.70,test\n"
            "vehicle,2022,petrol,keep_current,0.50,test\n"
        )
        path = tmp_path / "rate_sum_violation.csv"
        path.write_text(content, encoding="utf-8")

        with pytest.raises(CalibrationTargetValidationError):
            load_calibration_targets(path)


class TestParquetLoading:
    """AC-2, AC-3: Parquet loading."""

    def test_valid_parquet_loads_correctly(self, valid_vehicle_parquet: Path) -> None:
        """Given a valid vehicle Parquet file, when loaded, then returns correct CalibrationTargetSet."""
        target_set = load_calibration_targets(valid_vehicle_parquet)

        assert len(target_set.targets) == 4
        assert all(t.domain == "vehicle" for t in target_set.targets)

    def test_parquet_target_fields_match(self, valid_vehicle_parquet: Path) -> None:
        """Given a valid Parquet file, when loaded, then field values are correct."""
        target_set = load_calibration_targets(valid_vehicle_parquet)
        first = target_set.targets[0]

        assert first.domain == "vehicle"
        assert first.period == 2022
        assert first.from_state == "petrol"
        assert first.to_state == "buy_electric"
        assert first.observed_rate == pytest.approx(0.03)

    def test_parquet_source_metadata_defaults_to_empty(
        self, valid_vehicle_parquet: Path
    ) -> None:
        """Given a Parquet file (no source_metadata column), when loaded, then source_metadata={}."""
        target_set = load_calibration_targets(valid_vehicle_parquet)
        for target in target_set.targets:
            assert target.source_metadata == {}

    def test_parquet_consistency_validated(self, tmp_path: Path) -> None:
        """Given a Parquet file with rate sum violation, when loaded, then raises validation error."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        table = pa.table(
            {
                "domain": pa.array(["vehicle", "vehicle"], pa.utf8()),
                "period": pa.array([2022, 2022], pa.int64()),
                "from_state": pa.array(["petrol", "petrol"], pa.utf8()),
                "to_state": pa.array(["buy_electric", "keep_current"], pa.utf8()),
                "observed_rate": pa.array([0.70, 0.50], pa.float64()),
                "source_label": pa.array(["test", "test"], pa.utf8()),
            }
        )
        path = tmp_path / "rate_violation.parquet"
        pq.write_table(table, path)

        with pytest.raises(CalibrationTargetValidationError):
            load_calibration_targets(path)


class TestYAMLLoading:
    """AC-2, AC-4: YAML loading with JSON Schema validation."""

    def test_valid_yaml_loads_correctly(self, valid_multi_domain_yaml: Path) -> None:
        """Given a valid multi-domain YAML, when loaded, then returns correct CalibrationTargetSet."""
        target_set = load_calibration_targets(valid_multi_domain_yaml)

        domains = {t.domain for t in target_set.targets}
        assert "vehicle" in domains
        assert "heating" in domains

    def test_yaml_preserves_source_metadata(
        self, valid_multi_domain_yaml: Path
    ) -> None:
        """Given YAML with source_metadata, when loaded, then metadata preserved on target."""
        target_set = load_calibration_targets(valid_multi_domain_yaml)

        # First vehicle target has source_metadata in the fixture
        vehicle_targets = [t for t in target_set.targets if t.domain == "vehicle"]
        first_vehicle = vehicle_targets[0]
        assert first_vehicle.source_metadata == {"dataset": "parc-automobile-2022", "year": "2022"}

    def test_yaml_target_without_metadata_defaults_to_empty(
        self, valid_multi_domain_yaml: Path
    ) -> None:
        """Given YAML target without source_metadata, when loaded, then source_metadata={}."""
        target_set = load_calibration_targets(valid_multi_domain_yaml)
        # Second vehicle target in fixture has no source_metadata
        vehicle_targets = [t for t in target_set.targets if t.domain == "vehicle"]
        second_vehicle = vehicle_targets[1]
        assert second_vehicle.source_metadata == {}

    def test_yaml_rate_sum_violation_raises(
        self, invalid_rate_sum_yaml: Path
    ) -> None:
        """Given YAML with rates summing > 1.0, when loaded, then raises CalibrationTargetValidationError."""
        with pytest.raises(CalibrationTargetValidationError):
            load_calibration_targets(invalid_rate_sum_yaml)

    def test_yaml_schema_catches_missing_required_field(self, tmp_path: Path) -> None:
        """Given YAML target missing source_label, when loaded, then raises with targets[N].field in message.

        AC-4: Error message identifies record location as targets[N].field_name.
        """
        content = (
            "targets:\n"
            "  - domain: vehicle\n"
            "    period: 2022\n"
            "    from_state: petrol\n"
            "    to_state: buy_electric\n"
            "    observed_rate: 0.03\n"
            # source_label intentionally missing
        )
        path = tmp_path / "missing_source_label.yaml"
        path.write_text(content, encoding="utf-8")

        with pytest.raises(CalibrationTargetLoadError, match=r"targets\[0\]"):
            load_calibration_targets(path)

    def test_yaml_schema_catches_invalid_rate_type(self, tmp_path: Path) -> None:
        """Given YAML target with non-numeric observed_rate, when loaded, then raises with field location."""
        content = (
            "targets:\n"
            "  - domain: vehicle\n"
            "    period: 2022\n"
            "    from_state: petrol\n"
            "    to_state: buy_electric\n"
            "    observed_rate: not_a_number\n"
            "    source_label: test\n"
        )
        path = tmp_path / "invalid_rate_type.yaml"
        path.write_text(content, encoding="utf-8")

        with pytest.raises(CalibrationTargetLoadError, match=r"targets\[0\]"):
            load_calibration_targets(path)

    def test_yaml_schema_catches_rate_above_one(self, tmp_path: Path) -> None:
        """Given YAML target with observed_rate > 1.0, when loaded, then JSON Schema catches it."""
        content = (
            "targets:\n"
            "  - domain: vehicle\n"
            "    period: 2022\n"
            "    from_state: petrol\n"
            "    to_state: buy_electric\n"
            "    observed_rate: 1.5\n"
            "    source_label: test\n"
        )
        path = tmp_path / "rate_above_one.yaml"
        path.write_text(content, encoding="utf-8")

        with pytest.raises(CalibrationTargetLoadError):
            load_calibration_targets(path)

    def test_yaml_round_trip_stability(self, tmp_path: Path) -> None:
        """Given a valid YAML, when loaded twice, then returns identical results."""
        import yaml as yaml_lib

        content = {
            "targets": [
                {
                    "domain": "vehicle",
                    "period": 2022,
                    "from_state": "petrol",
                    "to_state": "buy_electric",
                    "observed_rate": 0.03,
                    "source_label": "SDES 2022",
                }
            ]
        }
        path = tmp_path / "round_trip.yaml"
        path.write_text(yaml_lib.dump(content), encoding="utf-8")

        set_a = load_calibration_targets(path)
        set_b = load_calibration_targets(path)

        assert len(set_a.targets) == len(set_b.targets)
        for ta, tb in zip(set_a.targets, set_b.targets):
            assert ta == tb

    def test_schema_loaded_via_importlib_resources(self, tmp_path: Path) -> None:
        """Given importlib.resources path, when schema loaded, then validator is returned.

        Verifies no path hardcoding — schema file locatable from installed package.
        """
        from reformlab.calibration.loader import _get_schema_validator

        # This call should succeed (schema loadable from package)
        validator = _get_schema_validator()
        # The validator should be a Draft202012Validator-compatible object
        assert hasattr(validator, "iter_errors")


class TestFormatDispatch:
    """AC-2: Format dispatch by file extension."""

    def test_csv_extension_dispatches_to_csv_path(
        self, valid_vehicle_csv: Path
    ) -> None:
        """Given a .csv file, when loaded, then CSV loader is used."""
        target_set = load_calibration_targets(valid_vehicle_csv)
        assert len(target_set.targets) > 0

    def test_yaml_extension_dispatches_to_yaml_path(
        self, valid_multi_domain_yaml: Path
    ) -> None:
        """Given a .yaml file, when loaded, then YAML loader is used."""
        target_set = load_calibration_targets(valid_multi_domain_yaml)
        assert len(target_set.targets) > 0

    def test_yml_extension_dispatches_to_yaml_path(self, tmp_path: Path) -> None:
        """Given a .yml file, when loaded, then YAML loader is used."""
        content = (
            "targets:\n"
            "  - domain: vehicle\n"
            "    period: 2022\n"
            "    from_state: petrol\n"
            "    to_state: buy_electric\n"
            "    observed_rate: 0.03\n"
            "    source_label: test\n"
        )
        path = tmp_path / "targets.yml"
        path.write_text(content, encoding="utf-8")

        target_set = load_calibration_targets(path)
        assert len(target_set.targets) == 1

    def test_parquet_extension_dispatches_to_ingest_path(
        self, valid_vehicle_parquet: Path
    ) -> None:
        """Given a .parquet file, when loaded, then Parquet/ingest loader is used."""
        target_set = load_calibration_targets(valid_vehicle_parquet)
        assert len(target_set.targets) > 0

    def test_csv_gz_extension_dispatches_to_csv_path(self, tmp_path: Path) -> None:
        """Given a .csv.gz file, when loaded, then CSV/ingest loader is used."""
        import gzip

        content = (
            b"domain,period,from_state,to_state,observed_rate,source_label\n"
            b"vehicle,2022,petrol,buy_electric,0.03,SDES 2022\n"
        )
        path = tmp_path / "targets.csv.gz"
        with gzip.open(path, "wb") as f:
            f.write(content)

        target_set = load_calibration_targets(path)
        assert len(target_set.targets) == 1

    def test_unknown_extension_raises_load_error(self, tmp_path: Path) -> None:
        """Given a .json file (unsupported), when loaded, then raises CalibrationTargetLoadError."""
        path = tmp_path / "targets.json"
        path.write_text("{}", encoding="utf-8")

        with pytest.raises(CalibrationTargetLoadError, match="unsupported"):
            load_calibration_targets(path)

    def test_error_message_contains_file_path(
        self, invalid_missing_field_csv: Path
    ) -> None:
        """Given an error during loading, when raised, then CalibrationTargetLoadError includes file path.

        AC-4: Error message includes source file path.
        """
        with pytest.raises(CalibrationTargetLoadError, match="file="):
            load_calibration_targets(invalid_missing_field_csv)
