"""Build the P5 Ganancias Sociedades legacy CAB/XLS inventory."""

import csv
from pathlib import Path
import sys


sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR.parents[0] / "config"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(CONFIG_DIR))

from afip_ganancias_sociedades import (  # noqa: E402
    inventory_fieldnames,
    inventory_p5_old_cab_xls_legacy_numbering,
)
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_P5_INVENTORY_PATH,
    RAW_ARCHIVE_DIR,
)


def main() -> None:
    rows = inventory_p5_old_cab_xls_legacy_numbering(RAW_ARCHIVE_DIR)
    GANANCIAS_SOCIEDADES_P5_INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with GANANCIAS_SOCIEDADES_P5_INVENTORY_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as output_file:
        writer = csv.DictWriter(output_file, fieldnames=inventory_fieldnames())
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote={GANANCIAS_SOCIEDADES_P5_INVENTORY_PATH}")
    print(f"rows={len(rows)}")
    print("period_id=P5_old_cab_xls_detail_legacy_numbering")


if __name__ == "__main__":
    main()
