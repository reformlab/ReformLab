"""Contract checks for Phase 1 exit checklist completeness and evidence links."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKLIST_PATH = ROOT / "docs" / "phase-1-exit-checklist.md"


def _extract_backtick_paths(markdown_fragment: str) -> list[Path]:
    paths: list[Path] = []
    for token in re.findall(r"`([^`]+)`", markdown_fragment):
        token = token.strip()
        if not token:
            continue
        token = token.split("::", 1)[0]
        if "/" not in token and "." not in token:
            continue
        paths.append(ROOT / token)
    return paths


def test_checklist_has_required_header_metadata() -> None:
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "# Phase 1 Exit Checklist" in content
    assert "**Project:** ReformLab" in content
    assert "**Date:** 2026-02-28" in content
    assert "**Version:** 1.1" in content


def test_functional_rows_cover_fr1_to_fr35_with_valid_evidence() -> None:
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    matches = re.findall(
        r"^\| \*\*FR(\d+)\*\* \| (.+?) \| (.+?) \| (.+?) \|$",
        content,
        flags=re.MULTILINE,
    )

    assert len(matches) == 35
    assert [int(fr_num) for fr_num, _, _, _ in matches] == list(range(1, 36))

    for _, requirement, evidence, status in matches:
        assert requirement.strip()
        assert any(marker in status for marker in ("PASS", "FAIL", "DEFERRED-P1"))

        evidence_paths = _extract_backtick_paths(evidence)
        assert evidence_paths, f"No evidence paths found: {evidence}"
        for evidence_path in evidence_paths:
            assert evidence_path.exists(), f"Missing evidence path: {evidence_path}"


def test_non_functional_rows_cover_nfr1_to_nfr21_with_required_fields() -> None:
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    matches = re.findall(
        r"^\| \*\*NFR(\d+)\*\* \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \|$",
        content,
        flags=re.MULTILINE,
    )

    assert len(matches) == 21
    assert [int(nfr_num) for nfr_num, *_ in matches] == list(range(1, 22))

    for _, metric, target, measured_result, evidence, status in matches:
        assert metric.strip()
        assert target.strip()
        assert measured_result.strip()
        assert any(marker in status for marker in ("PASS", "FAIL", "DEFERRED-P1"))

        evidence_paths = _extract_backtick_paths(evidence)
        assert evidence_paths, f"No evidence paths found: {evidence}"
        for evidence_path in evidence_paths:
            assert evidence_path.exists(), f"Missing evidence path: {evidence_path}"


def test_pilot_signoff_has_explicit_yes_no_for_ac1_to_ac7() -> None:
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    for ac_num in range(1, 8):
        pattern = rf"AC-{ac_num}:[^\n]+-> \[x\] Yes / \[ \] No"
        assert re.search(pattern, content), f"Missing explicit yes/no for AC-{ac_num}"
