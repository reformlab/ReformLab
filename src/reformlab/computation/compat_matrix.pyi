from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class CompatibilityInfo:
    version: str
    status: str
    modes_tested: tuple[str, ...]
    known_issues: tuple[str, ...]
    tested_date: str | None
    guidance: str
    matrix_url: str

def load_matrix() -> dict[str, Any]: ...
def get_compatibility_info(version: str) -> CompatibilityInfo: ...
def _clear_cache() -> None: ...
