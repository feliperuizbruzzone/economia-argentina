"""Validate the shareable tidy AFIP Ganancias Sociedades panel and dictionaries."""

from collections import Counter
import csv
import gzip
from pathlib import Path
import sys


sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR.parents[0] / "config"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(CONFIG_DIR))

from afip_ganancias_sociedades import long_fieldnames  # noqa: E402
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_ACTIVITY_DICTIONARY_PATH,
    GANANCIAS_SOCIEDADES_DATED_HARMONIZED_PATH,
    GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH,
    GANANCIAS_SOCIEDADES_P0_LONG_PATH,
    GANANCIAS_SOCIEDADES_P1_LONG_PATH,
    GANANCIAS_SOCIEDADES_P2_LONG_PATH,
    GANANCIAS_SOCIEDADES_P3_LONG_PATH,
    GANANCIAS_SOCIEDADES_P4_LONG_PATH,
    GANANCIAS_SOCIEDADES_P5_LONG_PATH,
    GANANCIAS_SOCIEDADES_P6_LONG_PATH,
    GANANCIAS_SOCIEDADES_SOURCE_DICTIONARY_PATH,
    GANANCIAS_SOCIEDADES_TIDY_HARMONIZED_PATH,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_tidy_outputs_validation.md"
DETAIL_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_tidy_branch_counts.csv"
EXPECTED_FISCAL_YEARS = {str(year) for year in range(1997, 2023)}
MAX_GITHUB_BLOB_BYTES = 100 * 1024 * 1024
TIDY_FIELDNAMES = [
    "publication_year",
    "fiscal_year",
    "period_id",
    "source_table_id",
    "source_key",
    "activity_key",
    "dimension_type",
    "dimension_value",
    "source_row_zero_based",
    "source_column_zero_based",
    "classifier_period",
    "activity_level",
    "activity_code",
    "rama_comun_codigo",
    "rama_detalle_homologada_codigo",
    "variable_name",
    "value",
    "unit_original",
    "value_pesos_current",
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
COMPONENT_PATHS = (
    GANANCIAS_SOCIEDADES_P0_LONG_PATH,
    GANANCIAS_SOCIEDADES_P1_LONG_PATH,
    GANANCIAS_SOCIEDADES_P2_LONG_PATH,
    GANANCIAS_SOCIEDADES_P3_LONG_PATH,
    GANANCIAS_SOCIEDADES_P4_LONG_PATH,
    GANANCIAS_SOCIEDADES_P5_LONG_PATH,
    GANANCIAS_SOCIEDADES_P6_LONG_PATH,
)


def _count_component_rows() -> int:
    total = 0
    fieldnames = long_fieldnames()
    for path in COMPONENT_PATHS:
        with path.open(encoding="utf-8") as input_file:
            reader = csv.DictReader(input_file)
            if reader.fieldnames != fieldnames:
                raise ValueError(f"Unexpected fieldnames in {path}")
            total += sum(1 for _row in reader)
    return total


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


def _validate_tidy_panel(
    source_keys: set[str],
    activity_keys: set[str],
) -> tuple[int, set[str], Counter[str], list[str]]:
    failures: list[str] = []
    fiscal_years: set[str] = set()
    branch_counts: Counter[str] = Counter()
    rows = 0
    with gzip.open(
        GANANCIAS_SOCIEDADES_TIDY_HARMONIZED_PATH,
        "rt",
        newline="",
        encoding="utf-8",
    ) as input_file:
        reader = csv.DictReader(input_file)
        if reader.fieldnames != TIDY_FIELDNAMES:
            failures.append("Tidy panel field order differs from expected schema.")
            return rows, fiscal_years, branch_counts, failures
        for row_number, row in enumerate(reader, start=2):
            rows += 1
            fiscal_years.add(row["fiscal_year"])
            branch_counts[row["rama_comun_codigo"]] += 1
            if row["source_key"] not in source_keys:
                failures.append(f"csv row {row_number}: unknown source_key={row['source_key']}")
            if row["activity_key"] not in activity_keys:
                failures.append(
                    f"csv row {row_number}: unknown activity_key={row['activity_key']}"
                )
            if row["rama_comun_codigo"] == "NO_HOMOLOGADO":
                failures.append(f"csv row {row_number}: NO_HOMOLOGADO branch")
    return rows, fiscal_years, branch_counts, failures


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
    expected_rows = _count_component_rows()
    output_size = GANANCIAS_SOCIEDADES_TIDY_HARMONIZED_PATH.stat().st_size
    if output_size >= MAX_GITHUB_BLOB_BYTES:
        failures.append(
            "Tidy panel is not GitHub-shareable as a regular blob: "
            f"bytes={output_size} limit={MAX_GITHUB_BLOB_BYTES}"
        )

    source_keys, source_dictionary_rows, source_row_count_sum = _load_dictionary_keys(
        GANANCIAS_SOCIEDADES_SOURCE_DICTIONARY_PATH,
        SOURCE_DICTIONARY_FIELDNAMES,
        "source_key",
    )
    activity_keys, activity_dictionary_rows, activity_row_count_sum = _load_dictionary_keys(
        GANANCIAS_SOCIEDADES_ACTIVITY_DICTIONARY_PATH,
        ACTIVITY_DICTIONARY_FIELDNAMES,
        "activity_key",
    )

    rows, fiscal_years, branch_counts, panel_failures = _validate_tidy_panel(
        source_keys,
        activity_keys,
    )
    failures.extend(panel_failures)
    if rows != expected_rows:
        failures.append(
            f"Tidy panel row count differs from P0-P6 components: rows={rows} "
            f"expected={expected_rows}"
        )
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

    VALIDATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    _write_branch_detail(branch_counts)
    with REPORT_PATH.open("w", encoding="utf-8") as report_file:
        report_file.write("# Ganancias Sociedades tidy-output validation\n\n")
        report_file.write(f"- tidy_rows: {rows}\n")
        report_file.write(f"- expected_component_rows: {expected_rows}\n")
        report_file.write(f"- tidy_bytes: {output_size}\n")
        report_file.write(f"- github_blob_limit_bytes: {MAX_GITHUB_BLOB_BYTES}\n")
        report_file.write(f"- source_dictionary_rows: {source_dictionary_rows}\n")
        report_file.write(f"- activity_dictionary_rows: {activity_dictionary_rows}\n")
        report_file.write(f"- fiscal_years: {min(fiscal_years)}-{max(fiscal_years)}\n")
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
    print(f"tidy_rows={rows}")
    print(f"tidy_bytes={output_size}")
    print(f"source_dictionary_rows={source_dictionary_rows}")
    print(f"activity_dictionary_rows={activity_dictionary_rows}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
