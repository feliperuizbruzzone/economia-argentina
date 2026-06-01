"""Validate final dated analysis CSVs for AFIP Ganancias Sociedades."""

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
    GANANCIAS_SOCIEDADES_BRANCH_HARMONIZATION_DICTIONARY_PATH,
    GANANCIAS_SOCIEDADES_DATED_HARMONIZED_PATH,
    GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH,
    GANANCIAS_SOCIEDADES_P0_LONG_PATH,
    GANANCIAS_SOCIEDADES_P1_LONG_PATH,
    GANANCIAS_SOCIEDADES_P2_LONG_PATH,
    GANANCIAS_SOCIEDADES_P3_LONG_PATH,
    GANANCIAS_SOCIEDADES_P4_LONG_PATH,
    GANANCIAS_SOCIEDADES_P5_LONG_PATH,
    GANANCIAS_SOCIEDADES_P6_LONG_PATH,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_analysis_outputs_validation.md"
DETAIL_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_harmonized_branch_counts.csv"
EXPECTED_FISCAL_YEARS = {str(year) for year in range(1997, 2023)}
HARMONIZATION_FIELDNAMES = [
    "rama_homologacion_version",
    "rama_homologacion_estado",
    "rama_comun_codigo",
    "rama_comun_label",
    "rama_comun_nivel",
    "rama_detalle_homologada_codigo",
    "rama_detalle_homologada_label",
    "rama_detalle_homologada_nivel",
    "rama_homologacion_nota",
]
COMMON_BRANCH_CODES = {
    "TOTAL",
    "AGRICULTURA_PESCA",
    "MINAS_CANTERAS",
    "INDUSTRIA_MANUFACTURERA",
    "ELECTRICIDAD_GAS_AGUA",
    "CONSTRUCCION",
    "COMERCIO_HOTELES_RESTAURANTES",
    "TRANSPORTE_COMUNICACIONES",
    "FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES",
    "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS",
    "OTRAS_NO_ESPECIFICADAS",
    "NO_HOMOLOGADO",
}
COMPONENT_PATHS = (
    GANANCIAS_SOCIEDADES_P0_LONG_PATH,
    GANANCIAS_SOCIEDADES_P1_LONG_PATH,
    GANANCIAS_SOCIEDADES_P2_LONG_PATH,
    GANANCIAS_SOCIEDADES_P3_LONG_PATH,
    GANANCIAS_SOCIEDADES_P4_LONG_PATH,
    GANANCIAS_SOCIEDADES_P5_LONG_PATH,
    GANANCIAS_SOCIEDADES_P6_LONG_PATH,
)


def _count_rows(path: Path, expected_fieldnames: list[str]) -> tuple[int, set[str]]:
    fiscal_years: set[str] = set()
    rows = 0
    with path.open(encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        if reader.fieldnames != expected_fieldnames:
            raise ValueError(f"Unexpected fieldnames in {path}")
        for row in reader:
            rows += 1
            if "fiscal_year" in row:
                fiscal_years.add(row["fiscal_year"])
    return rows, fiscal_years


def _component_row_count() -> int:
    total = 0
    fieldnames = long_fieldnames()
    for path in COMPONENT_PATHS:
        rows, _years = _count_rows(path, fieldnames)
        total += rows
    return total


def _validate_harmonized_rows(
    expected_fieldnames: list[str],
) -> tuple[int, set[str], Counter[str], Counter[tuple[str, str]], list[str]]:
    failures: list[str] = []
    fiscal_years: set[str] = set()
    status_counts: Counter[str] = Counter()
    common_counts: Counter[tuple[str, str]] = Counter()
    rows = 0
    with GANANCIAS_SOCIEDADES_DATED_HARMONIZED_PATH.open(encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        if reader.fieldnames != expected_fieldnames:
            failures.append(
                "Harmonized CSV field order does not match canonical source plus "
                "harmonization columns."
            )
            return rows, fiscal_years, status_counts, common_counts, failures
        for row_number, row in enumerate(reader, start=2):
            rows += 1
            fiscal_years.add(row["fiscal_year"])
            status_counts[row["rama_homologacion_estado"]] += 1
            common_counts[(row["rama_comun_codigo"], row["rama_comun_label"])] += 1
            for field in HARMONIZATION_FIELDNAMES:
                if row[field] == "":
                    failures.append(f"csv row {row_number}: blank {field}")
            if row["rama_homologacion_estado"] == "unmapped":
                failures.append(f"csv row {row_number}: unmapped branch")
            if row["rama_comun_codigo"] == "NO_HOMOLOGADO":
                failures.append(f"csv row {row_number}: NO_HOMOLOGADO branch")
            if row["rama_comun_codigo"] not in COMMON_BRANCH_CODES:
                failures.append(
                    f"csv row {row_number}: unexpected rama_comun_codigo="
                    f"{row['rama_comun_codigo']}"
                )
    return rows, fiscal_years, status_counts, common_counts, failures


def _validate_dictionary() -> list[str]:
    failures: list[str] = []
    if not GANANCIAS_SOCIEDADES_BRANCH_HARMONIZATION_DICTIONARY_PATH.exists():
        return ["Branch harmonization dictionary was not created."]
    with GANANCIAS_SOCIEDADES_BRANCH_HARMONIZATION_DICTIONARY_PATH.open(
        encoding="utf-8",
    ) as input_file:
        reader = csv.DictReader(input_file)
        rows = 0
        for row_number, row in enumerate(reader, start=2):
            rows += 1
            if row["rama_homologacion_estado"] == "unmapped":
                failures.append(f"dictionary row {row_number}: unmapped branch")
            if row["rama_comun_codigo"] == "NO_HOMOLOGADO":
                failures.append(f"dictionary row {row_number}: NO_HOMOLOGADO branch")
            if row["fiscal_year_min"] == "" or row["fiscal_year_max"] == "":
                failures.append(f"dictionary row {row_number}: blank fiscal year bounds")
        if rows == 0:
            failures.append("Branch harmonization dictionary is empty.")
    return failures


def _write_detail(common_counts: Counter[tuple[str, str]]) -> None:
    with DETAIL_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=["rama_comun_codigo", "rama_comun_label", "rows"],
        )
        writer.writeheader()
        for (code, label), rows in sorted(common_counts.items()):
            writer.writerow(
                {"rama_comun_codigo": code, "rama_comun_label": label, "rows": rows}
            )


def main() -> None:
    """Run row-count, year-coverage, and harmonization integrity checks."""

    failures: list[str] = []
    warnings: list[str] = []
    source_fieldnames = long_fieldnames()
    harmonized_fieldnames = source_fieldnames + HARMONIZATION_FIELDNAMES

    expected_rows = _component_row_count()
    unharmonized_rows, unharmonized_years = _count_rows(
        GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH,
        source_fieldnames,
    )
    if unharmonized_rows != expected_rows:
        failures.append(
            "Unharmonized dated CSV row count differs from P0-P6 components: "
            f"observed={unharmonized_rows} expected={expected_rows}"
        )
    if unharmonized_years != EXPECTED_FISCAL_YEARS:
        failures.append(
            "Unharmonized dated CSV fiscal-year coverage differs from expected "
            f"1997-2022: missing={sorted(EXPECTED_FISCAL_YEARS - unharmonized_years)} "
            f"extra={sorted(unharmonized_years - EXPECTED_FISCAL_YEARS)}"
        )

    (
        harmonized_rows,
        harmonized_years,
        status_counts,
        common_counts,
        harmonized_failures,
    ) = _validate_harmonized_rows(harmonized_fieldnames)
    failures.extend(harmonized_failures)
    if harmonized_rows != unharmonized_rows:
        failures.append(
            "Harmonized and unharmonized dated CSV row counts differ: "
            f"harmonized={harmonized_rows} unharmonized={unharmonized_rows}"
        )
    if harmonized_years != EXPECTED_FISCAL_YEARS:
        failures.append(
            "Harmonized dated CSV fiscal-year coverage differs from expected "
            f"1997-2022: missing={sorted(EXPECTED_FISCAL_YEARS - harmonized_years)} "
            f"extra={sorted(harmonized_years - EXPECTED_FISCAL_YEARS)}"
        )
    if status_counts.get("unmapped", 0):
        failures.append(f"Unmapped harmonization rows found: {status_counts['unmapped']}")
    if not common_counts:
        failures.append("No common branch counts were produced.")

    failures.extend(_validate_dictionary())
    if harmonized_rows and harmonized_rows == unharmonized_rows:
        warnings.append(
            "Branch harmonization preserves source rows and adds common broad branches; "
            "3-digit old/new activity codes remain classifier-specific."
        )

    VALIDATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    _write_detail(common_counts)
    with REPORT_PATH.open("w", encoding="utf-8") as report_file:
        report_file.write("# Ganancias Sociedades analysis-output validation\n\n")
        report_file.write(f"- unharmonized_rows: {unharmonized_rows}\n")
        report_file.write(f"- harmonized_rows: {harmonized_rows}\n")
        report_file.write(f"- expected_component_rows: {expected_rows}\n")
        report_file.write(f"- fiscal_years: {min(harmonized_years)}-{max(harmonized_years)}\n")
        report_file.write(f"- status_counts: {dict(sorted(status_counts.items()))}\n")
        report_file.write(f"- detail_counts_csv: {DETAIL_PATH}\n\n")
        report_file.write(f"## Failures ({len(failures)})\n")
        for failure in failures:
            report_file.write(f"- {failure}\n")
        report_file.write(f"\n## Warnings ({len(warnings)})\n")
        for warning in warnings:
            report_file.write(f"- {warning}\n")

    print(f"report={REPORT_PATH}")
    print(f"detail={DETAIL_PATH}")
    print(f"failures={len(failures)}")
    print(f"warnings={len(warnings)}")
    print(f"unharmonized_rows={unharmonized_rows}")
    print(f"harmonized_rows={harmonized_rows}")
    print(f"status_counts={dict(sorted(status_counts.items()))}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
