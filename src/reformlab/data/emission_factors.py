# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

from dataclasses import dataclass

import pyarrow as pa
import pyarrow.compute as pc


@dataclass(frozen=True)
class EmissionFactorIndex:
    """Frozen index wrapping a ``pa.Table`` of emission factors with lookup methods."""

    _table: pa.Table

    def by_category(self, category: str) -> pa.Table:
        """Return rows matching *category*."""
        mask = pc.equal(self._table.column("category"), category)
        return self._table.filter(mask)

    def by_category_and_year(self, category: str, year: int) -> pa.Table:
        """Return rows matching *category* and *year*."""
        if "year" not in self._table.column_names:
            raise ValueError(
                "Emission factor lookup failed - "
                "missing required 'year' column - "
                "Use a table that includes a year column for year-specific lookups"
            )
        mask = pc.and_(
            pc.equal(self._table.column("category"), category),
            pc.equal(self._table.column("year"), year),
        )
        return self._table.filter(mask)

    def categories(self) -> tuple[str, ...]:
        """Return sorted unique category names."""
        unique = pc.unique(self._table.column("category")).to_pylist()
        return tuple(sorted(v for v in unique if v is not None))


def build_emission_factor_index(table: pa.Table) -> EmissionFactorIndex:
    """Create an ``EmissionFactorIndex`` from a loaded emission factor table."""
    return EmissionFactorIndex(_table=table)
