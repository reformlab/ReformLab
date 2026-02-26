from __future__ import annotations

import textwrap
from pathlib import Path

import pyarrow as pa
import pytest

import reformlab.computation.mapping as mapping_module
from reformlab.computation.mapping import (
    FieldMapping,
    MappingConfig,
    MappingError,
    MappingValidationResult,
    apply_input_mapping,
    apply_output_mapping,
    load_mapping,
    load_mappings,
    merge_mappings,
    validate_mapping,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_yaml(tmp_path: Path) -> Path:
    """A valid YAML mapping file."""
    content = textwrap.dedent("""\
        version: "1"
        description: "Test mapping"

        mappings:
          - openfisca_name: "impot_revenu_net"
            project_name: "income_tax"
            direction: "output"
            type: "float64"
            description: "Net income tax"

          - openfisca_name: "menage_id"
            project_name: "household_id"
            direction: "both"
            type: "int64"
            description: "Household identifier"
    """)
    p = tmp_path / "mapping.yaml"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def extension_yaml(tmp_path: Path) -> Path:
    """An extension YAML mapping file that overrides one entry."""
    content = textwrap.dedent("""\
        version: "1"
        description: "Extension mapping"

        mappings:
          - openfisca_name: "impot_revenu_net"
            project_name: "net_income_tax"
            direction: "output"
            type: "float64"
            description: "Override: renamed income tax"

          - openfisca_name: "taxe_carbone"
            project_name: "carbon_tax"
            direction: "output"
            type: "float64"
    """)
    p = tmp_path / "extension.yaml"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def output_table() -> pa.Table:
    """A PyArrow table simulating OpenFisca output columns."""
    return pa.table(
        {
            "impot_revenu_net": [100.0, 200.0],
            "menage_id": [1, 2],
            "extra_col": ["a", "b"],
        }
    )


@pytest.fixture()
def project_table() -> pa.Table:
    """A PyArrow table using project-schema names."""
    return pa.table(
        {
            "income_tax": [100.0, 200.0],
            "household_id": [1, 2],
            "extra_col": ["a", "b"],
        }
    )


# ---------------------------------------------------------------------------
# Task 1 tests: Data types
# ---------------------------------------------------------------------------


class TestFieldMapping:
    """Tests for the FieldMapping frozen dataclass."""

    def test_create_field_mapping(self) -> None:
        """Given valid args, when created, then all fields set."""
        fm = FieldMapping(
            openfisca_name="impot_revenu_net",
            project_name="income_tax",
            direction="output",
            pa_type=pa.float64(),
            description="Net income tax",
        )
        assert fm.openfisca_name == "impot_revenu_net"
        assert fm.project_name == "income_tax"
        assert fm.direction == "output"
        assert fm.pa_type == pa.float64()
        assert fm.description == "Net income tax"

    def test_field_mapping_is_frozen(self) -> None:
        """Given a FieldMapping, when modifying, then raises."""
        fm = FieldMapping(
            openfisca_name="x",
            project_name="y",
            direction="both",
            pa_type=pa.utf8(),
        )
        with pytest.raises(AttributeError):
            fm.openfisca_name = "z"  # type: ignore[misc]

    def test_default_description(self) -> None:
        """Given no description, then defaults to empty."""
        fm = FieldMapping(
            openfisca_name="x",
            project_name="y",
            direction="input",
            pa_type=pa.int64(),
        )
        assert fm.description == ""


class TestMappingConfig:
    """Tests for the MappingConfig frozen dataclass."""

    def test_lookup_by_openfisca_name(self) -> None:
        """Lookup by openfisca_name returns correct mapping."""
        fm = FieldMapping("a", "b", "output", pa.float64())
        config = MappingConfig(mappings=(fm,))
        assert config.by_openfisca_name("a") is fm
        assert config.by_openfisca_name("nonexistent") is None

    def test_lookup_by_project_name(self) -> None:
        """Lookup by project_name returns correct mapping."""
        fm = FieldMapping("a", "b", "input", pa.float64())
        config = MappingConfig(mappings=(fm,))
        assert config.by_project_name("b") is fm
        assert config.by_project_name("nonexistent") is None

    def test_input_mappings(self) -> None:
        """input_mappings returns only input+both direction."""
        fm_in = FieldMapping("a", "b", "input", pa.int64())
        fm_out = FieldMapping("c", "d", "output", pa.int64())
        fm_both = FieldMapping("e", "f", "both", pa.int64())
        config = MappingConfig(mappings=(fm_in, fm_out, fm_both))
        result = config.input_mappings
        assert fm_in in result
        assert fm_both in result
        assert fm_out not in result

    def test_output_mappings(self) -> None:
        """output_mappings returns only output+both direction."""
        fm_in = FieldMapping("a", "b", "input", pa.int64())
        fm_out = FieldMapping("c", "d", "output", pa.int64())
        fm_both = FieldMapping("e", "f", "both", pa.int64())
        config = MappingConfig(mappings=(fm_in, fm_out, fm_both))
        result = config.output_mappings
        assert fm_out in result
        assert fm_both in result
        assert fm_in not in result


class TestMappingError:
    """Tests for the MappingError exception."""

    def test_mapping_error_attributes(self) -> None:
        """Structured fields are accessible on MappingError."""
        err = MappingError(
            file_path=Path("test.yaml"),
            summary="Mapping load failed",
            reason="missing version key",
            fix="Add 'version' to top-level keys",
            invalid_fields=("version",),
        )
        assert err.file_path == Path("test.yaml")
        assert "Mapping load failed" in str(err)
        assert "missing version key" in str(err)
        assert err.invalid_fields == ("version",)

    def test_mapping_error_message_format(self) -> None:
        """Message follows standard format."""
        err = MappingError(
            file_path=Path("bad.yaml"),
            summary="Schema error",
            reason="invalid type",
            fix="Use valid type strings",
        )
        msg = str(err)
        assert "Schema error" in msg
        assert "invalid type" in msg
        assert "Use valid type strings" in msg
        assert "bad.yaml" in msg


class TestMappingValidationResult:
    """Tests for the MappingValidationResult frozen dataclass."""

    def test_validation_result_fields(self) -> None:
        """Warnings and errors are accessible."""
        result = MappingValidationResult(
            warnings=("warn1",),
            errors=("err1", "err2"),
        )
        assert len(result.warnings) == 1
        assert len(result.errors) == 2

    def test_empty_validation_result(self) -> None:
        """No issues produces empty tuples."""
        result = MappingValidationResult(warnings=(), errors=())
        assert result.warnings == ()
        assert result.errors == ()


# ---------------------------------------------------------------------------
# Task 2 tests: YAML loader
# ---------------------------------------------------------------------------


class TestLoadMapping:
    """Tests for load_mapping YAML loader."""

    def test_load_valid_mapping(self, sample_yaml: Path) -> None:
        """Valid YAML loads into MappingConfig with correct fields."""
        config = load_mapping(sample_yaml)
        assert len(config.mappings) == 2
        assert config.source_path == sample_yaml.resolve()
        fm = config.by_openfisca_name("impot_revenu_net")
        assert fm is not None
        assert fm.project_name == "income_tax"
        assert fm.direction == "output"
        assert fm.pa_type == pa.float64()

    def test_load_mapping_default_type(self, tmp_path: Path) -> None:
        """Mapping without type defaults to pa.utf8()."""
        content = textwrap.dedent("""\
            version: "1"
            mappings:
              - openfisca_name: "x"
                project_name: "y"
                direction: "output"
        """)
        p = tmp_path / "m.yaml"
        p.write_text(content, encoding="utf-8")
        config = load_mapping(p)
        assert config.mappings[0].pa_type == pa.utf8()

    def test_load_missing_version_key(self, tmp_path: Path) -> None:
        """Missing 'version' raises MappingError."""
        content = textwrap.dedent("""\
            mappings:
              - openfisca_name: "x"
                project_name: "y"
                direction: "output"
        """)
        p = tmp_path / "bad.yaml"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(MappingError) as exc_info:
            load_mapping(p)
        assert "version" in str(exc_info.value)

    def test_load_missing_mappings_key(self, tmp_path: Path) -> None:
        """Missing 'mappings' raises MappingError."""
        content = textwrap.dedent("""\
            version: "1"
        """)
        p = tmp_path / "bad.yaml"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(MappingError) as exc_info:
            load_mapping(p)
        assert "mappings" in str(exc_info.value)

    def test_load_missing_required_entry_keys(
        self, tmp_path: Path
    ) -> None:
        """Missing entry keys reported in error."""
        content = textwrap.dedent("""\
            version: "1"
            mappings:
              - openfisca_name: "x"
        """)
        p = tmp_path / "bad.yaml"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(MappingError) as exc_info:
            load_mapping(p)
        assert "project_name" in str(exc_info.value)
        assert "direction" in str(exc_info.value)

    def test_load_invalid_type_string(self, tmp_path: Path) -> None:
        """Invalid type string raises MappingError."""
        content = textwrap.dedent("""\
            version: "1"
            mappings:
              - openfisca_name: "x"
                project_name: "y"
                direction: "output"
                type: "not_a_real_type"
        """)
        p = tmp_path / "bad.yaml"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(MappingError) as exc_info:
            load_mapping(p)
        assert "not_a_real_type" in str(exc_info.value)

    def test_load_duplicate_openfisca_names(
        self, tmp_path: Path
    ) -> None:
        """Duplicate openfisca_name raises MappingError."""
        content = textwrap.dedent("""\
            version: "1"
            mappings:
              - openfisca_name: "x"
                project_name: "y1"
                direction: "output"
              - openfisca_name: "x"
                project_name: "y2"
                direction: "output"
        """)
        p = tmp_path / "bad.yaml"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(MappingError) as exc_info:
            load_mapping(p)
        assert "duplicate" in str(exc_info.value).lower()

    def test_load_duplicate_project_names(
        self, tmp_path: Path
    ) -> None:
        """Duplicate project_name raises MappingError."""
        content = textwrap.dedent("""\
            version: "1"
            mappings:
              - openfisca_name: "a"
                project_name: "same"
                direction: "output"
              - openfisca_name: "b"
                project_name: "same"
                direction: "output"
        """)
        p = tmp_path / "bad.yaml"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(MappingError) as exc_info:
            load_mapping(p)
        assert "duplicate" in str(exc_info.value).lower()

    def test_load_aggregates_all_errors(self, tmp_path: Path) -> None:
        """Multiple errors reported at once."""
        content = textwrap.dedent("""\
            version: "1"
            mappings:
              - openfisca_name: "x"
                project_name: "y"
                direction: "output"
                type: "bad_type"
              - openfisca_name: "a"
        """)
        p = tmp_path / "bad.yaml"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(MappingError) as exc_info:
            load_mapping(p)
        msg = str(exc_info.value)
        assert "bad_type" in msg
        assert "project_name" in msg

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Nonexistent file raises MappingError."""
        p = tmp_path / "does_not_exist.yaml"
        with pytest.raises(MappingError):
            load_mapping(p)

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        """Invalid YAML syntax raises MappingError."""
        p = tmp_path / "bad.yaml"
        p.write_text("{{invalid: yaml: [", encoding="utf-8")
        with pytest.raises(MappingError):
            load_mapping(p)

    def test_load_invalid_direction(self, tmp_path: Path) -> None:
        """Invalid direction value raises MappingError."""
        content = textwrap.dedent("""\
            version: "1"
            mappings:
              - openfisca_name: "x"
                project_name: "y"
                direction: "sideways"
        """)
        p = tmp_path / "bad.yaml"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(MappingError) as exc_info:
            load_mapping(p)
        assert "sideways" in str(exc_info.value)

    def test_load_path_outside_allowed_roots(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Paths outside allowed directories are rejected."""
        allowed_root = tmp_path / "allowed"
        denied_root = tmp_path / "denied"
        allowed_root.mkdir()
        denied_root.mkdir()

        p = denied_root / "mapping.yaml"
        p.write_text('version: "1"\nmappings: []\n', encoding="utf-8")

        monkeypatch.setattr(
            mapping_module,
            "_allowed_mapping_roots",
            lambda: (allowed_root.resolve(),),
        )

        with pytest.raises(MappingError) as exc_info:
            load_mapping(p)
        assert "outside allowed mapping directories" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Task 3 tests: Mapping application
# ---------------------------------------------------------------------------


class TestApplyOutputMapping:
    """Tests for apply_output_mapping function."""

    def test_renames_output_columns(
        self, sample_yaml: Path, output_table: pa.Table
    ) -> None:
        """Columns renamed from OpenFisca to project names."""
        config = load_mapping(sample_yaml)
        result = apply_output_mapping(output_table, config)
        assert "income_tax" in result.column_names
        assert "household_id" in result.column_names
        assert "impot_revenu_net" not in result.column_names
        assert "menage_id" not in result.column_names

    def test_preserves_unmapped_columns(
        self, sample_yaml: Path, output_table: pa.Table
    ) -> None:
        """Extra columns are passed through unchanged."""
        config = load_mapping(sample_yaml)
        result = apply_output_mapping(output_table, config)
        assert "extra_col" in result.column_names

    def test_preserves_row_count(
        self, sample_yaml: Path, output_table: pa.Table
    ) -> None:
        """Row count is unchanged after mapping."""
        config = load_mapping(sample_yaml)
        result = apply_output_mapping(output_table, config)
        assert result.num_rows == output_table.num_rows

    def test_preserves_metadata(
        self, sample_yaml: Path, output_table: pa.Table
    ) -> None:
        """Table metadata is preserved after mapping."""
        meta = {"source": b"test"}
        table_with_meta = output_table.replace_schema_metadata(meta)
        config = load_mapping(sample_yaml)
        result = apply_output_mapping(table_with_meta, config)
        assert result.schema.metadata is not None
        assert result.schema.metadata[b"source"] == b"test"

    def test_coerces_mapped_column_to_configured_type(
        self, sample_yaml: Path
    ) -> None:
        """Mapped output columns are cast to configured pa_type."""
        table = pa.table(
            {
                "impot_revenu_net": ["100.0", "200.0"],
                "menage_id": [1, 2],
            }
        )
        config = load_mapping(sample_yaml)
        result = apply_output_mapping(table, config)
        assert result.schema.field("income_tax").type == pa.float64()


class TestApplyInputMapping:
    """Tests for apply_input_mapping function."""

    def test_renames_input_columns(
        self, sample_yaml: Path, project_table: pa.Table
    ) -> None:
        """Columns renamed from project to OpenFisca names."""
        config = load_mapping(sample_yaml)
        result = apply_input_mapping(project_table, config)
        assert "menage_id" in result.column_names
        assert "household_id" not in result.column_names

    def test_preserves_unmapped_columns_input(
        self, sample_yaml: Path, project_table: pa.Table
    ) -> None:
        """Extra columns preserved in input mapping."""
        config = load_mapping(sample_yaml)
        result = apply_input_mapping(project_table, config)
        assert "extra_col" in result.column_names


class TestBidirectionalMapping:
    """Tests for round-trip mapping (AC-4)."""

    def test_roundtrip_output_then_input(
        self, sample_yaml: Path, output_table: pa.Table
    ) -> None:
        """Round-trip restores 'both' direction columns."""
        config = load_mapping(sample_yaml)
        # output mapping: OpenFisca → project names
        projected = apply_output_mapping(output_table, config)
        # input mapping: project → OpenFisca names (input/both)
        restored = apply_input_mapping(projected, config)
        # menage_id is "both" so it should restore
        assert "menage_id" in restored.column_names
        assert "household_id" not in restored.column_names


# ---------------------------------------------------------------------------
# Task 4 tests: Validation against actual data
# ---------------------------------------------------------------------------


class TestValidateMapping:
    """Tests for validate_mapping function."""

    def test_valid_mapping_no_errors(self, sample_yaml: Path) -> None:
        """All columns present produces no errors."""
        config = load_mapping(sample_yaml)
        cols = ("impot_revenu_net", "menage_id", "extra")
        result = validate_mapping(config, cols)
        assert len(result.errors) == 0

    def test_unknown_variable_with_suggestion(
        self, sample_yaml: Path
    ) -> None:
        """Unknown column produces error with closest match."""
        config = load_mapping(sample_yaml)
        cols = ("impot_revenu_net", "menage_idx")
        result = validate_mapping(config, cols)
        assert len(result.errors) > 0
        error_text = " ".join(result.errors)
        assert "menage_id" in error_text

    def test_reports_all_unknowns(self) -> None:
        """Multiple unknowns all reported at once."""
        fm1 = FieldMapping("nonexistent_a", "a", "output", pa.float64())
        fm2 = FieldMapping("nonexistent_b", "b", "output", pa.float64())
        config = MappingConfig(mappings=(fm1, fm2))
        result = validate_mapping(config, ("real_col",))
        assert len(result.errors) == 2

    def test_ignores_input_only_mappings(self) -> None:
        """Input-only mappings are not validated against adapter output columns."""
        config = MappingConfig(
            mappings=(
                FieldMapping(
                    "project_only_input",
                    "project_input",
                    "input",
                    pa.float64(),
                ),
            )
        )
        result = validate_mapping(config, ("impot_revenu_net",))
        assert result.errors == ()


# ---------------------------------------------------------------------------
# Task 5 tests: Mapping composition
# ---------------------------------------------------------------------------


class TestMergeMappings:
    """Tests for merge_mappings function."""

    def test_merge_two_configs(self) -> None:
        """Later config overrides earlier by openfisca_name."""
        fm1 = FieldMapping("x", "old_name", "output", pa.float64())
        fm2 = FieldMapping("x", "new_name", "output", pa.float64())
        fm3 = FieldMapping("y", "another", "input", pa.int64())
        c1 = MappingConfig(mappings=(fm1, fm3))
        c2 = MappingConfig(mappings=(fm2,))
        merged = merge_mappings(c1, c2)
        assert merged.by_openfisca_name("x") is not None
        x = merged.by_openfisca_name("x")
        assert x is not None
        assert x.project_name == "new_name"
        assert merged.by_openfisca_name("y") is not None

    def test_merge_preserves_non_overlapping(self) -> None:
        """Non-overlapping configs keep all mappings."""
        fm1 = FieldMapping("a", "a_proj", "output", pa.float64())
        fm2 = FieldMapping("b", "b_proj", "output", pa.float64())
        c1 = MappingConfig(mappings=(fm1,))
        c2 = MappingConfig(mappings=(fm2,))
        merged = merge_mappings(c1, c2)
        assert len(merged.mappings) == 2

    def test_merge_conflict_logs_source_file_info(
        self, sample_yaml: Path, extension_yaml: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Conflict warning includes both source paths."""
        caplog.set_level("WARNING")
        base = load_mapping(sample_yaml)
        extension = load_mapping(extension_yaml)
        merge_mappings(base, extension)
        logs = " ".join(record.getMessage() for record in caplog.records)
        assert str(sample_yaml.resolve()) in logs
        assert str(extension_yaml.resolve()) in logs


class TestLoadMappings:
    """Tests for load_mappings convenience function."""

    def test_load_and_merge_files(
        self, sample_yaml: Path, extension_yaml: Path
    ) -> None:
        """Extension file overrides base file mappings."""
        config = load_mappings(sample_yaml, extension_yaml)
        fm = config.by_openfisca_name("impot_revenu_net")
        assert fm is not None
        assert fm.project_name == "net_income_tax"
        assert config.by_openfisca_name("taxe_carbone") is not None
        assert config.by_openfisca_name("menage_id") is not None


# ---------------------------------------------------------------------------
# Task 6 additional tests
# ---------------------------------------------------------------------------


class TestEmptyMapping:
    """Tests for empty mapping config edge case."""

    def test_empty_mapping_passes_through(self) -> None:
        """Empty mapping passes all columns through."""
        config = MappingConfig(mappings=())
        table = pa.table({"a": [1], "b": [2]})
        result = apply_output_mapping(table, config)
        assert result.column_names == ["a", "b"]
        assert result.equals(table)


class TestAdapterIntegration:
    """Integration with ComputationResult (AC-7)."""

    def test_mapping_on_computation_result(
        self, sample_yaml: Path
    ) -> None:
        """Mapping renames output without breaking metadata."""
        from reformlab.computation.types import ComputationResult

        output = pa.table(
            {
                "impot_revenu_net": [100.0, 200.0],
                "menage_id": [1, 2],
            }
        )
        result = ComputationResult(
            output_fields=output,
            adapter_version="0.1.0",
            period=2024,
            metadata={"source": "test"},
        )
        config = load_mapping(sample_yaml)
        mapped = apply_output_mapping(result.output_fields, config)
        assert "income_tax" in mapped.column_names
        assert "household_id" in mapped.column_names
        assert result.metadata["source"] == "test"
        assert result.period == 2024
