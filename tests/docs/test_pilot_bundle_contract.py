# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Static checks for pilot distribution contract artifacts.

These checks cover Story 7-4 bundle completeness expectations without requiring
a full packaging/release pipeline inside unit-test environments.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_pilot_bundle_required_artifacts_exist() -> None:
    """AC-7: companion pilot docs/notebooks/examples are present in-repo."""
    required_paths = [
        ROOT / "docs" / "pilot-checklist.md",
        ROOT / "notebooks" / "quickstart.ipynb",
        ROOT / "notebooks" / "advanced.ipynb",
        ROOT / "examples" / "workflows",
    ]

    for path in required_paths:
        assert path.exists(), f"Missing required pilot bundle artifact: {path}"


def test_pilot_checklist_tracks_all_story_acceptance_criteria() -> None:
    """Checklist should expose all AC sign-off items for external pilots."""
    checklist = (ROOT / "docs" / "pilot-checklist.md").read_text(encoding="utf-8")
    for idx in range(1, 8):
        assert f"AC-{idx}" in checklist


def test_wheel_packaging_boundary_matches_architecture_contract() -> None:
    """Architecture contract: only src/reformlab is packaged into the wheel."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    wheel_target = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]
    assert wheel_target["packages"] == ["src/reformlab"]
