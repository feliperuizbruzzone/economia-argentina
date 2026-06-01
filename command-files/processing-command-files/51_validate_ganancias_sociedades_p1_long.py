"""Validate the P1 Ganancias Sociedades HTML long extract."""

from collections import Counter, defaultdict
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import sys


sys.dont_write_bytecode = True

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
PROCESSING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CONFIG_DIR))
sys.path.insert(0, str(PROCESSING_DIR))

from afip_ganancias_sociedades import P1_ACTIVITY_TABLE_IDS, normalize_text  # noqa: E402
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_P1_INVENTORY_PATH,
    GANANCIAS_SOCIEDADES_P1_LONG_PATH,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_p1_long_validation.md"
DETAIL_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_p1_long_counts.csv"
MONETARY_TOLERANCE = Decimal("0.000001")


def _decimal(value: str) -> Decimal | None:
    if value == "":
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as input_file:
        return list(csv.DictReader(input_file))


def _write_detail(rows: list[dict[str, str]]) -> None:
    counts = Counter((row["source_table_id"], row["variable_name"]) for row in rows)
    with DETAIL_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=["source_table_id", "variable_name", "rows"],
        )
        writer.writeheader()
        for source_table_id, variable_name in sorted(counts):
            writer.writerow(
                {
                    "source_table_id": source_table_id,
                    "variable_name": variable_name,
                    "rows": counts[(source_table_id, variable_name)],
                }
            )


def _validate_inventory(inventory_rows: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    expected_tables = set(P1_ACTIVITY_TABLE_IDS)
    observed_tables = {row["source_table_id"] for row in inventory_rows}
    if observed_tables != expected_tables:
        failures.append(
            "Inventory source tables differ from expected P1 tables: "
            f"missing={sorted(expected_tables - observed_tables)}, "
            f"extra={sorted(observed_tables - expected_tables)}"
        )
    if len(inventory_rows) != len(P1_ACTIVITY_TABLE_IDS):
        failures.append(f"Inventory row count is {len(inventory_rows)}, expected 13.")

    for row in inventory_rows:
        label = f"inventory table={row['source_table_id']}"
        if row["period_id"] != "P1_new_html_detail":
            failures.append(f"{label}: period_id={row['period_id']}")
        if row["publication_year"] != "2014":
            failures.append(f"{label}: publication_year={row['publication_year']}")
        if row["fiscal_year"] != "2013":
            failures.append(f"{label}: fiscal_year={row['fiscal_year']}")
        if row["format"] != "html_excel":
            failures.append(f"{label}: format={row['format']}")
        if row["dimension_type"] != "actividad_economica":
            failures.append(f"{label}: dimension_type={row['dimension_type']}")
        if row["unit_original"] != "millones_pesos_corrientes":
            failures.append(f"{label}: unit_original={row['unit_original']}")
        if row["has_activity_3digit"] != "True":
            warnings.append(f"{label}: no 3-digit activity detail flag.")
        if not row["source_table_path"].endswith("_2_archivos/sheet001.htm"):
            warnings.append(
                f"{label}: source path is not a `_2` detail sheet: "
                f"{row['source_table_path']}"
            )
        if row["notes"] and "bounds_detection_failed" in row["notes"]:
            failures.append(f"{label}: {row['notes']}")
    return failures, warnings


def _validate_rows(
    rows: list[dict[str, str]],
    inventory_rows: list[dict[str, str]],
) -> tuple[list[str], list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    report: list[str] = []
    expected_tables = set(P1_ACTIVITY_TABLE_IDS)

    if not rows:
        return ["No rows found in the P1 long extract."], warnings, report

    inventory_failures, inventory_warnings = _validate_inventory(inventory_rows)
    failures.extend(inventory_failures)
    warnings.extend(inventory_warnings)

    observed_tables = {row["source_table_id"] for row in rows}
    if observed_tables != expected_tables:
        failures.append(
            "Extract source tables differ from expected P1 tables: "
            f"missing={sorted(expected_tables - observed_tables)}, "
            f"extra={sorted(observed_tables - expected_tables)}"
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
    if duplicate_count:
        failures.append(f"Duplicate canonical keys found: {duplicate_count}")

    for row_number, row in enumerate(rows, start=2):
        label = (
            f"csv row {row_number}: table={row['source_table_id']} "
            f"dimension_value={row['dimension_value']} variable={row['variable_name']}"
        )
        if row["period_id"] != "P1_new_html_detail":
            failures.append(f"{label}: period_id={row['period_id']}")
        if row["publication_year"] != "2014":
            failures.append(f"{label}: publication_year={row['publication_year']}")
        if row["fiscal_year"] != "2013":
            failures.append(f"{label}: fiscal_year={row['fiscal_year']}")
        if row["source_table_id"] not in expected_tables:
            failures.append(f"{label}: unexpected source_table_id")
        if row["dimension_type"] != "actividad_economica":
            failures.append(f"{label}: dimension_type={row['dimension_type']}")
        if row["classifier_period"] != "new":
            failures.append(f"{label}: classifier_period={row['classifier_period']}")
        if "ESTRUCTURA PORCENTUAL" in normalize_text(row["activity_label_original"]):
            failures.append(f"{label}: percentage-section row was extracted")
        if row["activity_level"] == "other":
            failures.append(f"{label}: unresolved activity_level=other")
        if row["activity_level"] == "activity_3digit" and not re.match(
            r"^[0-9]{3}(;[0-9]{3})*$",
            row["activity_code"],
        ):
            failures.append(f"{label}: malformed activity_code={row['activity_code']}")
        if row["activity_level"] == "section" and not re.match(r"^[A-Z]$", row["activity_code"]):
            failures.append(f"{label}: malformed section code={row['activity_code']}")

        value = _decimal(row["value"])
        if value is None:
            failures.append(f"{label}: value is not numeric")
        if row["unit_original"] == "casos":
            if row["value_pesos_current"]:
                failures.append(f"{label}: value_pesos_current should be blank")
        elif row["unit_original"] == "millones_pesos_corrientes":
            pesos = _decimal(row["value_pesos_current"])
            if value is not None and (
                pesos is None or abs(pesos - value * Decimal("1000000")) > MONETARY_TOLERANCE
            ):
                failures.append(f"{label}: value_pesos_current does not match value")
        else:
            failures.append(f"{label}: unexpected unit_original={row['unit_original']}")

    counts_by_table = Counter(row["source_table_id"] for row in rows)
    counts_by_level = Counter(row["activity_level"] for row in rows)
    counts_by_unit = Counter(row["unit_original"] for row in rows)
    counts_by_variable = Counter(row["variable_name"] for row in rows)
    variables_by_table: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        variables_by_table[row["source_table_id"]].add(row["variable_name"])

    report.extend(
        [
            "# Ganancias Sociedades P1 Long Validation",
            "",
            "Scope: `P1_new_html_detail`, publication year 2014, fiscal year 2013.",
            "",
            f"- rows_validated: {len(rows)}",
            f"- source_tables: {len(observed_tables)}",
            f"- variables: {len(counts_by_variable)}",
            f"- failures: {len(failures)}",
            f"- warnings: {len(warnings)}",
            "",
            "## Counts By Source Table",
            "",
            "| source_table_id | rows | variables |",
            "|---|---:|---:|",
        ]
    )
    for source_table_id in sorted(counts_by_table):
        report.append(
            f"| `{source_table_id}` | {counts_by_table[source_table_id]} | "
            f"{len(variables_by_table[source_table_id])} |"
        )

    report.extend(["", "## Counts By Activity Level", "", "| activity_level | rows |", "|---|---:|"])
    for activity_level, count in sorted(counts_by_level.items()):
        report.append(f"| `{activity_level}` | {count} |")

    report.extend(["", "## Counts By Unit", "", "| unit_original | rows |", "|---|---:|"])
    for unit_original, count in sorted(counts_by_unit.items()):
        report.append(f"| `{unit_original}` | {count} |")

    if failures:
        report.extend(["", "## Failures", ""])
        report.extend(f"- {failure}" for failure in failures)
    if warnings:
        report.extend(["", "## Warnings", ""])
        report.extend(f"- {warning}" for warning in warnings)

    return failures, warnings, report


def main() -> None:
    rows = _load_csv(GANANCIAS_SOCIEDADES_P1_LONG_PATH)
    inventory_rows = _load_csv(GANANCIAS_SOCIEDADES_P1_INVENTORY_PATH)
    VALIDATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    _write_detail(rows)
    failures, warnings, report = _validate_rows(rows, inventory_rows)
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"report={REPORT_PATH}")
    print(f"detail={DETAIL_PATH}")
    print(f"failures={len(failures)}")
    print(f"warnings={len(warnings)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
