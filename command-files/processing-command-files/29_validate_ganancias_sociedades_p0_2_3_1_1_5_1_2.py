"""Validate the thirteenth P0 long extract for Ganancias Sociedades."""

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

from afip_ganancias_sociedades import P0_ACTIVITY_CREDIT_ASSETS_TABLE_ID  # noqa: E402
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_P0_231151_LONG_PATH,
    GANANCIAS_SOCIEDADES_P0_2311512_LONG_PATH,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = (
    VALIDATION_REPORTS_DIR
    / "ganancias_sociedades_p0_2_3_1_1_5_1_2_validation.md"
)
DETAIL_PATH = (
    VALIDATION_REPORTS_DIR
    / "ganancias_sociedades_p0_2_3_1_1_5_1_2_validation_counts.csv"
)

CASE_VARIABLES = {
    "presentaciones_total",
    "activo_creditos_casos",
    "activo_creditos_previsiones_casos",
    "activo_creditos_deudores_ventas_servicios_casos",
    "activo_creditos_soc_controlada_controlante_vinculada_casos",
    "activo_creditos_cuentas_particulares_socios_casos",
    "activo_creditos_otros_casos",
}
MONETARY_VARIABLES = {
    "activo_creditos",
    "activo_creditos_previsiones",
    "activo_creditos_deudores_ventas_servicios",
    "activo_creditos_soc_controlada_controlante_vinculada",
    "activo_creditos_cuentas_particulares_socios",
    "activo_creditos_otros",
}
EXPECTED_VARIABLES = CASE_VARIABLES | MONETARY_VARIABLES
OVERLAP_WITH_ASSETS_TABLE = {
    "presentaciones_total",
    "activo_creditos",
}
ADDITIVE_COMPONENT_VARIABLES = {
    "activo_creditos_deudores_ventas_servicios",
    "activo_creditos_soc_controlada_controlante_vinculada",
    "activo_creditos_cuentas_particulares_socios",
    "activo_creditos_otros",
}
SUBTRACTIVE_COMPONENT_VARIABLE = "activo_creditos_previsiones"
MONETARY_TOLERANCE = Decimal("0.000001")
KNOWN_SOURCE_MISSING_FISCAL_YEARS = {"2014", "2015", "2016"}
KNOWN_CREDIT_IDENTITY_SOURCE_ANOMALIES = {
    ("2018", "267;268"),
}


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


def _values_match(variable_name: str, current: str, reference: str) -> bool:
    if variable_name in MONETARY_VARIABLES:
        current_decimal = _decimal(current)
        reference_decimal = _decimal(reference)
        if current_decimal is None or reference_decimal is None:
            return False
        return abs(current_decimal - reference_decimal) <= MONETARY_TOLERANCE
    return current == reference


def _validate_overlap_with_assets_table(
    rows: list[dict[str, str]],
    assets_rows: list[dict[str, str]],
) -> tuple[list[str], list[str], int]:
    failures: list[str] = []
    warnings: list[str] = []
    credit_dimensions = {
        (row["fiscal_year"], row["dimension_value"])
        for row in rows
        if row["variable_name"] == "activo_creditos"
    }
    presentation_only_dimensions = {
        (row["fiscal_year"], row["dimension_value"])
        for row in rows
        if row["variable_name"] == "presentaciones_total"
        and (row["fiscal_year"], row["dimension_value"]) not in credit_dimensions
    }
    current = {
        (row["fiscal_year"], row["dimension_value"], row["variable_name"]): row["value"]
        for row in rows
        if row["variable_name"] in OVERLAP_WITH_ASSETS_TABLE
    }
    reference = {
        (row["fiscal_year"], row["dimension_value"], row["variable_name"]): row["value"]
        for row in assets_rows
        if row["variable_name"] in OVERLAP_WITH_ASSETS_TABLE
    }

    missing_from_current_all = sorted(set(reference) - set(current))
    missing_from_current = []
    source_missing_year_counts = Counter()
    for key in missing_from_current_all:
        fiscal_year, dimension_value, variable_name = key
        if fiscal_year in KNOWN_SOURCE_MISSING_FISCAL_YEARS:
            source_missing_year_counts[fiscal_year] += 1
        elif (
            variable_name == "activo_creditos"
            and (fiscal_year, dimension_value) in presentation_only_dimensions
        ):
            warnings.append(
                "Overlap check: source detail table 2.3.1.1.5.1.2 has "
                "presentation-only row without credit values for "
                f"fiscal_year={fiscal_year}, dimension_value={dimension_value}; "
                "the aggregate table 2.3.1.1.5.1 reports activo_creditos."
            )
        else:
            missing_from_current.append(key)
    for fiscal_year, count in sorted(source_missing_year_counts.items()):
        warnings.append(
            "Overlap check: table 2.3.1.1.5.1.2 is source-missing for "
            f"fiscal_year={fiscal_year}; reference table 2.3.1.1.5.1 has "
            f"{count} overlap rows."
        )
    missing_from_reference = sorted(set(current) - set(reference))
    if missing_from_current:
        failures.append(
            "Overlap check: rows missing from 2.3.1.1.5.1.2 against 2.3.1.1.5.1: "
            f"{len(missing_from_current)}"
        )
    if missing_from_reference:
        failures.append(
            "Overlap check: rows missing from 2.3.1.1.5.1: "
            f"{len(missing_from_reference)}"
        )

    overlap_keys = set(current) & set(reference)
    mismatches = [
        key
        for key in overlap_keys
        if not _values_match(key[2], current[key], reference[key])
    ]
    if mismatches:
        failures.append(f"Overlap check: value mismatches with 2.3.1.1.5.1: {len(mismatches)}")

    return failures, warnings, len(overlap_keys)


def _validate_component_identity(rows: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    by_dimension: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(dict)
    required_variables = (
        ADDITIVE_COMPONENT_VARIABLES
        | {SUBTRACTIVE_COMPONENT_VARIABLE, "activo_creditos"}
    )
    for row in rows:
        if row["variable_name"] not in required_variables:
            continue
        value = _decimal(row["value"])
        if value is not None:
            by_dimension[(row["fiscal_year"], row["dimension_value"])][row["variable_name"]] = value

    for key, values in sorted(by_dimension.items()):
        fiscal_year, dimension_value = key
        missing = sorted(required_variables - set(values))
        if missing:
            failures.append(
                f"fiscal_year={fiscal_year} dimension_value={dimension_value}: "
                f"credit-assets identity missing variables: {', '.join(missing)}"
            )
            continue

        component_sum = sum(values[variable_name] for variable_name in ADDITIVE_COMPONENT_VARIABLES)
        net_components = component_sum - values[SUBTRACTIVE_COMPONENT_VARIABLE]
        if abs(net_components - values["activo_creditos"]) > MONETARY_TOLERANCE:
            if (fiscal_year, dimension_value) in KNOWN_CREDIT_IDENTITY_SOURCE_ANOMALIES:
                warnings.append(
                    f"fiscal_year={fiscal_year} dimension_value={dimension_value}: "
                    "source anomaly; credit components net of provisions do not "
                    "sum to total credits, while the total matches 2.3.1.1.5.1."
                )
                continue
            failures.append(
                f"fiscal_year={fiscal_year} dimension_value={dimension_value}: "
                "credit-asset components net of provisions do not sum to total credits."
            )
    return failures, warnings


def _validate(
    rows: list[dict[str, str]],
    assets_rows: list[dict[str, str]],
) -> tuple[list[str], list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    report: list[str] = []

    if not rows:
        return ["No rows found in the P0 2.3.1.1.5.1.2 long extract."], warnings, report

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
        if row["source_table_id"] != P0_ACTIVITY_CREDIT_ASSETS_TABLE_ID:
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
            non_presentation_variables = sorted(
                variable_name
                for variable_name in dimension_sets
                if variable_name != "presentaciones_total"
            )
            reference_variable = non_presentation_variables[0]
            reference_dimensions = dimension_sets[reference_variable]
            for variable_name, dimensions in sorted(dimension_sets.items()):
                if dimensions != reference_dimensions:
                    extra_dimensions = sorted(dimensions - reference_dimensions)
                    missing_dimensions = sorted(reference_dimensions - dimensions)
                    if (
                        variable_name == "presentaciones_total"
                        and extra_dimensions
                        and not missing_dimensions
                    ):
                        warnings.append(
                            f"Fiscal year {fiscal_year} has presentation-only "
                            "credit rows with blank value columns: "
                            f"{', '.join(extra_dimensions)}."
                        )
                    else:
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

    (
        overlap_failures,
        overlap_warnings,
        overlap_rows,
    ) = _validate_overlap_with_assets_table(rows, assets_rows)
    identity_failures, identity_warnings = _validate_component_identity(rows)
    failures.extend(overlap_failures)
    warnings.extend(overlap_warnings)
    warnings.extend(identity_warnings)
    failures.extend(identity_failures)

    counts_by_fiscal_year = Counter(row["fiscal_year"] for row in rows)
    counts_by_variable = Counter(row["variable_name"] for row in rows)
    counts_by_level = Counter(row["activity_level"] for row in rows)
    counts_by_unit = Counter(row["unit_original"] for row in rows)

    report.extend(
        [
            "# Ganancias Sociedades P0 2.3.1.1.5.1.2 Long Extract Validation",
            "",
            "Scope: table `2.3.1.1.5.1.2`, `P0_new_xls_detail`, activity dimension.",
            "",
            f"- rows_validated: {len(rows)}",
            f"- fiscal_years: {', '.join(fiscal_years)}",
            f"- variables: {', '.join(sorted(variables))}",
            f"- overlap_rows_checked_against_2_3_1_1_5_1: {overlap_rows}",
            f"- identity_failures: {len(identity_failures)}",
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
    rows = _load_csv(GANANCIAS_SOCIEDADES_P0_2311512_LONG_PATH)
    assets_rows = _load_csv(GANANCIAS_SOCIEDADES_P0_231151_LONG_PATH)
    VALIDATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    _write_detail(rows)
    failures, warnings, report = _validate(rows, assets_rows)
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"report={REPORT_PATH}")
    print(f"detail={DETAIL_PATH}")
    print(f"failures={len(failures)}")
    print(f"warnings={len(warnings)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
