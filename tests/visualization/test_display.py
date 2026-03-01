"""Tests for reformlab.visualization.display module."""

from __future__ import annotations

import pyarrow as pa

from reformlab.visualization.display import show


class TestShow:
    """Tests for the show() formatted table display function."""

    def test_show_basic_table(self, capsys: object) -> None:
        """Captures stdout, verifies header/separator/rows printed."""
        import _pytest.capture

        assert isinstance(capsys, _pytest.capture.CaptureFixture)
        table = pa.table(
            {
                "name": pa.array(["Alice", "Bob", "Charlie"]),
                "value": pa.array([1.0, 2.0, 3.0]),
            }
        )
        show(table)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 5  # header + separator + 3 rows
        assert "name" in lines[0]
        assert "value" in lines[0]
        assert "---" in lines[1]
        assert "Alice" in lines[2]
        assert "Bob" in lines[3]
        assert "Charlie" in lines[4]

    def test_show_truncation(self, capsys: object) -> None:
        """20-row table with n=5 shows truncation message."""
        import _pytest.capture

        assert isinstance(capsys, _pytest.capture.CaptureFixture)
        table = pa.table({"x": pa.array(range(20))})
        show(table, n=5)
        captured = capsys.readouterr()
        assert "... (15 more rows)" in captured.out

    def test_show_empty_table(self, capsys: object) -> None:
        """Empty table prints header and separator only."""
        import _pytest.capture

        assert isinstance(capsys, _pytest.capture.CaptureFixture)
        table = pa.table({"col_a": pa.array([], type=pa.utf8())})
        show(table)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 2  # header + separator
        assert "col_a" in lines[0]

    def test_show_single_row(self, capsys: object) -> None:
        """Single-row table prints correctly."""
        import _pytest.capture

        assert isinstance(capsys, _pytest.capture.CaptureFixture)
        table = pa.table({"id": pa.array([42]), "label": pa.array(["test"])})
        show(table)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 3  # header + separator + 1 row
        assert "42" in lines[2]
        assert "test" in lines[2]

    def test_show_negative_n_clamps_to_one(self, capsys: object) -> None:
        """Negative n is clamped to 1, shows at least one row."""
        import _pytest.capture

        assert isinstance(capsys, _pytest.capture.CaptureFixture)
        table = pa.table({"x": pa.array([10, 20, 30])})
        show(table, n=-5)
        captured = capsys.readouterr()
        assert "10" in captured.out
        assert "... (2 more rows)" in captured.out
