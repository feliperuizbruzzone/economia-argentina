"""Assemble the complete AFIP Ganancias Sociedades long CSV without branch harmonization."""

import csv
from pathlib import Path
import sys


sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR.parents[0] / "config"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(CONFIG_DIR))

from afip_ganancias_sociedades import long_fieldnames  # noqa: E402
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH,
    GANANCIAS_SOCIEDADES_P0_LONG_PATH,
    GANANCIAS_SOCIEDADES_P1_LONG_PATH,
    GANANCIAS_SOCIEDADES_P2_LONG_PATH,
    GANANCIAS_SOCIEDADES_P3_LONG_PATH,
    GANANCIAS_SOCIEDADES_P4_LONG_PATH,
    GANANCIAS_SOCIEDADES_P5_LONG_PATH,
    GANANCIAS_SOCIEDADES_P6_LONG_PATH,
)


COMPONENT_PATHS = (
    GANANCIAS_SOCIEDADES_P0_LONG_PATH,
    GANANCIAS_SOCIEDADES_P1_LONG_PATH,
    GANANCIAS_SOCIEDADES_P2_LONG_PATH,
    GANANCIAS_SOCIEDADES_P3_LONG_PATH,
    GANANCIAS_SOCIEDADES_P4_LONG_PATH,
    GANANCIAS_SOCIEDADES_P5_LONG_PATH,
    GANANCIAS_SOCIEDADES_P6_LONG_PATH,
)


def main() -> None:
    """Write one dated source-preserving CSV from the validated P0-P6 extracts."""

    fieldnames = long_fieldnames()
    total_rows = 0
    GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for path in COMPONENT_PATHS:
            with path.open(encoding="utf-8") as input_file:
                reader = csv.DictReader(input_file)
                if reader.fieldnames != fieldnames:
                    raise ValueError(f"Unexpected fieldnames in {path}")
                for row in reader:
                    writer.writerow(row)
                    total_rows += 1

    print(f"wrote={GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH}")
    print(f"rows={total_rows}")
    print(f"component_files={len(COMPONENT_PATHS)}")


if __name__ == "__main__":
    main()
