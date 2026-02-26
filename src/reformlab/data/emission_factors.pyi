from __future__ import annotations

from dataclasses import dataclass

import pyarrow as pa

@dataclass(frozen=True)
class EmissionFactorIndex:
    _table: pa.Table

    def by_category(self, category: str) -> pa.Table: ...
    def by_category_and_year(
        self, category: str, year: int
    ) -> pa.Table: ...
    def categories(self) -> tuple[str, ...]: ...

def build_emission_factor_index(
    table: pa.Table,
) -> EmissionFactorIndex: ...
