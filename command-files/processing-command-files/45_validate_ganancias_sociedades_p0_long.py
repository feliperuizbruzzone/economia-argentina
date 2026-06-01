"""Validate the assembled P0 Ganancias Sociedades long extract."""

from collections import Counter
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
    GANANCIAS_SOCIEDADES_P0_LONG_PATH,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_p0_long_validation.md"
DETAIL_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_p0_long_counts.csv"

EXPECTED_TABLE_IDS = {
    "2.3.1.1.1",
    "2.3.1.1.2.1",
    "2.3.1.1.2.2",
    "2.3.1.1.2.3",
    "2.3.1.1.2.4",
    "2.3.1.1.2.5",
    "2.3.1.1.2.6",
    "2.3.1.1.2.7",
    "2.3.1.1.3",
    "2.3.1.1.4",
    "2.3.1.1.5.1",
    "2.3.1.1.5.1.1",
    "2.3.1.1.5.1.2",
    "2.3.1.1.5.1.3",
    "2.3.1.1.5.1.4",
    "2.3.1.1.5.2",
    "2.3.1.1.5.2.1",
    "2.3.1.1.5.3",
    "2.3.1.1.5.3.1",
    "2.3.1.1.5.3.2",
}
EXPECTED_FISCAL_YEARS = {
    "2014",
    "2015",
    "2016",
    "2017",
    "2018",
    "2019",
    "2020",
    "2021",
    "2022",
}


def _load_rows() -> tuple[list[dict[str, str]], list[str]]:
    with GANANCIAS_SOCIEDADES_P0_LONG_PATH.open(encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        return list(reader), reader.fieldnames or []


def main() -> None:
    rows, fieldnames = _load_rows()
    failures: list[str] = []
    warnings: list[str] = []

    if fieldnames != long_fieldnames():
        failures.append("Assembled P0 CSV has unexpected fieldnames.")
    if not rows:
        failures.append("Assembled P0 CSV has no rows.")

    table_ids = {row["source_table_id"] for row in rows}
    missing_tables = sorted(EXPECTED_TABLE_IDS - table_ids)
    extra_tables = sorted(table_ids - EXPECTED_TABLE_IDS)
    if missing_tables:
        failures.append(f"Missing source_table_id values: {', '.join(missing_tables)}")
    if extra_tables:
        failures.append(f"Unexpected source_table_id values: {', '.join(extra_tables)}")

    fiscal_years = {row["fiscal_year"] for row in rows}
    if fiscal_years != EXPECTED_FISCAL_YEARS:
        failures.append(
            "Unexpected fiscal years: "
            f"expected={sorted(EXPECTED_FISCAL_YEARS)} observed={sorted(fiscal_years)}"
        )

    key_fields = (
        "fiscal_year",
        "source_table_id",
        "dimension_type",
        "dimension_value",
        "variable_name",
    )
    seen_keys: set[tuple[str, ...]] = set()
    duplicate_count = 0
    for row in rows:
        key = tuple(row[field] for field in key_fields)
        if key in seen_keys:
            duplicate_count += 1
        seen_keys.add(key)
        if row["period_id"] != "P0_new_xls_detail":
            failures.append(f"Unexpected period_id={row['period_id']}")
        if row["dimension_type"] != "actividad_economica":
            failures.append(f"Unexpected dimension_type={row['dimension_type']}")
        if row["classifier_period"] != "new":
            failures.append(f"Unexpected classifier_period={row['classifier_period']}")
    if duplicate_count:
        failures.append(f"Duplicate assembled canonical keys found: {duplicate_count}")

    counts_by_table = Counter(row["source_table_id"] for row in rows)
    counts_by_year = Counter(row["fiscal_year"] for row in rows)
    counts_by_variable = Counter(row["variable_name"] for row in rows)

    VALIDATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with DETAIL_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=["source_table_id", "rows"])
        writer.writeheader()
        for source_table_id, count in sorted(counts_by_table.items()):
            writer.writerow({"source_table_id": source_table_id, "rows": count})

    report = [
        "# Ganancias Sociedades P0 Long Assembly Validation",
        "",
        "Scope: assembled P0 `2.3.1.1.*` activity tables, fiscal years 2014-2022.",
        "",
        f"- rows_validated: {len(rows)}",
        f"- source_tables: {len(table_ids)}",
        f"- variables: {len(counts_by_variable)}",
        f"- failures: {len(failures)}",
        f"- warnings: {len(warnings)}",
        "",
        "## Counts By Fiscal Year",
        "",
        "| fiscal_year | rows |",
        "|---:|---:|",
    ]
    for fiscal_year, count in sorted(counts_by_year.items()):
        report.append(f"| {fiscal_year} | {count} |")

    report.extend(["", "## Counts By Source Table", "", "| source_table_id | rows |", "|---|---:|"])
    for source_table_id, count in sorted(counts_by_table.items()):
        report.append(f"| `{source_table_id}` | {count} |")

    if failures:
        report.extend(["", "## Failures", ""])
        report.extend(f"- {failure}" for failure in failures)
    if warnings:
        report.extend(["", "## Warnings", ""])
        report.extend(f"- {warning}" for warning in warnings)

    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"report={REPORT_PATH}")
    print(f"detail={DETAIL_PATH}")
    print(f"failures={len(failures)}")
    print(f"warnings={len(warnings)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
