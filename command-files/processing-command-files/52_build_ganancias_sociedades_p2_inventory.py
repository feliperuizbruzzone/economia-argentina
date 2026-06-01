"""Build the P2 Ganancias Sociedades HTML activity-table inventory."""

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
    inventory_p2_old_html_millions,
)
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_P2_INVENTORY_PATH,
    RAW_ARCHIVE_DIR,
)


def main() -> None:
    rows = inventory_p2_old_html_millions(RAW_ARCHIVE_DIR)
    GANANCIAS_SOCIEDADES_P2_INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with GANANCIAS_SOCIEDADES_P2_INVENTORY_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as output_file:
        writer = csv.DictWriter(output_file, fieldnames=inventory_fieldnames())
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote={GANANCIAS_SOCIEDADES_P2_INVENTORY_PATH}")
    print(f"rows={len(rows)}")
    print("period_id=P2_old_html_detail_millions")


if __name__ == "__main__":
    main()
