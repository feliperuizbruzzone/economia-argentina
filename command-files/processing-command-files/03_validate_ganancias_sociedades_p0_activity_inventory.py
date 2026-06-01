"""Validate the P0 activity-table inventory for Ganancias Sociedades."""

from collections import Counter
import csv
from pathlib import Path
import re
import sys


sys.dont_write_bytecode = True

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
sys.path.insert(0, str(CONFIG_DIR))

from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_INVENTORY_PATH,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = (
    VALIDATION_REPORTS_DIR
    / "ganancias_sociedades_p0_activity_inventory_validation.md"
)
DETAIL_PATH = (
    VALIDATION_REPORTS_DIR
    / "ganancias_sociedades_p0_activity_inventory_validation.csv"
)


def _truthy(value: str) -> bool:
    return value.strip().lower() == "true"


def _is_valid_first_data_label(value: str) -> bool:
    label = value.strip()
    return label == "TOTAL" or bool(re.match(r"^[A-Z] - ", label))


def _load_rows() -> list[dict[str, str]]:
    with GANANCIAS_SOCIEDADES_INVENTORY_PATH.open(encoding="utf-8") as input_file:
        return list(csv.DictReader(input_file))


def _write_detail(rows: list[dict[str, str]]) -> None:
    fields = [
        "publication_year",
        "fiscal_year",
        "source_table_id",
        "table_family",
        "dimension_type",
        "universe",
        "unit_original",
        "has_activity_section",
        "has_activity_3digit",
        "header_start_row_zero_based",
        "data_start_row_zero_based",
        "first_data_label",
        "notes",
    ]
    with DETAIL_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fields})


def _validate(rows: list[dict[str, str]]) -> tuple[list[str], list[str], list[str]]:
    """Return hard failures, warnings and report lines for the P0 activity inventory."""

    all_activity_rows = [
        row
        for row in rows
        if row["period_id"] == "P0_new_xls_detail"
        and row["source_table_id"].startswith("2.3.1.1.")
    ]
    continuation_rows = [row for row in all_activity_rows if _truthy(row["is_continuation"])]
    activity_rows = [row for row in all_activity_rows if not _truthy(row["is_continuation"])]
    failures: list[str] = []
    warnings: list[str] = []
    report: list[str] = []

    if not activity_rows:
        return ["No P0 activity rows found for source_table_id prefix 2.3.1.1."], warnings, report

    fiscal_years = sorted({row["fiscal_year"] for row in activity_rows})
    latest_fiscal_year = fiscal_years[-1]
    reference_ids = {
        row["source_table_id"]
        for row in activity_rows
        if row["fiscal_year"] == latest_fiscal_year
    }

    counts_by_fiscal_year = Counter(row["fiscal_year"] for row in activity_rows)
    for fiscal_year in fiscal_years:
        ids = {
            row["source_table_id"]
            for row in activity_rows
            if row["fiscal_year"] == fiscal_year
        }
        missing = sorted(reference_ids - ids)
        extra = sorted(ids - reference_ids)
        if missing:
            warnings.append(f"Fiscal year {fiscal_year} is missing table ids: {', '.join(missing)}")
        if extra:
            failures.append(f"Fiscal year {fiscal_year} has extra table ids: {', '.join(extra)}")
        if counts_by_fiscal_year[fiscal_year] != len(reference_ids):
            warnings.append(
                f"Fiscal year {fiscal_year} has {counts_by_fiscal_year[fiscal_year]} rows; "
                f"expected {len(reference_ids)}."
            )

    for row in activity_rows:
        label = f"{row['fiscal_year']} {row['source_table_id']}"
        if row["dimension_type"] != "actividad_economica":
            failures.append(f"{label}: dimension_type={row['dimension_type']}")
        if row["unit_original"] != "millones_pesos_corrientes":
            failures.append(f"{label}: unit_original={row['unit_original']}")
        if row["notes"]:
            failures.append(f"{label}: notes={row['notes']}")
        if not row["header_start_row_zero_based"]:
            failures.append(f"{label}: missing header_start_row_zero_based")
        if not row["data_start_row_zero_based"]:
            failures.append(f"{label}: missing data_start_row_zero_based")
        if not _is_valid_first_data_label(row["first_data_label"]):
            failures.append(f"{label}: first_data_label={row['first_data_label']}")
        elif row["first_data_label"] != "TOTAL":
            warnings.append(
                f"{label}: no TOTAL row detected; data begins at {row['first_data_label']}"
            )
        if not _truthy(row["has_activity_section"]):
            failures.append(f"{label}: has_activity_section is false")
        if not _truthy(row["has_activity_3digit"]):
            failures.append(f"{label}: has_activity_3digit is false")
        if row["table_family"] == "unknown":
            warnings.append(f"{label}: table_family is unknown")
        if "Impuesto a las Ganancias Sociedades" not in row["source_table_title"]:
            failures.append(f"{label}: title does not identify Ganancias Sociedades")

    table_family_counts = Counter(row["table_family"] for row in activity_rows)
    universe_counts = Counter(row["universe"] for row in activity_rows)
    if continuation_rows:
        warnings.append(
            f"Ignored {len(continuation_rows)} continuation-suffix rows in validation; "
            "canonical extraction uses the base table ids."
        )

    report.extend(
        [
            "# Ganancias Sociedades P0 Activity Inventory Validation",
            "",
            "Scope: `P0_new_xls_detail`, tables with source_table_id prefix `2.3.1.1.`.",
            "",
            f"- rows_validated: {len(activity_rows)}",
            f"- fiscal_years: {', '.join(fiscal_years)}",
            f"- reference_fiscal_year: {latest_fiscal_year}",
            f"- tables_per_fiscal_year: {len(reference_ids)}",
            f"- failures: {len(failures)}",
            f"- warnings: {len(warnings)}",
            "",
            "## Counts By Fiscal Year",
            "",
            "| fiscal_year | rows |",
            "|---:|---:|",
        ]
    )
    for fiscal_year in fiscal_years:
        report.append(f"| {fiscal_year} | {counts_by_fiscal_year[fiscal_year]} |")

    report.extend(["", "## Table Families", "", "| table_family | rows |", "|---|---:|"])
    for table_family, count in sorted(table_family_counts.items()):
        report.append(f"| `{table_family}` | {count} |")

    report.extend(["", "## Universes", "", "| universe | rows |", "|---|---:|"])
    for universe, count in sorted(universe_counts.items()):
        report.append(f"| `{universe}` | {count} |")

    report.extend(["", "## Reference Table IDs", ""])
    for table_id in sorted(reference_ids):
        report.append(f"- `{table_id}`")

    if failures:
        report.extend(["", "## Failures", ""])
        report.extend(f"- {failure}" for failure in failures)
    if warnings:
        report.extend(["", "## Warnings", ""])
        report.extend(f"- {warning}" for warning in warnings)

    return failures, warnings, report


def main() -> None:
    rows = _load_rows()
    activity_rows = [
        row
        for row in rows
        if row["period_id"] == "P0_new_xls_detail"
        and row["source_table_id"].startswith("2.3.1.1.")
    ]
    VALIDATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    _write_detail(activity_rows)
    failures, warnings, report = _validate(rows)
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"report={REPORT_PATH}")
    print(f"detail={DETAIL_PATH}")
    print(f"failures={len(failures)}")
    print(f"warnings={len(warnings)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
