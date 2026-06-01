"""Validate the seventh P0 long extract for Ganancias Sociedades."""

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

from afip_ganancias_sociedades import P0_ACTIVITY_OTHER_RESULTS_TABLE_ID  # noqa: E402
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_P0_23111_LONG_PATH,
    GANANCIAS_SOCIEDADES_P0_231126_LONG_PATH,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = (
    VALIDATION_REPORTS_DIR
    / "ganancias_sociedades_p0_2_3_1_1_2_6_validation.md"
)
DETAIL_PATH = (
    VALIDATION_REPORTS_DIR
    / "ganancias_sociedades_p0_2_3_1_1_2_6_validation_counts.csv"
)

CASE_VARIABLES = {
    "presentaciones_total",
    "resultado_inversiones_permanentes_utilidad_casos",
    "resultado_inversiones_permanentes_quebranto_casos",
    "resultados_financieros_utilidad_casos",
    "resultados_financieros_quebranto_casos",
    "resultados_contratos_derivados_utilidad_casos",
    "resultados_contratos_derivados_quebranto_casos",
    "otros_ingresos_egresos_utilidad_casos",
    "otros_ingresos_egresos_quebranto_casos",
}
MONETARY_VARIABLES = {
    "resultado_inversiones_permanentes_utilidad",
    "resultado_inversiones_permanentes_quebranto",
    "resultados_financieros_utilidad",
    "resultados_financieros_quebranto",
    "resultados_contratos_derivados_utilidad",
    "resultados_contratos_derivados_quebranto",
    "otros_ingresos_egresos_utilidad",
    "otros_ingresos_egresos_quebranto",
}
EXPECTED_VARIABLES = CASE_VARIABLES | MONETARY_VARIABLES
OVERLAP_WITH_SUMMARY_TABLE = {"presentaciones_total"}
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
    total_values: dict[tuple[str, str], str] = {}
    counts = Counter((row["fiscal_year"], row["variable_name"]) for row in rows)
    for row in rows:
        if row["dimension_value"] == "TOTAL":
            total_values[(row["fiscal_year"], row["variable_name"])] = row["value"]

    with DETAIL_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=["fiscal_year", "variable_name", "rows", "total_value"],
        )
        writer.writeheader()
        for fiscal_year, variable_name in sorted(counts):
            writer.writerow(
                {
                    "fiscal_year": fiscal_year,
                    "variable_name": variable_name,
                    "rows": counts[(fiscal_year, variable_name)],
                    "total_value": total_values.get((fiscal_year, variable_name), ""),
                }
            )


def _validate_overlap_with_summary_table(
    rows: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
) -> tuple[list[str], int]:
    failures: list[str] = []
    current = {
        (row["fiscal_year"], row["dimension_value"], row["variable_name"]): row["value"]
        for row in rows
        if row["variable_name"] in OVERLAP_WITH_SUMMARY_TABLE
    }
    reference = {
        (row["fiscal_year"], row["dimension_value"], row["variable_name"]): row["value"]
        for row in summary_rows
        if row["variable_name"] in OVERLAP_WITH_SUMMARY_TABLE
    }

    missing_from_current = sorted(set(reference) - set(current))
    missing_from_reference = sorted(set(current) - set(reference))
    if missing_from_current:
        failures.append(
            "Overlap check: rows missing from 2.3.1.1.2.6 against 2.3.1.1.1: "
            f"{len(missing_from_current)}"
        )
    if missing_from_reference:
        failures.append(
            "Overlap check: rows missing from 2.3.1.1.1: "
            f"{len(missing_from_reference)}"
        )

    overlap_keys = set(current) & set(reference)
    mismatches = [
        key
        for key in overlap_keys
        if current[key] != reference[key]
    ]
    if mismatches:
        failures.append(f"Overlap check: value mismatches with 2.3.1.1.1: {len(mismatches)}")

    return failures, len(overlap_keys)


def _validate(
    rows: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
) -> tuple[list[str], list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    report: list[str] = []

    if not rows:
        return ["No rows found in the P0 2.3.1.1.2.6 long extract."], warnings, report

    variables = {row["variable_name"] for row in rows}
    missing_variables = sorted(EXPECTED_VARIABLES - variables)
    extra_variables = sorted(variables - EXPECTED_VARIABLES)
    if missing_variables:
        failures.append(f"Missing variables: {', '.join(missing_variables)}")
    if extra_variables:
        failures.append(f"Unexpected variables: {', '.join(extra_variables)}")

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
            f"csv row {row_number}: fiscal_year={row['fiscal_year']} "
            f"dimension_value={row['dimension_value']} variable={row['variable_name']}"
        )
        if row["period_id"] != "P0_new_xls_detail":
            failures.append(f"{label}: period_id={row['period_id']}")
        if row["source_table_id"] != P0_ACTIVITY_OTHER_RESULTS_TABLE_ID:
            failures.append(f"{label}: source_table_id={row['source_table_id']}")
        if row["dimension_type"] != "actividad_economica":
            failures.append(f"{label}: dimension_type={row['dimension_type']}")
        if row["classifier_period"] != "new":
            failures.append(f"{label}: classifier_period={row['classifier_period']}")
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

        if row["variable_name"] in CASE_VARIABLES:
            if row["unit_original"] != "casos":
                failures.append(f"{label}: unit_original={row['unit_original']}")
            if row["value_pesos_current"]:
                failures.append(f"{label}: value_pesos_current should be blank")
        elif row["variable_name"] in MONETARY_VARIABLES:
            if row["unit_original"] != "millones_pesos_corrientes":
                failures.append(f"{label}: unit_original={row['unit_original']}")
            pesos = _decimal(row["value_pesos_current"])
            if value is not None and pesos != value * Decimal("1000000"):
                failures.append(f"{label}: value_pesos_current does not match value")

    fiscal_years = sorted({row["fiscal_year"] for row in rows})
    for fiscal_year in fiscal_years:
        year_rows = [row for row in rows if row["fiscal_year"] == fiscal_year]
        year_variables = {row["variable_name"] for row in year_rows}
        missing = sorted(EXPECTED_VARIABLES - year_variables)
        if missing:
            failures.append(f"Fiscal year {fiscal_year} missing variables: {', '.join(missing)}")

        dimension_sets: dict[str, set[str]] = defaultdict(set)
        for row in year_rows:
            dimension_sets[row["variable_name"]].add(row["dimension_value"])
        if dimension_sets:
            reference_variable = sorted(dimension_sets)[0]
            reference_dimensions = dimension_sets[reference_variable]
            for variable_name, dimensions in sorted(dimension_sets.items()):
                if dimensions != reference_dimensions:
                    failures.append(
                        f"Fiscal year {fiscal_year} variable {variable_name} "
                        "does not share the reference activity dimension set."
                    )

        for variable_name in EXPECTED_VARIABLES:
            total_rows = [
                row
                for row in year_rows
                if row["variable_name"] == variable_name
                and row["dimension_value"] == "TOTAL"
            ]
            if len(total_rows) != 1:
                failures.append(
                    f"Fiscal year {fiscal_year} variable {variable_name} "
                    f"has {len(total_rows)} TOTAL rows."
                )

    overlap_failures, overlap_rows = _validate_overlap_with_summary_table(rows, summary_rows)
    failures.extend(overlap_failures)

    counts_by_fiscal_year = Counter(row["fiscal_year"] for row in rows)
    counts_by_variable = Counter(row["variable_name"] for row in rows)
    counts_by_level = Counter(row["activity_level"] for row in rows)
    counts_by_unit = Counter(row["unit_original"] for row in rows)

    report.extend(
        [
            "# Ganancias Sociedades P0 2.3.1.1.2.6 Long Extract Validation",
            "",
            "Scope: table `2.3.1.1.2.6`, `P0_new_xls_detail`, activity dimension.",
            "",
            f"- rows_validated: {len(rows)}",
            f"- fiscal_years: {', '.join(fiscal_years)}",
            f"- variables: {', '.join(sorted(variables))}",
            f"- overlap_rows_checked_against_2_3_1_1_1: {overlap_rows}",
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

    report.extend(["", "## Counts By Variable", "", "| variable_name | rows |", "|---|---:|"])
    for variable_name, count in sorted(counts_by_variable.items()):
        report.append(f"| `{variable_name}` | {count} |")

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
    rows = _load_csv(GANANCIAS_SOCIEDADES_P0_231126_LONG_PATH)
    summary_rows = _load_csv(GANANCIAS_SOCIEDADES_P0_23111_LONG_PATH)
    VALIDATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    _write_detail(rows)
    failures, warnings, report = _validate(rows, summary_rows)
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"report={REPORT_PATH}")
    print(f"detail={DETAIL_PATH}")
    print(f"failures={len(failures)}")
    print(f"warnings={len(warnings)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
