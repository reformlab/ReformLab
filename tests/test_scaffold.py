"""Smoke tests for scaffolded subsystem package layout."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path


def test_all_subsystem_packages_are_importable() -> None:
    package_names = (
        "reformlab.computation",
        "reformlab.data",
        "reformlab.templates",
        "reformlab.orchestrator",
        "reformlab.vintage",
        "reformlab.indicators",
        "reformlab.governance",
        "reformlab.interfaces",
    )
    for package_name in package_names:
        module = import_module(package_name)
        assert module is not None


def test_scaffold_directory_structure_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    package_dirs = (
        root / "src/reformlab/computation",
        root / "src/reformlab/data",
        root / "src/reformlab/templates",
        root / "src/reformlab/orchestrator",
        root / "src/reformlab/vintage",
        root / "src/reformlab/indicators",
        root / "src/reformlab/governance",
        root / "src/reformlab/interfaces",
    )
    for package_dir in package_dirs:
        assert package_dir.is_dir()
        assert (package_dir / "__init__.py").is_file()


_SCAFFOLD_ONLY = (
    "orchestrator",
    "vintage",
    "indicators",
    "governance",
    "interfaces",
)


def test_scaffold_packages_are_empty_placeholders() -> None:
    """Placeholder packages must stay empty until their epic is implemented."""
    root = Path(__file__).resolve().parents[1]
    for name in _SCAFFOLD_ONLY:
        init = root / "src/reformlab" / name / "__init__.py"
        content = init.read_text().strip()
        rel = init.relative_to(root)
        assert content == "", f"{rel} should be empty, got: {content!r}"
