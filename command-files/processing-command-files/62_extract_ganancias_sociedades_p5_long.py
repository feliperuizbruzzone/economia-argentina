"""Extract P5 Ganancias Sociedades legacy CAB/XLS tables into long format."""

import csv
from pathlib import Path
import sys


sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR.parents[0] / "config"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(CONFIG_DIR))

from afip_ganancias_sociedades import (  # noqa: E402
    extract_p5_old_cab_xls_detail_legacy_numbering,
    long_fieldnames,
)
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_P5_INVENTORY_PATH,
    GANANCIAS_SOCIEDADES_P5_LONG_PATH,
    RAW_ARCHIVE_DIR,
)


def _load_inventory() -> list[dict[str, str]]:
    with GANANCIAS_SOCIEDADES_P5_INVENTORY_PATH.open(encoding="utf-8") as input_file:
        return list(csv.DictReader(input_file))


def main() -> None:
    inventory_rows = _load_inventory()
    rows = extract_p5_old_cab_xls_detail_legacy_numbering(RAW_ARCHIVE_DIR, inventory_rows)

    GANANCIAS_SOCIEDADES_P5_LONG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with GANANCIAS_SOCIEDADES_P5_LONG_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as output_file:
        writer = csv.DictWriter(output_file, fieldnames=long_fieldnames())
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote={GANANCIAS_SOCIEDADES_P5_LONG_PATH}")
    print(f"rows={len(rows)}")
    print("period_id=P5_old_cab_xls_detail_legacy_numbering")


if __name__ == "__main__":
    main()
