"""Generate and persist a synthetic population Parquet file.

Story 8.2 — Task 5: Persistent population file generation script.

Usage:
    uv run python scripts/generate_synthetic_population.py
    uv run python scripts/generate_synthetic_population.py --size 500000 --seed 42
    uv run python scripts/generate_synthetic_population.py --output data/synthetic/custom.parquet
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure src/ is importable when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from reformlab.data.synthetic import generate_synthetic_population, save_synthetic_population


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic synthetic population Parquet file.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=100_000,
        help="Number of households to generate (default: 100,000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output Parquet file path (default: data/synthetic/population_{size}_seed{seed}.parquet)",
    )
    args = parser.parse_args()

    output_path = args.output
    if output_path is None:
        output_path = f"data/synthetic/population_{args.size}_seed{args.seed}.parquet"

    path = Path(output_path)

    print(f"Generating {args.size:,} households (seed={args.seed})...")
    table = generate_synthetic_population(size=args.size, seed=args.seed)

    print(f"Saving to {path}...")
    manifest = save_synthetic_population(table, path, seed=args.seed)

    print("\nManifest summary:")
    print(f"  Path:       {manifest.file_path}")
    print(f"  Rows:       {manifest.row_count:,}")
    print(f"  Columns:    {', '.join(manifest.column_names)}")
    print(f"  SHA-256:    {manifest.content_hash}")
    print(f"  Format:     {manifest.format}")
    print(f"  Loaded at:  {manifest.loaded_at}")


if __name__ == "__main__":
    main()
