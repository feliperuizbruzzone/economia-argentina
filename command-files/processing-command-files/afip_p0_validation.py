"""Reusable validation helpers for P0 Ganancias Sociedades long extracts."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
from typing import Callable, Iterable


MONETARY_TOLERANCE = Decimal("0.000001")


@dataclass(frozen=True)
class IdentityRule:
    """A monetary identity of the form target = sum(add) - sum(subtract)."""

    target: str
    add: tuple[str, ...]
    subtract: tuple[str, ...] = ()
    label: str = "component identity"
    allow_missing_fiscal_years: frozenset[str] = frozenset()


@dataclass(frozen=True)
class OverlapSpec:
    """A cross-table overlap check for variables shared with a reference table."""

    reference_rows: list[dict[str, str]]
    reference_label: str
    variables: frozenset[str]
    allowed_missing_fiscal_years: frozenset[str] = frozenset()
    allowed_missing_total_fiscal_years: frozenset[str] = frozenset()
    allowed_mismatch_keys: frozenset[tuple[str, str, str]] = frozenset()


ExtraCheck = Callable[[list[dict[str, str]]], tuple[list[str], list[str], list[str]]]


def decimal_from_text(value: str) -> Decimal | None:
    """Parse a CSV decimal value, preserving blanks as missing."""

    if value == "":
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def load_csv(path: Path) -> list[dict[str, str]]:
    """Load a CSV file as a list of dictionaries."""

    with path.open(encoding="utf-8") as input_file:
        return list(csv.DictReader(input_file))


def write_detail(
    rows: list[dict[str, str]],
    detail_path: Path,
) -> None:
    """Write variable-year row counts and TOTAL values for a long extract."""

    total_values: dict[tuple[str, str], str] = {}
    counts = Counter((row["fiscal_year"], row["variable_name"]) for row in rows)
    for row in rows:
        if row["dimension_value"] == "TOTAL":
            total_values[(row["fiscal_year"], row["variable_name"])] = row["value"]

    with detail_path.open("w", newline="", encoding="utf-8") as output_file:
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


def values_match(
    variable_name: str,
    current: str,
    reference: str,
    monetary_variables: set[str],
) -> bool:
    """Return whether two observed values match under their expected unit."""

    if variable_name in monetary_variables:
        current_decimal = decimal_from_text(current)
        reference_decimal = decimal_from_text(reference)
        if current_decimal is None or reference_decimal is None:
            return False
        return abs(current_decimal - reference_decimal) <= MONETARY_TOLERANCE
    return current == reference


def _validate_overlap(
    rows: list[dict[str, str]],
    spec: OverlapSpec,
    monetary_variables: set[str],
    presentation_only_dimensions: set[tuple[str, str]],
) -> tuple[list[str], list[str], int]:
    failures: list[str] = []
    warnings: list[str] = []
    current = {
        (row["fiscal_year"], row["dimension_value"], row["variable_name"]): row["value"]
        for row in rows
        if row["variable_name"] in spec.variables
    }
    reference = {
        (row["fiscal_year"], row["dimension_value"], row["variable_name"]): row["value"]
        for row in spec.reference_rows
        if row["variable_name"] in spec.variables
    }

    missing_from_current = []
    source_missing_year_counts: Counter[str] = Counter()
    for key in sorted(set(reference) - set(current)):
        fiscal_year, dimension_value, variable_name = key
        if fiscal_year in spec.allowed_missing_fiscal_years:
            source_missing_year_counts[fiscal_year] += 1
        elif (
            dimension_value == "TOTAL"
            and fiscal_year in spec.allowed_missing_total_fiscal_years
        ):
            warnings.append(
                f"Overlap check: source table has no TOTAL row for fiscal_year={fiscal_year}, "
                f"variable={variable_name}; reference table {spec.reference_label} has one."
            )
        elif (
            variable_name != "presentaciones_total"
            and (fiscal_year, dimension_value) in presentation_only_dimensions
        ):
            warnings.append(
                "Overlap check: source detail table has a presentation-only row "
                f"without `{variable_name}` for fiscal_year={fiscal_year}, "
                f"dimension_value={dimension_value}; reference table "
                f"{spec.reference_label} reports a value."
            )
        else:
            missing_from_current.append(key)
    for fiscal_year, count in sorted(source_missing_year_counts.items()):
        warnings.append(
            "Overlap check: source detail table is missing for "
            f"fiscal_year={fiscal_year}; reference table {spec.reference_label} "
            f"has {count} overlap rows."
        )
    missing_from_reference = sorted(set(current) - set(reference))
    if missing_from_current:
        failures.append(
            f"Overlap check: rows missing from current extract against {spec.reference_label}: "
            f"{len(missing_from_current)}"
        )
    if missing_from_reference:
        failures.append(
            f"Overlap check: rows missing from reference table {spec.reference_label}: "
            f"{len(missing_from_reference)}"
        )

    overlap_keys = set(current) & set(reference)
    mismatches = []
    for key in overlap_keys:
        if values_match(key[2], current[key], reference[key], monetary_variables):
            continue
        if key in spec.allowed_mismatch_keys:
            warnings.append(
                f"Overlap check: source value mismatch allowed for fiscal_year={key[0]}, "
                f"dimension_value={key[1]}, variable={key[2]}; current={current[key]}, "
                f"reference {spec.reference_label}={reference[key]}."
            )
            continue
        mismatches.append(key)
    if mismatches:
        failures.append(
            f"Overlap check: value mismatches with {spec.reference_label}: {len(mismatches)}"
        )

    return failures, warnings, len(overlap_keys)


def _validate_identity(
    rows: list[dict[str, str]],
    rule: IdentityRule,
) -> list[str]:
    failures: list[str] = []
    by_dimension: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(dict)
    required_variables = set(rule.add) | set(rule.subtract) | {rule.target}
    for row in rows:
        if row["variable_name"] not in required_variables:
            continue
        value = decimal_from_text(row["value"])
        if value is not None:
            by_dimension[(row["fiscal_year"], row["dimension_value"])][row["variable_name"]] = value

    for key, values in sorted(by_dimension.items()):
        fiscal_year, dimension_value = key
        missing = sorted(required_variables - set(values))
        if missing:
            if fiscal_year in rule.allow_missing_fiscal_years:
                continue
            failures.append(
                f"fiscal_year={fiscal_year} dimension_value={dimension_value}: "
                f"{rule.label} missing variables: {', '.join(missing)}"
            )
            continue

        calculated = sum(values[variable_name] for variable_name in rule.add)
        calculated -= sum(values[variable_name] for variable_name in rule.subtract)
        if abs(calculated - values[rule.target]) > MONETARY_TOLERANCE:
            failures.append(
                f"fiscal_year={fiscal_year} dimension_value={dimension_value}: "
                f"{rule.label} does not reconcile."
            )
    return failures


def validate_p0_long_extract(
    rows: list[dict[str, str]],
    *,
    table_id: str,
    report_title: str,
    scope: str,
    expected_variables: set[str],
    case_variables: set[str],
    monetary_variables: set[str],
    overlap_specs: Iterable[OverlapSpec] = (),
    identity_rules: Iterable[IdentityRule] = (),
    allowed_missing_total_fiscal_years: set[str] | None = None,
    known_missing_variables_by_year: dict[str, set[str]] | None = None,
    allow_presentation_only_value_rows: bool = False,
    extra_checks: Iterable[ExtraCheck] = (),
) -> tuple[list[str], list[str], list[str]]:
    """Validate canonical P0 long rows and return failures, warnings and report lines."""

    allowed_missing_total_fiscal_years = allowed_missing_total_fiscal_years or set()
    known_missing_variables_by_year = known_missing_variables_by_year or {}
    failures: list[str] = []
    warnings: list[str] = []
    report: list[str] = []

    if not rows:
        return [f"No rows found in the P0 {table_id} long extract."], warnings, report

    variables = {row["variable_name"] for row in rows}
    missing_variables = sorted(expected_variables - variables)
    extra_variables = sorted(variables - expected_variables)
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

    non_presentation_dimensions = {
        (row["fiscal_year"], row["dimension_value"])
        for row in rows
        if row["variable_name"] != "presentaciones_total"
    }
    presentation_only_dimensions = {
        (row["fiscal_year"], row["dimension_value"])
        for row in rows
        if row["variable_name"] == "presentaciones_total"
        and (row["fiscal_year"], row["dimension_value"]) not in non_presentation_dimensions
    }

    for row_number, row in enumerate(rows, start=2):
        label = (
            f"csv row {row_number}: fiscal_year={row['fiscal_year']} "
            f"dimension_value={row['dimension_value']} variable={row['variable_name']}"
        )
        if row["period_id"] != "P0_new_xls_detail":
            failures.append(f"{label}: period_id={row['period_id']}")
        if row["source_table_id"] != table_id:
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

        value = decimal_from_text(row["value"])
        if value is None:
            failures.append(f"{label}: value is not numeric")

        if row["variable_name"] in case_variables:
            if row["unit_original"] != "casos":
                failures.append(f"{label}: unit_original={row['unit_original']}")
            if row["value_pesos_current"]:
                failures.append(f"{label}: value_pesos_current should be blank")
        elif row["variable_name"] in monetary_variables:
            if row["unit_original"] != "millones_pesos_corrientes":
                failures.append(f"{label}: unit_original={row['unit_original']}")
            pesos = decimal_from_text(row["value_pesos_current"])
            if value is not None and pesos != value * Decimal("1000000"):
                failures.append(f"{label}: value_pesos_current does not match value")

    fiscal_years = sorted({row["fiscal_year"] for row in rows})
    for fiscal_year in fiscal_years:
        year_rows = [row for row in rows if row["fiscal_year"] == fiscal_year]
        year_variables = {row["variable_name"] for row in year_rows}
        known_missing = known_missing_variables_by_year.get(fiscal_year, set())
        observed_known_missing = sorted(known_missing - year_variables)
        if observed_known_missing:
            warnings.append(
                f"Fiscal year {fiscal_year} source-missing variables: "
                f"{', '.join(observed_known_missing)}."
            )
        missing = sorted((expected_variables - year_variables) - known_missing)
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
                    extra_dimensions = sorted(dimensions - reference_dimensions)
                    missing_dimensions = sorted(reference_dimensions - dimensions)
                    if (
                        allow_presentation_only_value_rows
                        and variable_name == "presentaciones_total"
                        and extra_dimensions
                        and not missing_dimensions
                    ):
                        warnings.append(
                            f"Fiscal year {fiscal_year} has presentation-only rows "
                            "with blank value columns: "
                            f"{', '.join(extra_dimensions)}."
                        )
                    else:
                        failures.append(
                            f"Fiscal year {fiscal_year} variable {variable_name} "
                            "does not share the reference activity dimension set."
                        )

        for variable_name in expected_variables - known_missing:
            total_rows = [
                row
                for row in year_rows
                if row["variable_name"] == variable_name
                and row["dimension_value"] == "TOTAL"
            ]
            if fiscal_year in allowed_missing_total_fiscal_years:
                if total_rows:
                    warnings.append(
                        f"Fiscal year {fiscal_year} variable {variable_name} has a TOTAL row, "
                        "although this fiscal year was marked as source-missing TOTAL."
                    )
            elif len(total_rows) != 1:
                failures.append(
                    f"Fiscal year {fiscal_year} variable {variable_name} "
                    f"has {len(total_rows)} TOTAL rows."
                )

    total_overlap_rows = 0
    for overlap_spec in overlap_specs:
        overlap_failures, overlap_warnings, overlap_rows = _validate_overlap(
            rows,
            overlap_spec,
            monetary_variables,
            presentation_only_dimensions if allow_presentation_only_value_rows else set(),
        )
        failures.extend(overlap_failures)
        warnings.extend(overlap_warnings)
        total_overlap_rows += overlap_rows

    identity_failures: list[str] = []
    for rule in identity_rules:
        identity_failures.extend(_validate_identity(rows, rule))
    failures.extend(identity_failures)

    extra_report_lines: list[str] = []
    for extra_check in extra_checks:
        extra_failures, extra_warnings, check_lines = extra_check(rows)
        failures.extend(extra_failures)
        warnings.extend(extra_warnings)
        extra_report_lines.extend(check_lines)

    counts_by_fiscal_year = Counter(row["fiscal_year"] for row in rows)
    counts_by_variable = Counter(row["variable_name"] for row in rows)
    counts_by_level = Counter(row["activity_level"] for row in rows)
    counts_by_unit = Counter(row["unit_original"] for row in rows)

    report.extend(
        [
            f"# {report_title}",
            "",
            f"Scope: {scope}",
            "",
            f"- rows_validated: {len(rows)}",
            f"- fiscal_years: {', '.join(fiscal_years)}",
            f"- variables: {', '.join(sorted(variables))}",
            f"- overlap_rows_checked: {total_overlap_rows}",
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

    if extra_report_lines:
        report.extend(["", "## Extra Checks", ""])
        report.extend(extra_report_lines)
    if failures:
        report.extend(["", "## Failures", ""])
        report.extend(f"- {failure}" for failure in failures)
    if warnings:
        report.extend(["", "## Warnings", ""])
        report.extend(f"- {warning}" for warning in warnings)

    return failures, warnings, report
