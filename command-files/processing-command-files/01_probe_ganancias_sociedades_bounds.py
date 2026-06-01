"""Probe automatic table-bound detection on one modern XLS example."""

from pathlib import Path
from zipfile import ZipFile
import sys

import xlrd


sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR.parents[0] / "config"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(CONFIG_DIR))

from afip_ganancias_sociedades import detect_xls_table_bounds  # noqa: E402
from project_config import RAW_ARCHIVE_DIR  # noqa: E402


EXAMPLE_ARCHIVE = "Estadisticas-Tributarias-2023.zip"
EXAMPLE_TABLE_SUFFIX = "/2.3.1.1.1.xls"


def _find_example_member(zip_file: ZipFile) -> str:
    candidates = [
        name
        for name in zip_file.namelist()
        if name.endswith(EXAMPLE_TABLE_SUFFIX)
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected exactly one member ending in {EXAMPLE_TABLE_SUFFIX}; "
            f"found {len(candidates)}."
        )
    return candidates[0]


def main() -> None:
    archive_path = RAW_ARCHIVE_DIR / EXAMPLE_ARCHIVE
    with ZipFile(archive_path) as zip_file:
        member_name = _find_example_member(zip_file)
        workbook = xlrd.open_workbook(
            file_contents=zip_file.read(member_name),
            on_demand=True,
        )

    sheet = workbook.sheet_by_index(0)
    rows = [
        [sheet.cell_value(row_index, col_index) for col_index in range(sheet.ncols)]
        for row_index in range(sheet.nrows)
    ]
    bounds = detect_xls_table_bounds(rows)

    if bounds.header_start_row != 6:
        raise AssertionError(f"Expected zero-based header row 6, got {bounds.header_start_row}.")
    if bounds.data_start_row != 9:
        raise AssertionError(f"Expected zero-based data row 9, got {bounds.data_start_row}.")
    if bounds.first_data_label != "TOTAL":
        raise AssertionError(f"Expected first data label TOTAL, got {bounds.first_data_label}.")

    print(f"archive={EXAMPLE_ARCHIVE}")
    print(f"member={member_name}")
    print(f"header_start_row_zero_based={bounds.header_start_row}")
    print(f"header_start_row_spreadsheet={bounds.header_start_row + 1}")
    print(f"data_start_row_zero_based={bounds.data_start_row}")
    print(f"data_start_row_spreadsheet={bounds.data_start_row + 1}")
    print(f"first_data_label={bounds.first_data_label}")


if __name__ == "__main__":
    main()
