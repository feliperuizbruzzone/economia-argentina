"""Validate the P5 Ganancias Sociedades legacy CAB/XLS long extract."""

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

from afip_ganancias_sociedades import (  # noqa: E402
    P5_ACTIVITY_TABLE_IDS_1999_2000,
    P5_ACTIVITY_TABLE_IDS_2001,
    normalize_text,
)
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_P5_INVENTORY_PATH,
    GANANCIAS_SOCIEDADES_P5_LONG_PATH,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_p5_long_validation.md"
DETAIL_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_p5_long_counts.csv"
MONETARY_TOLERANCE = Decimal("0.000001")
EXPECTED_PUBLICATION_YEAR = "2002"
EXPECTED_FISCAL_YEARS = ("1999", "2000", "2001")


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


def _expected_inventory_pairs() -> set[tuple[str, str]]:
    expected: set[tuple[str, str]] = set()
    for fiscal_year in ("1999", "2000"):
        for table_id in P5_ACTIVITY_TABLE_IDS_1999_2000:
            expected.add((fiscal_year, table_id))
    for table_id in P5_ACTIVITY_TABLE_IDS_2001:
        expected.add(("2001", table_id))
    return expected


def _validate_inventory(inventory_rows: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    expected_pairs = _expected_inventory_pairs()
    observed_pairs = {(row["fiscal_year"], row["source_table_id"]) for row in inventory_rows}
    if observed_pairs != expected_pairs:
        missing = sorted(expected_pairs - observed_pairs)
        extra = sorted(observed_pairs - expected_pairs)
        if missing:
            failures.append(f"Inventory missing expected P5 fiscal/table pairs: {missing}")
        if extra:
            failures.append(f"Inventory has unexpected P5 fiscal/table pairs: {extra}")

    for row in inventory_rows:
        label = f"inventory fiscal={row['fiscal_year']} table={row['source_table_id']}"
        if row["period_id"] != "P5_old_cab_xls_detail_legacy_numbering":
            failures.append(f"{label}: period_id={row['period_id']}")
        if row["publication_year"] != EXPECTED_PUBLICATION_YEAR:
            failures.append(f"{label}: publication_year={row['publication_year']}")
        if row["fiscal_year"] not in EXPECTED_FISCAL_YEARS:
            failures.append(f"{label}: unexpected fiscal_year={row['fiscal_year']}")
        if row["format"] != "xls_in_cab":
            failures.append(f"{label}: format={row['format']}")
        if row["dimension_type"] != "actividad_economica":
            failures.append(f"{label}: dimension_type={row['dimension_type']}")
        if row["unit_original"] != "miles_pesos_corrientes":
            failures.append(f"{label}: unit_original={row['unit_original']}")
        if row["has_activity_3digit"] != "True":
            warnings.append(f"{label}: no 3-digit activity detail flag.")
        if not row["source_table_path"].startswith("AFIP.CAB/"):
            failures.append(f"{label}: source path is not nested under AFIP.CAB.")
        if not row["source_table_path"].endswith("_2.xls"):
            warnings.append(f"{label}: source path is not an `_2.xls` detail file.")
        if "canonical_latest_publication_2002" not in row["notes"]:
            failures.append(f"{label}: latest-publication rule note is missing.")
        if "legacy_four_table_schema" in row["notes"]:
            warnings.append(f"{label}: legacy four-table schema for fiscal 1999-2000.")
        if "supersedes_publication_2000_2001_duplicates" in row["notes"]:
            warnings.append(f"{label}: publication 2002 selected over older duplicate releases.")
        if "summary_count_is_ganancia_neta_imponible" in row["notes"]:
            warnings.append(f"{label}: summary count is `con ganancia neta imponible`.")
        if "old_result_final_ejercicio_mapped_to_resultado_contable" in row["notes"]:
            warnings.append(f"{label}: old final-result label mapped to accounting result.")
        if "old_tax_quebranto_mapped_to_resultado_impositivo_perdida" in row["notes"]:
            warnings.append(f"{label}: old quebranto label mapped to tax-result loss.")
        if "old_aggregate_balance_sheet" in row["notes"]:
            warnings.append(f"{label}: aggregate balance sheet, no asset/liability components.")
        if "legacy_numbering_expanded_2001" in row["notes"]:
            warnings.append(f"{label}: fiscal 2001 uses expanded legacy numbering.")
        if "old_costs_otros_component" in row["notes"]:
            warnings.append(f"{label}: reports `OTROS` cost component.")
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

    if not rows:
        return ["No rows found in the P5 long extract."], warnings, report

    inventory_failures, inventory_warnings = _validate_inventory(inventory_rows)
    failures.extend(inventory_failures)
    warnings.extend(inventory_warnings)

    inventory_pairs = {(row["fiscal_year"], row["source_table_id"]) for row in inventory_rows}
    extract_pairs = {(row["fiscal_year"], row["source_table_id"]) for row in rows}
    if extract_pairs != inventory_pairs:
        failures.append(
            "Extract fiscal/table pairs differ from inventory: "
            f"missing={sorted(inventory_pairs - extract_pairs)}, "
            f"extra={sorted(extract_pairs - inventory_pairs)}"
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

    variables_by_table_year: dict[tuple[str, str], set[str]] = defaultdict(set)
    variables_by_dimension: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    label_by_dimension: dict[tuple[str, str, str], str] = {}
    for row in rows:
        table_year = (row["fiscal_year"], row["source_table_id"])
        dimension_key = (row["fiscal_year"], row["source_table_id"], row["dimension_value"])
        variables_by_table_year[table_year].add(row["variable_name"])
        variables_by_dimension[dimension_key].add(row["variable_name"])
        label_by_dimension[dimension_key] = row["activity_label_original"]

    for dimension_key, variable_names in sorted(variables_by_dimension.items()):
        fiscal_year, source_table_id, dimension_value = dimension_key
        expected_count = len(variables_by_table_year[(fiscal_year, source_table_id)])
        if len(variable_names) < expected_count:
            warnings.append(
                "Sparse source values: "
                f"fiscal_year={fiscal_year} table={source_table_id} "
                f"dimension={dimension_value} label={label_by_dimension[dimension_key]} "
                f"variables_observed={len(variable_names)} table_year_variables={expected_count}"
            )

    for row_number, row in enumerate(rows, start=2):
        label = (
            f"csv row {row_number}: fiscal={row['fiscal_year']} "
            f"table={row['source_table_id']} dimension_value={row['dimension_value']} "
            f"variable={row['variable_name']}"
        )
        if row["period_id"] != "P5_old_cab_xls_detail_legacy_numbering":
            failures.append(f"{label}: period_id={row['period_id']}")
        if row["publication_year"] != EXPECTED_PUBLICATION_YEAR:
            failures.append(f"{label}: publication_year={row['publication_year']}")
        if (row["fiscal_year"], row["source_table_id"]) not in inventory_pairs:
            failures.append(f"{label}: unexpected fiscal/table pair")
        if row["dimension_type"] != "actividad_economica":
            failures.append(f"{label}: dimension_type={row['dimension_type']}")
        if row["classifier_period"] != "old":
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
        elif row["unit_original"] == "miles_pesos_corrientes":
            pesos = _decimal(row["value_pesos_current"])
            if value is not None and (
                pesos is None or abs(pesos - value * Decimal("1000")) > MONETARY_TOLERANCE
            ):
                failures.append(f"{label}: value_pesos_current does not match value")
        else:
            failures.append(f"{label}: unexpected unit_original={row['unit_original']}")

    counts_by_table = Counter(row["source_table_id"] for row in rows)
    counts_by_year = Counter(row["fiscal_year"] for row in rows)
    counts_by_level = Counter(row["activity_level"] for row in rows)
    counts_by_unit = Counter(row["unit_original"] for row in rows)
    counts_by_variable = Counter(row["variable_name"] for row in rows)
    variables_by_table: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        variables_by_table[row["source_table_id"]].add(row["variable_name"])

    report.extend(
        [
            "# Ganancias Sociedades P5 Long Validation",
            "",
            "Scope: `P5_old_cab_xls_detail_legacy_numbering`, canonical publication year 2002, fiscal years 1999-2001.",
            "",
            f"- rows_validated: {len(rows)}",
            f"- fiscal_table_pairs: {len(extract_pairs)}",
            f"- variables: {len(counts_by_variable)}",
            f"- failures: {len(failures)}",
            f"- warnings: {len(warnings)}",
            "",
            "## Counts By Fiscal Year",
            "",
            "| fiscal_year | rows |",
            "|---|---:|",
        ]
    )
    for fiscal_year in sorted(counts_by_year):
        report.append(f"| `{fiscal_year}` | {counts_by_year[fiscal_year]} |")

    report.extend(["", "## Counts By Source Table", "", "| source_table_id | rows | variables |", "|---|---:|---:|"])
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
    rows = _load_csv(GANANCIAS_SOCIEDADES_P5_LONG_PATH)
    inventory_rows = _load_csv(GANANCIAS_SOCIEDADES_P5_INVENTORY_PATH)
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
