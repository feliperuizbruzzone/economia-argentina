"""Probe current P0 detectors against the Fase 3 backward inventory."""

from collections import Counter
import csv
from pathlib import Path
import re
import sys
from zipfile import ZipFile


sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR.parents[0] / "config"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(CONFIG_DIR))

from afip_ganancias_sociedades import (  # noqa: E402
    detect_p0_23111_columns,
    detect_p0_231121_columns,
    detect_p0_231122_columns,
    detect_p0_231123_columns,
    detect_p0_231124_columns,
    detect_p0_231125_columns,
    detect_p0_231126_columns,
    detect_p0_231127_columns,
    detect_p0_23113_columns,
    detect_p0_23114_columns,
    detect_p0_231151_columns,
    detect_p0_2311511_columns,
    detect_p0_2311512_columns,
    detect_p0_2311513_columns,
    detect_p0_2311514_columns,
    detect_p0_231152_columns,
    detect_p0_2311521_columns,
    detect_p0_231153_columns,
    detect_p0_2311531_columns,
    detect_p0_2311532_columns,
    detect_xls_table_bounds,
    xls_rows_from_bytes,
)
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_P0_BACKWARD_DETECTOR_PROBE_PATH,
    GANANCIAS_SOCIEDADES_P0_BACKWARD_INVENTORY_PATH,
    RAW_ARCHIVE_DIR,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_p0_backward_detector_probe.md"

DETECTORS = {
    "2.3.1.1.1": detect_p0_23111_columns,
    "2.3.1.1.2.1": detect_p0_231121_columns,
    "2.3.1.1.2.2": detect_p0_231122_columns,
    "2.3.1.1.2.3": detect_p0_231123_columns,
    "2.3.1.1.2.4": detect_p0_231124_columns,
    "2.3.1.1.2.5": detect_p0_231125_columns,
    "2.3.1.1.2.6": detect_p0_231126_columns,
    "2.3.1.1.2.7": detect_p0_231127_columns,
    "2.3.1.1.3": detect_p0_23113_columns,
    "2.3.1.1.4": detect_p0_23114_columns,
    "2.3.1.1.5.1": detect_p0_231151_columns,
    "2.3.1.1.5.1.1": detect_p0_2311511_columns,
    "2.3.1.1.5.1.2": detect_p0_2311512_columns,
    "2.3.1.1.5.1.3": detect_p0_2311513_columns,
    "2.3.1.1.5.1.4": detect_p0_2311514_columns,
    "2.3.1.1.5.2": detect_p0_231152_columns,
    "2.3.1.1.5.2.1": detect_p0_2311521_columns,
    "2.3.1.1.5.3": detect_p0_231153_columns,
    "2.3.1.1.5.3.1": detect_p0_2311531_columns,
    "2.3.1.1.5.3.2": detect_p0_2311532_columns,
}


def _canonical_id(source_table_id: str) -> str:
    return re.sub(r"_2-?$", "", source_table_id)


def _load_inventory() -> list[dict[str, str]]:
    with GANANCIAS_SOCIEDADES_P0_BACKWARD_INVENTORY_PATH.open(encoding="utf-8") as input_file:
        return list(csv.DictReader(input_file))


def main() -> None:
    inventory_rows = _load_inventory()
    output_rows: list[dict[str, str]] = []
    warnings: list[str] = []

    for inventory_row in inventory_rows:
        source_table_id = inventory_row["source_table_id"]
        canonical_source_table_id = _canonical_id(source_table_id)
        detector = DETECTORS.get(canonical_source_table_id)
        status = "ok"
        variable_count = ""
        variables = ""
        warning = ""

        if detector is None:
            status = "no_detector"
            warning = f"No detector is registered for canonical table {canonical_source_table_id}."
        else:
            try:
                archive_path = RAW_ARCHIVE_DIR / inventory_row["archive_filename"]
                with ZipFile(archive_path) as zip_file:
                    rows = xls_rows_from_bytes(zip_file.read(inventory_row["source_table_path"]))
                bounds = detect_xls_table_bounds(rows)
                _, variable_columns = detector(rows[bounds.header_start_row:bounds.data_start_row])
                variable_names = [variable.variable_name for variable in variable_columns]
                variable_count = str(len(variable_names))
                variables = ";".join(variable_names)
            except Exception as error:  # noqa: BLE001 - diagnostic probe must record all mismatches
                status = "detector_failed"
                warning = str(error)

        if warning:
            warnings.append(
                f"{inventory_row['fiscal_year']} {source_table_id}: {warning}"
            )
        output_rows.append(
            {
                "publication_year": inventory_row["publication_year"],
                "fiscal_year": inventory_row["fiscal_year"],
                "archive_filename": inventory_row["archive_filename"],
                "source_table_id": source_table_id,
                "canonical_source_table_id": canonical_source_table_id,
                "source_table_path": inventory_row["source_table_path"],
                "status": status,
                "variable_count": variable_count,
                "variables": variables,
                "warning": warning,
            }
        )

    GANANCIAS_SOCIEDADES_P0_BACKWARD_DETECTOR_PROBE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with GANANCIAS_SOCIEDADES_P0_BACKWARD_DETECTOR_PROBE_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=[
                "publication_year",
                "fiscal_year",
                "archive_filename",
                "source_table_id",
                "canonical_source_table_id",
                "source_table_path",
                "status",
                "variable_count",
                "variables",
                "warning",
            ],
        )
        writer.writeheader()
        writer.writerows(output_rows)

    status_counts = Counter(row["status"] for row in output_rows)
    year_status_counts = Counter((row["fiscal_year"], row["status"]) for row in output_rows)
    report = [
        "# Ganancias Sociedades P0 Backward Detector Probe",
        "",
        "Scope: compatibility of current P0 column detectors against publication years 2015-2020.",
        "",
        f"- rows_probed: {len(output_rows)}",
        f"- detector_failures_or_warnings: {len(warnings)}",
        "",
        "## Status Counts",
        "",
        "| status | rows |",
        "|---|---:|",
    ]
    for status, count in sorted(status_counts.items()):
        report.append(f"| `{status}` | {count} |")

    report.extend(["", "## Status By Fiscal Year", "", "| fiscal_year | status | rows |", "|---:|---|---:|"])
    for (fiscal_year, status), count in sorted(year_status_counts.items()):
        report.append(f"| {fiscal_year} | `{status}` | {count} |")

    if warnings:
        report.extend(["", "## Warnings", ""])
        report.extend(f"- {warning}" for warning in warnings)

    VALIDATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"wrote={GANANCIAS_SOCIEDADES_P0_BACKWARD_DETECTOR_PROBE_PATH}")
    print(f"report={REPORT_PATH}")
    print(f"rows={len(output_rows)}")
    print(f"warnings={len(warnings)}")


if __name__ == "__main__":
    main()
