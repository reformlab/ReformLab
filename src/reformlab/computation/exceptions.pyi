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
