"""Consistency checks between sprint tracking and epic/story status artifacts."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DOC_EPICS = ROOT / "docs" / "epics.md"
PLAN_EPICS = ROOT / "_bmad-output" / "planning-artifacts" / "epics.md"
SPRINT_STATUS = ROOT / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
IMPL_ARTIFACTS = ROOT / "_bmad-output" / "implementation-artifacts"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_table_status(content: str, epic_label: str) -> str:
    match = re.search(
        rf"^\| {re.escape(epic_label)} \| [^|]+ \| [^|]+ \| ([^|]+) \|",
        content,
        flags=re.MULTILINE,
    )
    assert match, f"Could not find table row for {epic_label}"
    return match.group(1).strip()


def _extract_epic_section(content: str, epic_number: int) -> str:
    match = re.search(
        rf"## Epic {epic_number}:.*?(?=\n## Epic \d+:|\Z)",
        content,
        flags=re.DOTALL,
    )
    assert match, f"Could not find Epic {epic_number} section"
    return match.group(0)


def _extract_epic_status(section: str) -> str:
    match = re.search(r"(?:_Status:|\*\*Status:\*\*)\s*([A-Za-z-]+)", section)
    assert match, "Could not find epic status marker"
    return match.group(1).strip().lower()


def _extract_story_statuses(section: str) -> list[str]:
    lines = section.splitlines()
    statuses: list[str] = []
    for idx, line in enumerate(lines):
        if not line.startswith("### Story "):
            continue
        for lookahead in range(idx + 1, min(idx + 8, len(lines))):
            if lines[lookahead].startswith("**Status:**"):
                statuses.append(lines[lookahead].split("**Status:**", 1)[1].strip().lower())
                break
    return statuses


def test_sprint_status_marks_epics_11_12_done() -> None:
    sprint = yaml.safe_load(_read(SPRINT_STATUS))
    development_status = sprint["development_status"]

    assert development_status["epic-11"] == "done"
    assert development_status["epic-12"] == "done"
    for key, value in development_status.items():
        if re.match(r"^(11|12)-\d-", key):
            assert value == "done", f"{key} should be done in sprint-status.yaml"


def test_docs_and_planning_epics_align_on_epic_11_12_done() -> None:
    docs_content = _read(DOC_EPICS)
    plan_content = _read(PLAN_EPICS)

    assert _extract_table_status(docs_content, "Epic 11") == "done"
    assert _extract_table_status(docs_content, "Epic 12") == "done"
    assert _extract_table_status(plan_content, "EPIC-11") == "done"
    assert _extract_table_status(plan_content, "EPIC-12") == "done"

    for epic_number, expected_count in ((11, 8), (12, 5)):
        docs_section = _extract_epic_section(docs_content, epic_number)
        plan_section = _extract_epic_section(plan_content, epic_number)

        assert _extract_epic_status(docs_section) == "done"
        assert _extract_epic_status(plan_section) == "done"

        docs_story_statuses = _extract_story_statuses(docs_section)
        plan_story_statuses = _extract_story_statuses(plan_section)
        assert len(docs_story_statuses) == expected_count
        assert len(plan_story_statuses) == expected_count
        assert all(status == "done" for status in docs_story_statuses)
        assert all(status == "done" for status in plan_story_statuses)


def test_implementation_story_status_vocabulary_is_done_only() -> None:
    story_files = sorted(IMPL_ARTIFACTS.glob("11-[1-8]-*.md")) + sorted(
        IMPL_ARTIFACTS.glob("12-[1-5]-*.md")
    )

    status_lines: list[str] = []
    for story_file in story_files:
        header = "\n".join(story_file.read_text(encoding="utf-8").splitlines()[:24])
        match = re.search(r"^Status:\s*(.+)$", header, flags=re.MULTILINE)
        if match:
            status_lines.append(match.group(1).strip().lower())

    # 12-2 is currently represented by a synthesis file without top-level story status.
    assert len(status_lines) >= 12
    assert all(status == "done" for status in status_lines)
