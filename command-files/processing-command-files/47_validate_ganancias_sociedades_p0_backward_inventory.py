"""Validate and document warnings for the Fase 3 P0 backward inventory."""

from collections import Counter, defaultdict
import csv
from pathlib import Path
import re
import sys


sys.dont_write_bytecode = True

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
PROCESSING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CONFIG_DIR))
sys.path.insert(0, str(PROCESSING_DIR))

from afip_ganancias_sociedades import P0_RECENT_ACTIVITY_TABLE_IDS  # noqa: E402
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_P0_BACKWARD_INVENTORY_PATH,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_p0_backward_inventory_validation.md"
DETAIL_PATH = VALIDATION_REPORTS_DIR / "ganancias_sociedades_p0_backward_inventory_validation.csv"

EXPECTED_FISCAL_YEARS = {"2014", "2015", "2016", "2017", "2018", "2019"}
RECENT_TABLE_IDS = set(P0_RECENT_ACTIVITY_TABLE_IDS)


def _truthy(value: str) -> bool:
    return value.strip().lower() == "true"


def _canonical_id(source_table_id: str) -> str:
    return re.sub(r"_2-?$", "", source_table_id)


def _load_rows() -> list[dict[str, str]]:
    with GANANCIAS_SOCIEDADES_P0_BACKWARD_INVENTORY_PATH.open(encoding="utf-8") as input_file:
        return list(csv.DictReader(input_file))


def _write_detail(rows: list[dict[str, str]], warnings_by_row: dict[tuple[str, str], list[str]]) -> None:
    fields = [
        "publication_year",
        "fiscal_year",
        "source_table_id",
        "canonical_source_table_id",
        "source_table_path",
        "first_data_label",
        "notes",
        "warnings",
    ]
    with DETAIL_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            key = (row["publication_year"], row["source_table_id"])
            writer.writerow(
                {
                    "publication_year": row["publication_year"],
                    "fiscal_year": row["fiscal_year"],
                    "source_table_id": row["source_table_id"],
                    "canonical_source_table_id": _canonical_id(row["source_table_id"]),
                    "source_table_path": row["source_table_path"],
                    "first_data_label": row["first_data_label"],
                    "notes": row["notes"],
                    "warnings": " | ".join(warnings_by_row.get(key, [])),
                }
            )


def main() -> None:
    rows = _load_rows()
    failures: list[str] = []
    warnings: list[str] = []
    warnings_by_row: dict[tuple[str, str], list[str]] = defaultdict(list)

    if not rows:
        failures.append("No rows found in backward P0 inventory.")

    fiscal_years = {row["fiscal_year"] for row in rows}
    if fiscal_years != EXPECTED_FISCAL_YEARS:
        warnings.append(
            "Unexpected fiscal-year coverage in backward inventory: "
            f"observed={sorted(fiscal_years)} expected={sorted(EXPECTED_FISCAL_YEARS)}"
        )

    by_fiscal_year: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_fiscal_year[row["fiscal_year"]].append(row)
        row_key = (row["publication_year"], row["source_table_id"])
        if row["period_id"] != "P0_new_xls_backward_probe":
            failures.append(f"{row_key}: period_id={row['period_id']}")
        if row["dimension_type"] != "actividad_economica":
            failures.append(f"{row_key}: dimension_type={row['dimension_type']}")
        if row["unit_original"] != "millones_pesos_corrientes":
            warnings.append(f"{row_key}: unit_original={row['unit_original']}")
            warnings_by_row[row_key].append(f"unit_original={row['unit_original']}")
        if row["first_data_label"] != "TOTAL":
            warnings.append(
                f"{row_key}: first_data_label={row['first_data_label']}; source may lack TOTAL row."
            )
            warnings_by_row[row_key].append(f"first_data_label={row['first_data_label']}")
        if row["notes"]:
            warnings.append(f"{row_key}: notes={row['notes']}")
            warnings_by_row[row_key].append(row["notes"])
        if not row["header_start_row_zero_based"] or not row["data_start_row_zero_based"]:
            failures.append(f"{row_key}: missing detected table bounds")
        if not _truthy(row["has_activity_section"]):
            failures.append(f"{row_key}: has_activity_section is false")
        if not _truthy(row["has_activity_3digit"]):
            failures.append(f"{row_key}: has_activity_3digit is false")
        if "Impuesto a las Ganancias Sociedades" not in row["source_table_title"]:
            failures.append(f"{row_key}: title does not identify Ganancias Sociedades")

    for fiscal_year, year_rows in sorted(by_fiscal_year.items()):
        source_ids = {row["source_table_id"] for row in year_rows}
        canonical_ids = {_canonical_id(source_id) for source_id in source_ids}
        missing_recent = sorted(RECENT_TABLE_IDS - canonical_ids)
        extra_canonical = sorted(canonical_ids - RECENT_TABLE_IDS)
        continuation_ids = sorted(source_id for source_id in source_ids if source_id != _canonical_id(source_id))
        if missing_recent:
            warnings.append(
                f"Fiscal year {fiscal_year}: missing recent P0 detailed table ids: "
                f"{', '.join(missing_recent)}"
            )
        if extra_canonical:
            warnings.append(
                f"Fiscal year {fiscal_year}: extra canonical table ids not in recent P0 schema: "
                f"{', '.join(extra_canonical)}"
            )
        if continuation_ids:
            warnings.append(
                f"Fiscal year {fiscal_year}: continuation files require concatenation: "
                f"{', '.join(continuation_ids)}"
            )

    counts_by_publication_year = Counter(row["publication_year"] for row in rows)
    counts_by_fiscal_year = Counter(row["fiscal_year"] for row in rows)
    counts_by_archive = Counter(row["archive_filename"] for row in rows)

    VALIDATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    _write_detail(rows, warnings_by_row)

    report = [
        "# Ganancias Sociedades P0 Backward Inventory Validation",
        "",
        "Scope: Fase 3 structural inventory, publication years 2015-2020, fiscal years 2014-2019.",
        "",
        f"- rows_validated: {len(rows)}",
        f"- fiscal_years: {', '.join(sorted(fiscal_years))}",
        f"- failures: {len(failures)}",
        f"- warnings: {len(warnings)}",
        "",
        "## Counts By Publication Year",
        "",
        "| publication_year | rows |",
        "|---:|---:|",
    ]
    for publication_year, count in sorted(counts_by_publication_year.items()):
        report.append(f"| {publication_year} | {count} |")

    report.extend(["", "## Counts By Fiscal Year", "", "| fiscal_year | rows |", "|---:|---:|"])
    for fiscal_year, count in sorted(counts_by_fiscal_year.items()):
        report.append(f"| {fiscal_year} | {count} |")

    report.extend(["", "## Archives", "", "| archive_filename | rows |", "|---|---:|"])
    for archive_filename, count in sorted(counts_by_archive.items()):
        report.append(f"| `{archive_filename}` | {count} |")

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
