# Dataset Folder Convention

A dataset can be defined as a folder containing a data file and JSON metadata:

```
my-dataset/
├── data.csv          # or data.parquet
├── schema.json       # DataSchema as JSON
└── source.json       # DataSourceMetadata as JSON
```

## Usage

```python
from reformlab.data import load_population_folder

population, manifest = load_population_folder("path/to/my-dataset/")
```

## Files

### `schema.json`

Defines the expected columns, their PyArrow types, and whether each is required or optional.

### `source.json`

Describes the data source origin (name, version, URL, description, license).

## Example

See `insee-filosofi-commune/` for a reference example showing how the INSEE Filosofi commune dataset's metadata maps to JSON.
