from __future__ import annotations

class CompatibilityError(Exception):
    expected: str
    actual: str
    details: str

    def __init__(
        self,
        expected: str,
        actual: str,
        details: str = "",
    ) -> None: ...

class ApiMappingError(Exception):
    summary: str
    reason: str
    fix: str
    invalid_names: tuple[str, ...]
    valid_names: tuple[str, ...]
    suggestions: dict[str, list[str]]

    def __init__(
        self,
        *,
        summary: str,
        reason: str,
        fix: str,
        invalid_names: tuple[str, ...] = ...,
        valid_names: tuple[str, ...] = ...,
        suggestions: dict[str, list[str]] | None = ...,
    ) -> None: ...
