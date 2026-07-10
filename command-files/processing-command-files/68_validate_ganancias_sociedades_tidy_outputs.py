"""Validate the analytic AFIP Ganancias Sociedades panel and dictionaries."""

from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sys


sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR.parents[0] / "config"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(CONFIG_DIR))

from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_ACTIVITY_DICTIONARY_PATH,
    GANANCIAS_SOCIEDADES_DATED_HARMONIZED_PATH,
    GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH,
    GANANCIAS_SOCIEDADES_SOURCE_DICTIONARY_PATH,
    GANANCIAS_SOCIEDADES_TIDY_HARMONIZED_PATH,
    GANANCIAS_SOCIEDADES_VARIABLE_DICTIONARY_PATH,
    ANALYSIS_DATA_DIR,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_tidy_outputs_validation.md"
DETAIL_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_tidy_branch_counts.csv"
EXPECTED_FISCAL_YEARS = {str(year) for year in range(1997, 2023)}
MAX_GITHUB_BLOB_BYTES = 100 * 1024 * 1024
TIDY_FIELDNAMES = [
    "fiscal_year",
    "rama_original_codigo",
    "rama_original_nombre",
    "rama_original_nivel",
    "clasificador_actividad",
    "rama_homologada_codigo",
    "rama_homologada_nombre",
    "variable_grupo",
    "variable_nombre",
    "valor_pesos_corrientes",
]
SOURCE_DICTIONARY_FIELDNAMES = [
    "source_key",
    "publication_year",
    "fiscal_year",
    "period_id",
    "archive_filename",
    "source_table_id",
    "source_table_path",
    "source_table_title",
    "table_family",
    "universe",
    "dimension_type",
    "source_note",
    "header_start_row_zero_based",
    "data_start_row_zero_based",
    "row_count",
]
ACTIVITY_DICTIONARY_FIELDNAMES = [
    "activity_key",
    "rama_homologacion_version",
    "classifier_period",
    "activity_level",
    "activity_code",
    "activity_label_original",
    "activity_section_original",
    "rama_homologacion_estado",
    "rama_comun_codigo",
    "rama_comun_label",
    "rama_comun_nivel",
    "rama_detalle_homologada_codigo",
    "rama_detalle_homologada_label",
    "rama_detalle_homologada_nivel",
    "rama_homologacion_nota",
    "fiscal_year_min",
    "fiscal_year_max",
    "row_count",
]
VARIABLE_DICTIONARY_FIELDNAMES = [
    "variable_key",
    "variable_name",
    "unit_original",
    "row_count",
]
def _load_dictionary_keys(
    path: Path,
    expected_fieldnames: list[str],
    key_field: str,
) -> tuple[set[str], int, int]:
    keys: set[str] = set()
    row_count_sum = 0
    rows = 0
    with path.open(encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        if reader.fieldnames != expected_fieldnames:
            raise ValueError(f"Unexpected fieldnames in {path}")
        for row in reader:
            rows += 1
            keys.add(row[key_field])
            row_count_sum += int(row["row_count"])
    return keys, rows, row_count_sum


def _load_source_dictionary() -> tuple[set[str], int, int]:
    keys: set[str] = set()
    row_count_sum = 0
    rows = 0
    with GANANCIAS_SOCIEDADES_SOURCE_DICTIONARY_PATH.open(
        encoding="utf-8",
    ) as input_file:
        reader = csv.DictReader(input_file)
        if reader.fieldnames != SOURCE_DICTIONARY_FIELDNAMES:
            raise ValueError(
                f"Unexpected fieldnames in {GANANCIAS_SOCIEDADES_SOURCE_DICTIONARY_PATH}"
            )
        for row in reader:
            rows += 1
            source_key = row["source_key"]
            keys.add(source_key)
            row_count_sum += int(row["row_count"])
    return keys, rows, row_count_sum


def _load_activity_dictionary() -> tuple[set[str], int, int]:
    keys: set[str] = set()
    row_count_sum = 0
    rows = 0
    with GANANCIAS_SOCIEDADES_ACTIVITY_DICTIONARY_PATH.open(
        encoding="utf-8",
    ) as input_file:
        reader = csv.DictReader(input_file)
        if reader.fieldnames != ACTIVITY_DICTIONARY_FIELDNAMES:
            raise ValueError(
                "Unexpected fieldnames in "
                f"{GANANCIAS_SOCIEDADES_ACTIVITY_DICTIONARY_PATH}"
            )
        for row in reader:
            rows += 1
            activity_key = row["activity_key"]
            keys.add(activity_key)
            row_count_sum += int(row["row_count"])
    return keys, rows, row_count_sum


def _load_variable_dictionary() -> tuple[set[str], int, int]:
    variables: set[str] = set()
    row_count_sum = 0
    rows = 0
    with GANANCIAS_SOCIEDADES_VARIABLE_DICTIONARY_PATH.open(
        encoding="utf-8",
    ) as input_file:
        reader = csv.DictReader(input_file)
        if reader.fieldnames != VARIABLE_DICTIONARY_FIELDNAMES:
            raise ValueError(
                "Unexpected fieldnames in "
                f"{GANANCIAS_SOCIEDADES_VARIABLE_DICTIONARY_PATH}"
            )
        for row in reader:
            rows += 1
            variables.add(row["variable_name"])
            row_count_sum += int(row["row_count"])
            if row["unit_original"] == "casos":
                raise ValueError(
                    "Variable dictionary for final analytic panel contains cases: "
                    f"{row['variable_name']}"
                )
    return variables, rows, row_count_sum


def _validate_tidy_panel(
    variable_names: set[str],
) -> tuple[int, set[str], Counter[str], Counter[str], Counter[str], list[str]]:
    failures: list[str] = []
    fiscal_years: set[str] = set()
    branch_counts: Counter[str] = Counter()
    variable_counts: Counter[str] = Counter()
    level_counts: Counter[str] = Counter()
    seen_keys: set[tuple[str, ...]] = set()
    rows = 0
    with GANANCIAS_SOCIEDADES_TIDY_HARMONIZED_PATH.open(
        newline="",
        encoding="utf-8",
    ) as input_file:
        reader = csv.DictReader(input_file)
        if reader.fieldnames != TIDY_FIELDNAMES:
            failures.append("Tidy panel field order differs from expected schema.")
            return rows, fiscal_years, branch_counts, variable_counts, level_counts, failures
        for row_number, row in enumerate(reader, start=2):
            rows += 1
            for field in TIDY_FIELDNAMES:
                if not row[field]:
                    failures.append(f"csv row {row_number}: empty required field={field}")
            fiscal_years.add(row["fiscal_year"])
            branch_counts[row["rama_homologada_codigo"]] += 1
            variable_counts[row["variable_nombre"]] += 1
            level_counts[row["rama_original_nivel"]] += 1
            try:
                Decimal(row["valor_pesos_corrientes"])
            except InvalidOperation:
                failures.append(
                    f"csv row {row_number}: invalid valor_pesos_corrientes="
                    f"{row['valor_pesos_corrientes']}"
                )
            if row["variable_nombre"] not in variable_names:
                failures.append(
                    f"csv row {row_number}: variable not present in dictionary="
                    f"{row['variable_nombre']}"
                )
            if row["variable_nombre"].endswith("_casos"):
                failures.append(f"csv row {row_number}: case variable in final panel")
            if row["variable_nombre"].startswith("presentaciones_"):
                failures.append(
                    f"csv row {row_number}: presentation-count variable in final panel"
                )
            if row["rama_original_nivel"] == "total":
                failures.append(f"csv row {row_number}: total activity row in final panel")
            if row["rama_homologada_codigo"] in {"TOTAL", "NO_HOMOLOGADO"}:
                failures.append(
                    f"csv row {row_number}: invalid homologated branch="
                    f"{row['rama_homologada_codigo']}"
                )
            duplicate_key = (
                row["fiscal_year"],
                row["rama_original_codigo"],
                row["rama_original_nombre"],
                row["rama_original_nivel"],
                row["clasificador_actividad"],
                row["variable_grupo"],
                row["variable_nombre"],
            )
            if duplicate_key in seen_keys:
                failures.append(f"csv row {row_number}: duplicate analytic key")
            seen_keys.add(duplicate_key)
    return rows, fiscal_years, branch_counts, variable_counts, level_counts, failures


def _write_branch_detail(branch_counts: Counter[str]) -> None:
    with DETAIL_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=["rama_comun_codigo", "rows"])
        writer.writeheader()
        for code, rows in sorted(branch_counts.items()):
            writer.writerow({"rama_comun_codigo": code, "rows": rows})


def main() -> None:
    """Run final validation checks for the tidy GitHub-shareable output."""

    failures: list[str] = []
    warnings: list[str] = []
    output_size = GANANCIAS_SOCIEDADES_TIDY_HARMONIZED_PATH.stat().st_size
    if output_size >= MAX_GITHUB_BLOB_BYTES:
        failures.append(
            "Tidy panel is not GitHub-shareable as a regular blob: "
            f"bytes={output_size} limit={MAX_GITHUB_BLOB_BYTES}"
        )

    (
        source_keys,
        source_dictionary_rows,
        source_row_count_sum,
    ) = _load_source_dictionary()
    (
        activity_keys,
        activity_dictionary_rows,
        activity_row_count_sum,
    ) = _load_activity_dictionary()
    (
        variable_names,
        variable_dictionary_rows,
        variable_row_count_sum,
    ) = _load_variable_dictionary()

    (
        rows,
        fiscal_years,
        branch_counts,
        variable_counts,
        level_counts,
        panel_failures,
    ) = _validate_tidy_panel(
        variable_names,
    )
    failures.extend(panel_failures)
    if source_row_count_sum != rows:
        failures.append(
            "Source dictionary row_count sum differs from tidy panel rows: "
            f"dictionary={source_row_count_sum} panel={rows}"
        )
    if activity_row_count_sum != rows:
        failures.append(
            "Activity dictionary row_count sum differs from tidy panel rows: "
            f"dictionary={activity_row_count_sum} panel={rows}"
        )
    if variable_row_count_sum != rows:
        failures.append(
            "Variable dictionary row_count sum differs from tidy panel rows: "
            f"dictionary={variable_row_count_sum} panel={rows}"
        )
    if fiscal_years != EXPECTED_FISCAL_YEARS:
        failures.append(
            "Tidy panel fiscal-year coverage differs from expected 1997-2022: "
            f"missing={sorted(EXPECTED_FISCAL_YEARS - fiscal_years)} "
            f"extra={sorted(fiscal_years - EXPECTED_FISCAL_YEARS)}"
        )

    for legacy_path in (
        GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH,
        GANANCIAS_SOCIEDADES_DATED_HARMONIZED_PATH,
    ):
        if legacy_path.exists():
            warnings.append(f"Stale legacy full CSV still exists locally: {legacy_path}")
    for gzip_path in sorted(ANALYSIS_DATA_DIR.glob("*afip_ganancias_sociedades*.csv.gz")):
        warnings.append(f"Stale compressed analysis CSV still exists locally: {gzip_path}")

    VALIDATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    _write_branch_detail(branch_counts)
    with REPORT_PATH.open("w", encoding="utf-8") as report_file:
        report_file.write("# Ganancias Sociedades analytic-output validation\n\n")
        report_file.write(f"- analytic_rows: {rows}\n")
        report_file.write(f"- analytic_bytes: {output_size}\n")
        report_file.write(f"- github_blob_limit_bytes: {MAX_GITHUB_BLOB_BYTES}\n")
        report_file.write(f"- source_dictionary_rows: {source_dictionary_rows}\n")
        report_file.write(f"- activity_dictionary_rows: {activity_dictionary_rows}\n")
        report_file.write(f"- variable_dictionary_rows: {variable_dictionary_rows}\n")
        report_file.write(f"- variable_names: {len(variable_counts)}\n")
        report_file.write(f"- fiscal_years: {min(fiscal_years)}-{max(fiscal_years)}\n")
        report_file.write(
            f"- activity_levels: {dict(sorted(level_counts.items()))}\n"
        )
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
    print(f"analytic_rows={rows}")
    print(f"analytic_bytes={output_size}")
    print(f"source_dictionary_rows={source_dictionary_rows}")
    print(f"activity_dictionary_rows={activity_dictionary_rows}")
    print(f"variable_dictionary_rows={variable_dictionary_rows}")
    print(f"variable_names={len(variable_counts)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
