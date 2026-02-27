import pyarrow as pa

from reformlab.computation.ingestion import DataSchema


def fill_missing_energy_columns(table: pa.Table) -> pa.Table: ...

SYNTHETIC_POPULATION_SCHEMA: DataSchema
EMISSION_FACTOR_SCHEMA: DataSchema
