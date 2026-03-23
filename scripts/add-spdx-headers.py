# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Add SPDX license headers to all source files."""

from pathlib import Path

SPDX_PY = "# SPDX-License-Identifier: AGPL-3.0-or-later\n# Copyright 2026 Lucas Vivier\n"
SPDX_TS = "// SPDX-License-Identifier: AGPL-3.0-or-later\n// Copyright 2026 Lucas Vivier\n"

DIRS = [Path("src"), Path("tests"), Path("frontend/src")]


def add_headers() -> None:
    modified = 0
    skipped = 0

    for base_dir in DIRS:
        if not base_dir.exists():
            print(f"  Skipping {base_dir} (not found)")
            continue

        for path in sorted(base_dir.rglob("*")):
            if path.suffix == ".py":
                header = SPDX_PY
            elif path.suffix in (".ts", ".tsx"):
                header = SPDX_TS
            else:
                continue

            content = path.read_text(encoding="utf-8")

            if content.startswith(("# SPDX-License-Identifier", "// SPDX-License-Identifier")):
                skipped += 1
                continue

            path.write_text(header + content, encoding="utf-8")
            modified += 1

    print(f"Modified: {modified}")
    print(f"Skipped:  {skipped}")


if __name__ == "__main__":
    add_headers()
