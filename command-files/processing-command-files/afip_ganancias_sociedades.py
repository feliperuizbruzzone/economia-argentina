"""Helpers for AFIP Ganancias Sociedades extraction.

This module contains small, testable building blocks for the ETL pipeline.
It intentionally does not implement the full extraction pipeline yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unicodedata
from zipfile import ZipFile
from typing import Any, Iterable, Sequence

import xlrd


@dataclass(frozen=True)
class TableBounds:
    """Detected row positions for a statistical table.

    Row indexes are zero-based because they are intended for programmatic use.
    The probe scripts print one-based values for spreadsheet inspection.
    """

    header_start_row: int
    header_end_row: int
    data_start_row: int
    data_end_row_exclusive: int | None
    header_score: int
    first_data_label: str


@dataclass(frozen=True)
class VariableColumn:
    """A detected value column in a source statistical table."""

    column_index: int
    variable_name: str
    unit_original: str
    is_monetary: bool


P0_MODERN_XLS_ARCHIVES = {
    2015: "estadisticasTributarias2015.zip",
    2016: "estadisticasTributarias2016.zip",
    2017: "estadisticasTributarias2017.zip",
    2018: "estadisticasTributarias2018.zip",
    2019: "Public2019.zip",
    2020: "Publicacion-2020.zip",
    2021: "Estadisticas-Tributarias-2021.zip",
    2022: "estadisticas-Tributarias-2022.zip",
    2023: "Estadisticas-Tributarias-2023.zip",
}
P0_BACKWARD_XLS_ARCHIVES = {
    2015: "estadisticasTributarias2015.zip",
    2016: "estadisticasTributarias2016.zip",
    2017: "estadisticasTributarias2017.zip",
    2018: "estadisticasTributarias2018.zip",
    2019: "Public2019.zip",
    2020: "Publicacion-2020.zip",
}
P1_HTML_ARCHIVES = {
    2014: "estadisticasTributarias2014.zip",
}
P2_HTML_ARCHIVES = {
    2013: "estadisticasTributarias2013.zip",
}
P3_HTML_ARCHIVES = {
    2009: "estadisticasTributarias2009.zip",
    2010: "estadisticasTributarias2010.zip",
    2011: "estadisticasTributarias2011.zip",
    2012: "estadisticasTributarias2012.zip",
}
P4_CAB_XLS_ARCHIVES = {
    2003: "estadisticasTributarias2003.zip",
    2004: "estadisticasTributarias2004.zip",
    2005: "estadisticasTributarias2005.zip",
    2006: "estadisticasTributarias2006.zip",
    2007: "estadisticasTributarias2007.zip",
    2008: "estadisticasTributarias2008.zip",
}
P5_CAB_XLS_ARCHIVES = {
    2002: "estadisticasTributarias2002.zip",
}
P6_DIRECT_XLS_ARCHIVES = {
    1998: "estadisticasTributarias1998.zip",
    1999: "estadisticasTributarias1999.zip",
}

P0_ACTIVITY_SUMMARY_TABLE_ID = "2.3.1.1.1"
P0_ACTIVITY_COSTS_TABLE_ID = "2.3.1.1.2.1"
P0_ACTIVITY_SALES_DETAIL_TABLE_ID = "2.3.1.1.2.2"
P0_ACTIVITY_COST_LINKED_EXPENSES_TABLE_ID = "2.3.1.1.2.3"
P0_ACTIVITY_GROSS_RESULT_TABLE_ID = "2.3.1.1.2.4"
P0_ACTIVITY_OPERATING_EXPENSES_TABLE_ID = "2.3.1.1.2.5"
P0_ACTIVITY_OTHER_RESULTS_TABLE_ID = "2.3.1.1.2.6"
P0_ACTIVITY_ACCOUNTING_RESULT_TABLE_ID = "2.3.1.1.2.7"
P0_ACTIVITY_TAX_RESULT_TABLE_ID = "2.3.1.1.3"
P0_ACTIVITY_TAX_DETERMINATION_TABLE_ID = "2.3.1.1.4"
P0_ACTIVITY_ASSETS_TABLE_ID = "2.3.1.1.5.1"
P0_ACTIVITY_CASH_ASSETS_TABLE_ID = "2.3.1.1.5.1.1"
P0_ACTIVITY_CREDIT_ASSETS_TABLE_ID = "2.3.1.1.5.1.2"
P0_ACTIVITY_INVENTORY_ASSETS_TABLE_ID = "2.3.1.1.5.1.3"
P0_ACTIVITY_FIXED_ASSETS_TABLE_ID = "2.3.1.1.5.1.4"
P0_ACTIVITY_LIABILITIES_TABLE_ID = "2.3.1.1.5.2"
P0_ACTIVITY_DEBT_LIABILITIES_TABLE_ID = "2.3.1.1.5.2.1"
P0_ACTIVITY_EQUITY_TABLE_ID = "2.3.1.1.5.3"
P0_ACTIVITY_EQUITY_INCREASES_TABLE_ID = "2.3.1.1.5.3.1"
P0_ACTIVITY_EQUITY_DECREASES_TABLE_ID = "2.3.1.1.5.3.2"
P0_RECENT_ACTIVITY_TABLE_IDS = (
    P0_ACTIVITY_SUMMARY_TABLE_ID,
    P0_ACTIVITY_COSTS_TABLE_ID,
    P0_ACTIVITY_SALES_DETAIL_TABLE_ID,
    P0_ACTIVITY_COST_LINKED_EXPENSES_TABLE_ID,
    P0_ACTIVITY_GROSS_RESULT_TABLE_ID,
    P0_ACTIVITY_OPERATING_EXPENSES_TABLE_ID,
    P0_ACTIVITY_OTHER_RESULTS_TABLE_ID,
    P0_ACTIVITY_ACCOUNTING_RESULT_TABLE_ID,
    P0_ACTIVITY_TAX_RESULT_TABLE_ID,
    P0_ACTIVITY_TAX_DETERMINATION_TABLE_ID,
    P0_ACTIVITY_ASSETS_TABLE_ID,
    P0_ACTIVITY_CASH_ASSETS_TABLE_ID,
    P0_ACTIVITY_CREDIT_ASSETS_TABLE_ID,
    P0_ACTIVITY_INVENTORY_ASSETS_TABLE_ID,
    P0_ACTIVITY_FIXED_ASSETS_TABLE_ID,
    P0_ACTIVITY_LIABILITIES_TABLE_ID,
    P0_ACTIVITY_DEBT_LIABILITIES_TABLE_ID,
    P0_ACTIVITY_EQUITY_TABLE_ID,
    P0_ACTIVITY_EQUITY_INCREASES_TABLE_ID,
    P0_ACTIVITY_EQUITY_DECREASES_TABLE_ID,
)
P1_ACTIVITY_TABLE_IDS = (
    P0_ACTIVITY_SUMMARY_TABLE_ID,
    P0_ACTIVITY_COSTS_TABLE_ID,
    P0_ACTIVITY_SALES_DETAIL_TABLE_ID,
    P0_ACTIVITY_COST_LINKED_EXPENSES_TABLE_ID,
    P0_ACTIVITY_GROSS_RESULT_TABLE_ID,
    P0_ACTIVITY_OPERATING_EXPENSES_TABLE_ID,
    P0_ACTIVITY_OTHER_RESULTS_TABLE_ID,
    P0_ACTIVITY_ACCOUNTING_RESULT_TABLE_ID,
    P0_ACTIVITY_TAX_RESULT_TABLE_ID,
    P0_ACTIVITY_TAX_DETERMINATION_TABLE_ID,
    P0_ACTIVITY_ASSETS_TABLE_ID,
    P0_ACTIVITY_LIABILITIES_TABLE_ID,
    P0_ACTIVITY_EQUITY_TABLE_ID,
)
P2_ACTIVITY_TABLE_IDS = P1_ACTIVITY_TABLE_IDS
P3_ACTIVITY_TABLE_IDS = P2_ACTIVITY_TABLE_IDS
P4_ACTIVITY_TABLE_IDS = (
    P0_ACTIVITY_SUMMARY_TABLE_ID,
    P0_ACTIVITY_COSTS_TABLE_ID,
    P0_ACTIVITY_SALES_DETAIL_TABLE_ID,
    P0_ACTIVITY_COST_LINKED_EXPENSES_TABLE_ID,
    P0_ACTIVITY_GROSS_RESULT_TABLE_ID,
    P0_ACTIVITY_TAX_RESULT_TABLE_ID,
    P0_ACTIVITY_TAX_DETERMINATION_TABLE_ID,
    P0_ACTIVITY_ASSETS_TABLE_ID,
    P0_ACTIVITY_LIABILITIES_TABLE_ID,
    P0_ACTIVITY_EQUITY_TABLE_ID,
)
P5_LEGACY_ACTIVITY_SUMMARY_TABLE_ID = "3.3.1.1.1"
P5_LEGACY_ACTIVITY_RESULTS_TABLE_ID = "3.3.1.1.2"
P5_LEGACY_ACTIVITY_TAX_RESULT_TABLE_ID = "3.3.1.1.3"
P5_LEGACY_ACTIVITY_BALANCE_TABLE_ID = "3.3.1.1.4"
P5_LEGACY_ACTIVITY_COSTS_TABLE_ID = "3.3.1.1.2.1"
P5_LEGACY_ACTIVITY_GROSS_RESULT_TABLE_ID = "3.3.1.1.2.2"
P5_LEGACY_ACTIVITY_OTHER_RESULTS_TABLE_ID = "3.3.1.1.2.3"
P5_LEGACY_ACTIVITY_ACCOUNTING_RESULT_TABLE_ID = "3.3.1.1.2.4"
P5_LEGACY_ACTIVITY_ASSETS_TABLE_ID = "3.3.1.1.5.1"
P5_LEGACY_ACTIVITY_LIABILITIES_TABLE_ID = "3.3.1.1.5.2"
P5_LEGACY_ACTIVITY_EQUITY_TABLE_ID = "3.3.1.1.5.3"
P5_ACTIVITY_TABLE_IDS_1999_2000 = (
    P5_LEGACY_ACTIVITY_SUMMARY_TABLE_ID,
    P5_LEGACY_ACTIVITY_RESULTS_TABLE_ID,
    P5_LEGACY_ACTIVITY_TAX_RESULT_TABLE_ID,
    P5_LEGACY_ACTIVITY_BALANCE_TABLE_ID,
)
P5_ACTIVITY_TABLE_IDS_2001 = (
    P5_LEGACY_ACTIVITY_SUMMARY_TABLE_ID,
    P5_LEGACY_ACTIVITY_COSTS_TABLE_ID,
    P5_LEGACY_ACTIVITY_GROSS_RESULT_TABLE_ID,
    P5_LEGACY_ACTIVITY_OTHER_RESULTS_TABLE_ID,
    P5_LEGACY_ACTIVITY_ACCOUNTING_RESULT_TABLE_ID,
    P5_LEGACY_ACTIVITY_TAX_RESULT_TABLE_ID,
    P5_LEGACY_ACTIVITY_BALANCE_TABLE_ID,
    P5_LEGACY_ACTIVITY_ASSETS_TABLE_ID,
    P5_LEGACY_ACTIVITY_LIABILITIES_TABLE_ID,
    P5_LEGACY_ACTIVITY_EQUITY_TABLE_ID,
)
P6_1997_ACTIVITY_SUMMARY_TABLE_ID = "4.4.1.1.1"
P6_1997_ACTIVITY_RESULTS_TABLE_ID = "4.4.1.1.2"
P6_1997_ACTIVITY_TAX_ADJUSTMENTS_TABLE_ID = "4.4.1.1.3"
P6_1997_ACTIVITY_BALANCE_TABLE_ID = "4.4.1.1.4"
P6_1998_ACTIVITY_SUMMARY_TABLE_ID = "3.3.1.1.1"
P6_1998_ACTIVITY_RESULTS_TABLE_ID = "3.3.1.1.2"
P6_1998_ACTIVITY_TAX_RESULT_TABLE_ID = "3.3.1.1.3"
P6_1998_ACTIVITY_BALANCE_TABLE_ID = "3.3.1.1.4"
P6_ACTIVITY_TABLE_IDS_1997 = (
    P6_1997_ACTIVITY_SUMMARY_TABLE_ID,
    P6_1997_ACTIVITY_RESULTS_TABLE_ID,
    P6_1997_ACTIVITY_TAX_ADJUSTMENTS_TABLE_ID,
    P6_1997_ACTIVITY_BALANCE_TABLE_ID,
)
P6_ACTIVITY_TABLE_IDS_1998 = (
    P6_1998_ACTIVITY_SUMMARY_TABLE_ID,
    P6_1998_ACTIVITY_RESULTS_TABLE_ID,
    P6_1998_ACTIVITY_TAX_RESULT_TABLE_ID,
    P6_1998_ACTIVITY_BALANCE_TABLE_ID,
)


def normalize_text(value: Any) -> str:
    """Return an uppercase ASCII-normalized representation of a cell value."""

    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        text = str(int(value))
    else:
        text = str(value)
    text = " ".join(text.strip().split())
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.upper()
    text = text.replace("IMFORTE", "IMPORTE")
    text = text.replace("ESPORTACIONES", "EXPORTACIONES")
    text = text.replace("OBRAS EM CONSTRUCCION", "OBRAS EN CONSTRUCCION")
    return text


def cell_display_text(value: Any) -> str:
    """Return a compact display string for diagnostics and output metadata."""

    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return " ".join(str(value).strip().split())


def is_number_like(value: Any) -> bool:
    """Return True when a cell looks like a numeric table value."""

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return True
    text = cell_display_text(value)
    if not text:
        return False
    normalized = text.replace(".", "").replace(",", ".")
    try:
        float(normalized)
    except ValueError:
        return False
    return True


def row_text(row: Sequence[Any]) -> str:
    """Return normalized text for a full spreadsheet row."""

    return " ".join(normalize_text(cell) for cell in row if normalize_text(cell))


def _header_score(row: Sequence[Any]) -> int:
    text = row_text(row)
    score = 0
    if "ACTIVIDAD ECONOMICA" in text:
        score += 6
    if "PRESENTACIONES" in text:
        score += 2
    if "VENTAS" in text:
        score += 2
    if "GANANCIA NETA" in text:
        score += 1
    if "IMPUESTO DETERMINADO" in text:
        score += 1
    return score


def _first_nonblank_cell(row: Sequence[Any]) -> tuple[int, str] | None:
    for index, value in enumerate(row):
        text = cell_display_text(value)
        if text:
            return index, text
    return None


def _looks_like_data_row(row: Sequence[Any], min_numeric_cells: int) -> bool:
    first = _first_nonblank_cell(row)
    if first is None:
        return False

    _, first_text = first
    first_norm = normalize_text(first_text)
    if not first_norm:
        return False
    if first_norm in {"ACTIVIDAD ECONOMICA", "PRESENTACIONES"}:
        return False
    if first_norm.startswith(("CASOS", "IMPORTE", "UTILIDAD", "PERDIDA")):
        return False

    numeric_count = sum(is_number_like(value) for value in row[1:])
    if numeric_count < min_numeric_cells:
        return False

    if first_norm == "TOTAL":
        return True
    if re.match(r"^[A-Z]\s*-\s*", first_norm):
        return True
    if re.match(r"^[0-9]{3}\s*\.", first_norm):
        return True

    return bool(re.search(r"[A-Z]", first_norm))


def detect_xls_table_bounds(
    rows: Sequence[Sequence[Any]],
    *,
    min_numeric_cells: int = 2,
) -> TableBounds:
    """Detect header and data-start rows for an AFIP XLS statistical table.

    The detector scores rows by semantic labels such as "ACTIVIDAD ECONOMICA",
    "PRESENTACIONES", "VENTAS", "GANANCIA NETA" and "IMPUESTO DETERMINADO".
    It then searches downward for the first row that looks like actual data:
    a nonblank activity label plus at least ``min_numeric_cells`` numeric cells.

    This avoids hard-coded row numbers. The same function can be reused across
    modern XLS periods and then validated against older XLS/CAB periods before
    writing value extraction.

    Parameters
    ----------
    rows:
        Spreadsheet rows as lists or tuples of cell values.
    min_numeric_cells:
        Minimum number of numeric cells required after the label column for a
        row to be treated as data.

    Returns
    -------
    TableBounds
        Detected zero-based header/data row positions and diagnostic metadata.

    Raises
    ------
    ValueError
        If no plausible activity header or data-start row is found.
    """

    scored_rows = [
        (row_index, _header_score(row))
        for row_index, row in enumerate(rows)
    ]
    header_row, header_score = max(scored_rows, key=lambda item: item[1])
    if header_score <= 0:
        raise ValueError("Could not detect an activity header row.")

    data_start_row = None
    first_data_label = ""
    for row_index in range(header_row + 1, len(rows)):
        row = rows[row_index]
        if _looks_like_data_row(row, min_numeric_cells):
            data_start_row = row_index
            first = _first_nonblank_cell(row)
            first_data_label = first[1] if first else ""
            break

    if data_start_row is None:
        raise ValueError("Could not detect a data-start row.")

    return TableBounds(
        header_start_row=header_row,
        header_end_row=data_start_row - 1,
        data_start_row=data_start_row,
        data_end_row_exclusive=None,
        header_score=header_score,
        first_data_label=first_data_label,
    )


def xls_rows_from_bytes(file_contents: bytes) -> list[list[Any]]:
    """Read the first sheet of an XLS workbook into a row-value matrix."""

    workbook = xlrd.open_workbook(file_contents=file_contents, on_demand=True)
    sheet = workbook.sheet_by_index(0)
    return [
        [sheet.cell_value(row_index, col_index) for col_index in range(sheet.ncols)]
        for row_index in range(sheet.nrows)
    ]


def _title_lines(rows: Sequence[Sequence[Any]], max_rows: int = 8) -> list[str]:
    lines: list[str] = []
    for row in rows[:max_rows]:
        line = " | ".join(
            cell_display_text(cell)
            for cell in row
            if cell_display_text(cell)
        )
        if line:
            lines.append(line)
    return lines


def _find_fiscal_year(text: str) -> int | None:
    match = re.search(r"ANO FISCAL\s+([0-9]{4})", normalize_text(text))
    if match:
        return int(match.group(1))
    return None


def _unit_from_text(text: str) -> str:
    normalized = normalize_text(text)
    if "MILLONES DE PESOS CORRIENTES" in normalized:
        return "millones_pesos_corrientes"
    if "MILES DE PESOS CORRIENTES" in normalized:
        return "miles_pesos_corrientes"
    return "unknown"


def _table_family_from_text(text: str) -> str:
    normalized = normalize_text(text)
    if "PRESENTACIONES" in normalized and "VENTAS" in normalized and "IMPUESTO DETERMINADO" in normalized:
        return "resumen_presentaciones_ventas_impuesto"
    if "ESTADO DE RESULTADOS" in normalized:
        return "estado_resultados"
    if "RESULTADO IMPOSITIVO" in normalized:
        return "resultado_impositivo"
    if "DETERMINACION DEL RESULTADO IMPOSITIVO" in normalized:
        return "resultado_impositivo"
    if "DETERMINACION DEL IMPUESTO" in normalized:
        return "determinacion_impuesto"
    if "ESTADO DE SITUACION PATRIMONIAL" in normalized:
        return "situacion_patrimonial"
    return "unknown"


def _dimension_type_from_text(text: str) -> str:
    normalized = normalize_text(text)
    if "ACTIVIDAD ECONOMICA" in normalized:
        return "actividad_economica"
    if "MES DE CIERRE" in normalized:
        return "mes_cierre"
    if "TRAMO DE VENTAS" in normalized:
        return "tramo_ventas"
    if "TRAMO DE GANANCIA" in normalized:
        return "tramo_ganancia_neta_imponible"
    return "unknown"


def _universe_from_text(text: str) -> str:
    normalized = normalize_text(text)
    if "PRESENTACIONES CON IMPUESTO DETERMINADO" in normalized:
        return "presentaciones_con_impuesto_determinado"
    if "PRESENTACIONES CON VENTAS DE BIENES Y SERVICIOS" in normalized:
        return "presentaciones_con_ventas"
    if "TOTAL DE PRESENTACIONES" in normalized:
        return "total_presentaciones"
    return "unknown"


def _activity_detail_flags(rows: Sequence[Sequence[Any]]) -> tuple[bool, bool]:
    has_section = False
    has_detail = False
    for row in rows:
        first = _first_nonblank_cell(row)
        if first is None:
            continue
        label = normalize_text(first[1])
        if re.match(r"^[A-Z]\s*-\s*", label):
            has_section = True
        if re.match(r"^[0-9]{3}\s*\.", label):
            has_detail = True
        if has_section and has_detail:
            break
    return has_section, has_detail


def _source_table_id(member_name: str) -> str:
    return Path(member_name).stem


def _chapter_code(source_table_id: str) -> str:
    parts = source_table_id.split(".")
    if len(parts) >= 2:
        return ".".join(parts[:2])
    return source_table_id


def decimal_from_cell(value: Any) -> Decimal | None:
    """Parse a spreadsheet cell into a Decimal, returning None for blanks."""

    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))

    text = cell_display_text(value)
    if not text:
        return None
    text = text.replace(".", "").replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def decimal_to_text(value: Decimal | None) -> str:
    """Return a stable CSV representation for Decimal values."""

    if value is None:
        return ""
    if value == value.to_integral_value():
        return str(value.quantize(Decimal("1")))
    return format(value.normalize(), "f")


def _monetary_multiplier(unit_original: str) -> Decimal | None:
    if unit_original == "millones_pesos_corrientes":
        return Decimal("1000000")
    if unit_original == "miles_pesos_corrientes":
        return Decimal("1000")
    return None


def _combined_header_text(rows: Sequence[Sequence[Any]], column_index: int) -> str:
    pieces = []
    for row in rows:
        if column_index < len(row):
            text = normalize_text(row[column_index])
            if text:
                pieces.append(text)
    return " ".join(pieces)


def _forward_filled_column_header_text(
    header_rows: Sequence[Sequence[Any]],
    column_index: int,
    max_columns: int,
) -> str:
    pieces = []
    for row in header_rows:
        current = ""
        for current_column in range(max_columns):
            if current_column < len(row):
                text = normalize_text(row[current_column])
                if text:
                    current = text
            if current_column == column_index and current:
                pieces.append(current)
                break
    return " ".join(dict.fromkeys(pieces))


def _trim_header_rows_from_markers(
    header_rows: Sequence[Sequence[Any]],
    markers: Sequence[str],
) -> Sequence[Sequence[Any]]:
    """Return header rows beginning at the first row containing all markers."""

    for row_index, row in enumerate(header_rows):
        text = row_text(row)
        if all(marker in text for marker in markers):
            return header_rows[row_index:]
    return header_rows


def _trim_header_rows_from_exact_cell(
    header_rows: Sequence[Sequence[Any]],
    marker: str,
) -> Sequence[Sequence[Any]]:
    """Return header rows beginning at the first row with an exact marker cell."""

    for row_index, row in enumerate(header_rows):
        if any(normalize_text(cell) == marker for cell in row):
            return header_rows[row_index:]
    return header_rows


def _detect_p0_paired_columns(
    header_rows: Sequence[Sequence[Any]],
    paired_mappings: Sequence[tuple[str, str]],
    markers: Sequence[str] = ("ACTIVIDAD ECONOMICA", "PRESENTACIONES"),
    trim_to_exact_activity_header: bool = False,
    optional_prefixes: frozenset[str] = frozenset(),
) -> tuple[int, list[VariableColumn]]:
    """Detect activity, presentation and paired `Casos`/`Importe` columns."""

    if trim_to_exact_activity_header:
        effective_header_rows = _trim_header_rows_from_exact_cell(
            header_rows,
            "ACTIVIDAD ECONOMICA",
        )
    else:
        effective_header_rows = _trim_header_rows_from_markers(header_rows, markers)
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            effective_header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue
        if not direct_text:
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        else:
            for concept_text, variable_prefix in paired_mappings:
                if concept_text in filled_text:
                    if "CASOS" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            f"{variable_prefix}_casos",
                            "casos",
                            False,
                        )
                    elif "IMPORTE" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            variable_prefix,
                            "millones_pesos_corrientes",
                            True,
                        )
                    break

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {"presentaciones_total"}
    for _, variable_prefix in paired_mappings:
        if variable_prefix in optional_prefixes:
            continue
        expected.update({f"{variable_prefix}_casos", variable_prefix})

    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_23111_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.1.

    The source uses merged Excel headers: "PRESENTACIONES" spans three
    subcolumns while the monetary variables appear as standalone columns. This
    detector reads the header text around each column rather than relying on
    fixed column numbers.
    """

    max_columns = max((len(row) for row in header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    for column_index in range(max_columns):
        text = _combined_header_text(header_rows, column_index)
        if not text:
            continue
        if "ACTIVIDAD ECONOMICA" in text:
            activity_column = column_index
            continue
        if "PRESENTACIONES" in text and "TOTAL" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif text.startswith("CON VENTAS"):
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "presentaciones_con_ventas",
                "casos",
                False,
            )
        elif text.startswith("CON IMPUESTO"):
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "presentaciones_con_impuesto_determinado",
                "casos",
                False,
            )
        elif "VENTAS DE BIENES Y SERVICIOS Y LOCACIONES NETAS" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "ventas_bienes_servicios_locaciones_netas",
                "millones_pesos_corrientes",
                True,
            )
        elif "GANANCIA NETA IMPONIBLE" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "ganancia_neta_imponible",
                "millones_pesos_corrientes",
                True,
            )
        elif text == "IMPUESTO DETERMINADO":
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "impuesto_determinado",
                "millones_pesos_corrientes",
                True,
            )

    expected = {
        "presentaciones_total",
        "presentaciones_con_ventas",
        "presentaciones_con_impuesto_determinado",
        "ventas_bienes_servicios_locaciones_netas",
        "ganancia_neta_imponible",
        "impuesto_determinado",
    }
    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_231121_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.2.1.

    This table has paired `Casos` and `Importe` columns under sales and cost
    concepts. The detector forward-fills merged Excel headers before mapping
    each semantic header to a canonical variable name.
    """

    max_columns = max((len(row) for row in header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    for column_index in range(max_columns):
        direct_text = _combined_header_text(header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif "VENTAS DE BIENES Y SERVICIOS Y LOCACIONES NETAS" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "presentaciones_con_ventas",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "ventas_bienes_servicios_locaciones_netas",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "COSTOS" in filled_text and "TOTAL" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "costos_total_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "costos_total",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "COMPRAS NETAS" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "compras_netas_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "compras_netas",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "GASTOS DE PRODUCCION" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "gastos_produccion_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "gastos_produccion",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "GASTOS VINCULADOS AL COSTO" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "gastos_vinculados_al_costo_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "gastos_vinculados_al_costo",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "EXISTENCIA INICIAL" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "existencia_inicial_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "existencia_inicial",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "EXISTENCIA FINAL" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "existencia_final_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "existencia_final",
                    "millones_pesos_corrientes",
                    True,
                )

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {
        "presentaciones_total",
        "presentaciones_con_ventas",
        "costos_total_casos",
        "costos_total",
        "compras_netas_casos",
        "compras_netas",
        "gastos_produccion_casos",
        "gastos_produccion",
        "gastos_vinculados_al_costo_casos",
        "gastos_vinculados_al_costo",
        "existencia_inicial_casos",
        "existencia_inicial",
        "existencia_final_casos",
        "existencia_final",
    }
    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p3_2008_231121_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect fiscal 2008 table 2.3.1.1.2.1 with old cost labels.

    Fiscal year 2008 labels the residual cost component as `OTROS` instead of
    `GASTOS VINCULADOS AL COSTO`. The variable is kept as `costos_otros` to
    avoid implying exact comparability with later labels.
    """

    max_columns = max((len(row) for row in header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    for column_index in range(max_columns):
        direct_text = _combined_header_text(header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif "VENTAS DE BIENES Y SERVICIOS Y LOCACIONES NETAS" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "presentaciones_con_ventas",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "ventas_bienes_servicios_locaciones_netas",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "COSTOS" in filled_text and "TOTAL" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "costos_total_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "costos_total",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "COMPRAS NETAS" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "compras_netas_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "compras_netas",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "GASTOS DE PRODUCCION" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "gastos_produccion_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "gastos_produccion",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "OTROS" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "costos_otros_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "costos_otros",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "EXISTENCIA INICIAL" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "existencia_inicial_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "existencia_inicial",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "EXISTENCIA FINAL" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "existencia_final_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "existencia_final",
                    "millones_pesos_corrientes",
                    True,
                )

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {
        "presentaciones_total",
        "presentaciones_con_ventas",
        "costos_total_casos",
        "costos_total",
        "compras_netas_casos",
        "compras_netas",
        "gastos_produccion_casos",
        "gastos_produccion",
        "costos_otros_casos",
        "costos_otros",
        "existencia_inicial_casos",
        "existencia_inicial",
        "existencia_final_casos",
        "existencia_final",
    }
    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_231122_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.2.2.

    This table details sales and export concepts. Each concept has paired
    `Casos` and `Importe` columns, except the standalone presentation count.
    """

    max_columns = max((len(row) for row in header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}
    paired_mappings = (
        (
            "VENTAS DE BIENES Y SERVICIOS Y LOCACIONES NETAS",
            "presentaciones_con_ventas",
            "ventas_bienes_servicios_locaciones_netas",
        ),
        (
            "VENTAS GRAVADAS REALIZADAS EN EL MERCADO LOCAL A SUJETOS VINCULADOS",
            "ventas_gravadas_mercado_local_sujetos_vinculados_casos",
            "ventas_gravadas_mercado_local_sujetos_vinculados",
        ),
        (
            "VENTAS EXENTAS EN EL MERCADO LOCAL",
            "ventas_exentas_mercado_local_casos",
            "ventas_exentas_mercado_local",
        ),
        (
            "TOTAL DE EXPORTACIONES A SUJETOS RADICADOS O LOCALIZADOS EN JURISDICCIONES DE BAJA O NULA IMPOSICION",
            "exportaciones_baja_nula_imposicion_sin_detraer_derechos_casos",
            "exportaciones_baja_nula_imposicion_sin_detraer_derechos",
        ),
        (
            "TOTAL DE EXPORTACIONES EXENTAS",
            "exportaciones_exentas_casos",
            "exportaciones_exentas",
        ),
        (
            "OTRAS VENTAS GRAVADAS EN EL MERCADO LOCAL",
            "otras_ventas_gravadas_mercado_local_casos",
            "otras_ventas_gravadas_mercado_local",
        ),
        (
            "TOTAL DE EXPORTACIONES A SUJETOS VINCULADOS SIN DETRAER DERECHOS DE EXPORTACION",
            "exportaciones_vinculados_sin_detraer_derechos_excluye_baja_nula_casos",
            "exportaciones_vinculados_sin_detraer_derechos_excluye_baja_nula",
        ),
        (
            "TOTAL DE OTRAS EXPORTACIONES SIN DETRAER DERECHOS DE EXPORTACION",
            "otras_exportaciones_sin_detraer_derechos_casos",
            "otras_exportaciones_sin_detraer_derechos",
        ),
        (
            "TOTAL DE VENTAS, SERVICIOS Y LOCACIONES DEL EJERCICIO",
            "total_ventas_servicios_locaciones_ejercicio_casos",
            "total_ventas_servicios_locaciones_ejercicio",
        ),
        (
            "DERECHOS DE EXPORTACION",
            "derechos_exportacion_casos",
            "derechos_exportacion",
        ),
    )

    for column_index in range(max_columns):
        direct_text = _combined_header_text(header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        else:
            for concept_text, case_variable, amount_variable in paired_mappings:
                if concept_text in filled_text:
                    if "CASOS" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            case_variable,
                            "casos",
                            False,
                        )
                    elif "IMPORTE" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            amount_variable,
                            "millones_pesos_corrientes",
                            True,
                        )
                    break

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {"presentaciones_total"}
    optional_sales_detail_variables = {
        "derechos_exportacion_casos",
        "derechos_exportacion",
        "exportaciones_baja_nula_imposicion_sin_detraer_derechos_casos",
        "exportaciones_baja_nula_imposicion_sin_detraer_derechos",
        "exportaciones_exentas_casos",
        "exportaciones_exentas",
        "exportaciones_vinculados_sin_detraer_derechos_excluye_baja_nula_casos",
        "exportaciones_vinculados_sin_detraer_derechos_excluye_baja_nula",
        "otras_exportaciones_sin_detraer_derechos_casos",
        "otras_exportaciones_sin_detraer_derechos",
        "otras_ventas_gravadas_mercado_local_casos",
        "otras_ventas_gravadas_mercado_local",
        "total_ventas_servicios_locaciones_ejercicio_casos",
        "total_ventas_servicios_locaciones_ejercicio",
        "ventas_exentas_mercado_local_casos",
        "ventas_exentas_mercado_local",
        "ventas_gravadas_mercado_local_sujetos_vinculados_casos",
        "ventas_gravadas_mercado_local_sujetos_vinculados",
    }
    for _, case_variable, amount_variable in paired_mappings:
        if case_variable not in optional_sales_detail_variables:
            expected.add(case_variable)
        if amount_variable not in optional_sales_detail_variables:
            expected.add(amount_variable)

    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_231123_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.2.3.

    The table reports a monetary total for cost-linked expenses and paired
    `Casos`/`Importe` columns for each component.
    """

    max_columns = max((len(row) for row in header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}
    component_mappings = (
        (
            "DEPRECIACION BIENES DE USO",
            "depreciacion_bienes_uso_casos",
            "depreciacion_bienes_uso",
        ),
        (
            "HONORARIOS Y RETRIBUCIONES POR SERVICIOS",
            "honorarios_retribuciones_servicios_casos",
            "honorarios_retribuciones_servicios",
        ),
        (
            "OTROS GASTOS VINCULADOS AL COSTO",
            "otros_gastos_vinculados_al_costo_casos",
            "otros_gastos_vinculados_al_costo",
        ),
        (
            "SUELDOS, AGUINALDOS, GRATIFICACIONES Y CONTRIBUCIONES SOCIAL",
            "sueldos_aguinaldos_gratificaciones_contribuciones_social_casos",
            "sueldos_aguinaldos_gratificaciones_contribuciones_social",
        ),
    )

    for column_index in range(max_columns):
        direct_text = _combined_header_text(header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif (
            "GASTOS VINCULADOS AL COSTO" in filled_text
            and "TOTAL" in filled_text
            and "IMPORTE" in filled_text
        ):
            variable = VariableColumn(
                column_index,
                "gastos_vinculados_al_costo",
                "millones_pesos_corrientes",
                True,
            )
        else:
            for concept_text, case_variable, amount_variable in component_mappings:
                if concept_text in filled_text:
                    if "CASOS" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            case_variable,
                            "casos",
                            False,
                        )
                    elif "IMPORTE" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            amount_variable,
                            "millones_pesos_corrientes",
                            True,
                        )
                    break

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {
        "presentaciones_total",
        "gastos_vinculados_al_costo",
    }
    for _, case_variable, amount_variable in component_mappings:
        expected.add(case_variable)
        expected.add(amount_variable)

    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_231124_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.2.4.

    This table reports gross result as utility/loss pairs and then two expense
    concepts. The effective header starts at the row containing both
    `PRESENTACIONES` and `RESULTADO BRUTO`, because the generic bounds detector
    may include title rows above the merged spreadsheet header.
    """

    effective_header_rows = _trim_header_rows_from_markers(
        header_rows,
        ("PRESENTACIONES", "RESULTADO BRUTO"),
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            effective_header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif "RESULTADO BRUTO" in filled_text:
            if "UTILIDAD" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_bruto_utilidad_casos",
                    "casos",
                    False,
                )
            elif "UTILIDAD" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_bruto_utilidad",
                    "millones_pesos_corrientes",
                    True,
                )
            elif "PERDIDA" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_bruto_perdida_casos",
                    "casos",
                    False,
                )
            elif "PERDIDA" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_bruto_perdida",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "RESULTADO POR VENTA DE ACCIONES" in filled_text:
            if "UTILIDAD" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_venta_acciones_utilidad_casos",
                    "casos",
                    False,
                )
            elif "UTILIDAD" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_venta_acciones_utilidad",
                    "millones_pesos_corrientes",
                    True,
                )
            elif "PERDIDA" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_venta_acciones_perdida_casos",
                    "casos",
                    False,
                )
            elif "PERDIDA" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_venta_acciones_perdida",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "CARGO POR DEUDORES INCOBRABLES" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "cargo_deudores_incobrables_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "cargo_deudores_incobrables",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "GASTOS OPERATIVOS" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "gastos_operativos_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "gastos_operativos",
                    "millones_pesos_corrientes",
                    True,
                )

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {
        "presentaciones_total",
        "resultado_bruto_utilidad_casos",
        "resultado_bruto_utilidad",
        "resultado_bruto_perdida_casos",
        "resultado_bruto_perdida",
        "resultado_venta_acciones_utilidad_casos",
        "resultado_venta_acciones_utilidad",
        "resultado_venta_acciones_perdida_casos",
        "resultado_venta_acciones_perdida",
        "cargo_deudores_incobrables_casos",
        "cargo_deudores_incobrables",
        "gastos_operativos_casos",
        "gastos_operativos",
    }
    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_231125_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.2.5.

    The table expands operating expenses into component pairs. The generic
    bounds detector can include title rows, so the detector trims to the
    effective merged header before mapping columns.
    """

    effective_header_rows = _trim_header_rows_from_markers(
        header_rows,
        ("PRESENTACIONES", "GASTOS OPERATIVOS"),
    )
    header_text = " ".join(row_text(row) for row in header_rows)
    is_fiscal_2015 = "ANO FISCAL 2015" in header_text
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}
    component_mappings = (
        (
            "DEPRECIACION BIENES DE USO",
            "depreciacion_bienes_uso_casos",
            "depreciacion_bienes_uso",
        ),
        (
            "GASTOS DE REPRESENTACION",
            "gastos_representacion_casos",
            "gastos_representacion",
        ),
        (
            "HONORARIOS DIRECTORES",
            "honorarios_directores_casos",
            "honorarios_directores",
        ),
        (
            "HONORARIOS Y RETRIBUCIONES POR SERVICIOS",
            "honorarios_retribuciones_servicios_casos",
            "honorarios_retribuciones_servicios",
        ),
        (
            "OTROS GASTOS OPERATIVOS",
            "otros_gastos_operativos_casos",
            "otros_gastos_operativos",
        ),
        (
            "SUELDOS, AGUINALDOS, GRATIFICACIONES Y CONTRIBUCIONES SOCIAL",
            "sueldos_aguinaldos_gratificaciones_contribuciones_social_casos",
            "sueldos_aguinaldos_gratificaciones_contribuciones_social",
        ),
    )

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            effective_header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif (
            "GASTOS OPERATIVOS" in filled_text
            and "TOTAL" in filled_text
            and "IMPORTE" in filled_text
        ):
            if is_fiscal_2015:
                variable = VariableColumn(
                    column_index,
                    "gastos_operativos_casos",
                    "casos",
                    False,
                )
            else:
                variable = VariableColumn(
                    column_index,
                    "gastos_operativos",
                    "millones_pesos_corrientes",
                    True,
                )
        else:
            for concept_text, case_variable, amount_variable in component_mappings:
                if concept_text in filled_text:
                    if "CASOS" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            case_variable,
                            "casos",
                            False,
                        )
                    elif "IMPORTE" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            amount_variable,
                            "millones_pesos_corrientes",
                            True,
                        )
                    break

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {
        "presentaciones_total",
    }
    if is_fiscal_2015:
        expected.add("gastos_operativos_casos")
    else:
        expected.add("gastos_operativos")
    for _, case_variable, amount_variable in component_mappings:
        expected.add(case_variable)
        expected.add(amount_variable)

    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_231126_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.2.6.

    The table reports utility/quebranto pairs for four non-operating result
    concepts. Header rows are trimmed to the effective merged-header block
    before semantic column mapping.
    """

    effective_header_rows = _trim_header_rows_from_markers(
        header_rows,
        ("PRESENTACIONES", "RESULTADO POR INVERSIONES PERMANENTES"),
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}
    result_mappings = (
        (
            "RESULTADO POR INVERSIONES PERMANENTES",
            "resultado_inversiones_permanentes",
        ),
        (
            "RESULTADOS FINANCIEROS",
            "resultados_financieros",
        ),
        (
            "RESULTADOS POR CONTRATOS DERIVADOS",
            "resultados_contratos_derivados",
        ),
        (
            "OTROS INGRESOS Y EGRESOS",
            "otros_ingresos_egresos",
        ),
    )

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            effective_header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        else:
            for concept_text, variable_prefix in result_mappings:
                if concept_text in filled_text:
                    if "UTILIDAD" in filled_text and "CASOS" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            f"{variable_prefix}_utilidad_casos",
                            "casos",
                            False,
                        )
                    elif "UTILIDAD" in filled_text and "IMPORTE" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            f"{variable_prefix}_utilidad",
                            "millones_pesos_corrientes",
                            True,
                        )
                    elif "QUEBRANTO" in filled_text and "CASOS" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            f"{variable_prefix}_quebranto_casos",
                            "casos",
                            False,
                        )
                    elif "QUEBRANTO" in filled_text and "IMPORTE" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            f"{variable_prefix}_quebranto",
                            "millones_pesos_corrientes",
                            True,
                        )
                    break

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {"presentaciones_total"}
    for _, variable_prefix in result_mappings:
        expected.update(
            {
                f"{variable_prefix}_utilidad_casos",
                f"{variable_prefix}_utilidad",
                f"{variable_prefix}_quebranto_casos",
                f"{variable_prefix}_quebranto",
            }
        )

    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_231127_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.2.7.

    Fiscal year 2022 adds a games/gambling accounting-result concept. The
    detector treats that pair as optional source-observed columns rather than
    requiring it in earlier years.
    """

    effective_header_rows = _trim_header_rows_from_markers(
        header_rows,
        ("PRESENTACIONES", "RESULTADOS EXTRAORDINARIOS"),
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}
    has_games_result = any(
        "RESULTADO FINAL CONTABLE POR JUEGOS DE AZAR Y APUESTAS" in row_text(row)
        for row in effective_header_rows
    )

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            effective_header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif "RESULTADOS EXTRAORDINARIOS" in filled_text:
            if "UTILIDAD" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultados_extraordinarios_utilidad_casos",
                    "casos",
                    False,
                )
            elif "UTILIDAD" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultados_extraordinarios_utilidad",
                    "millones_pesos_corrientes",
                    True,
                )
            elif "QUEBRANTO" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultados_extraordinarios_quebranto_casos",
                    "casos",
                    False,
                )
            elif "QUEBRANTO" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultados_extraordinarios_quebranto",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "IMPUESTO A LAS GANANCIAS" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "impuesto_ganancias_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "impuesto_ganancias",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "RESULTADO FINAL CONTABLE POR JUEGOS DE AZAR Y APUESTAS" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_final_contable_juegos_azar_apuestas_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_final_contable_juegos_azar_apuestas",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "RESULTADO CONTABLE" in filled_text:
            if "UTILIDAD" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_contable_utilidad_casos",
                    "casos",
                    False,
                )
            elif "UTILIDAD" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_contable_utilidad",
                    "millones_pesos_corrientes",
                    True,
                )
            elif "PERDIDA" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_contable_perdida_casos",
                    "casos",
                    False,
                )
            elif "PERDIDA" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_contable_perdida",
                    "millones_pesos_corrientes",
                    True,
                )

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {
        "presentaciones_total",
        "resultados_extraordinarios_utilidad_casos",
        "resultados_extraordinarios_utilidad",
        "resultados_extraordinarios_quebranto_casos",
        "resultados_extraordinarios_quebranto",
        "impuesto_ganancias_casos",
        "impuesto_ganancias",
        "resultado_contable_utilidad_casos",
        "resultado_contable_utilidad",
        "resultado_contable_perdida_casos",
        "resultado_contable_perdida",
    }
    if has_games_result:
        expected.update(
            {
                "resultado_final_contable_juegos_azar_apuestas_casos",
                "resultado_final_contable_juegos_azar_apuestas",
            }
        )

    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_23113_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.3.

    Fiscal year 2020 has degraded subheaders for `resultado impositivo -
    perdida`: the data columns exist but the `Casos`/`Importe` labels are not
    both explicit. The detector uses the concept block and column position
    evidence to keep the extraction semantic instead of hard-coding row
    numbers.
    """

    effective_header_rows = _trim_header_rows_from_markers(
        header_rows,
        ("PRESENTACIONES", "IMPORTES QUE AUMENTAN LA UTILIDAD"),
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            effective_header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif "IMPORTES QUE AUMENTAN LA UTILIDAD O DISMINUYEN LA PERDIDA" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "importes_aumentan_utilidad_o_disminuyen_perdida_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "importes_aumentan_utilidad_o_disminuyen_perdida",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "IMPORTES QUE DISMINUYEN LA UTILIDAD O AUMENTAN LA PERDIDA" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "importes_disminuyen_utilidad_o_aumentan_perdida_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "importes_disminuyen_utilidad_o_aumentan_perdida",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "RESULTADO IMPOSITIVO" in filled_text:
            if "UTILIDAD" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_impositivo_utilidad_casos",
                    "casos",
                    False,
                )
            elif "UTILIDAD" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_impositivo_utilidad",
                    "millones_pesos_corrientes",
                    True,
                )
            elif "PERDIDA" in filled_text:
                if "CASOS" in direct_text or direct_text == "PERDIDA":
                    variable = VariableColumn(
                        column_index,
                        "resultado_impositivo_perdida_casos",
                        "casos",
                        False,
                    )
                elif "IMPORTE" in filled_text:
                    variable = VariableColumn(
                        column_index,
                        "resultado_impositivo_perdida",
                        "millones_pesos_corrientes",
                        True,
                    )
        elif "QUEBRANTO COMPUTABLE" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "quebranto_computable_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "quebranto_computable",
                    "millones_pesos_corrientes",
                    True,
                )

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {
        "presentaciones_total",
        "importes_aumentan_utilidad_o_disminuyen_perdida_casos",
        "importes_aumentan_utilidad_o_disminuyen_perdida",
        "importes_disminuyen_utilidad_o_aumentan_perdida_casos",
        "importes_disminuyen_utilidad_o_aumentan_perdida",
        "resultado_impositivo_utilidad_casos",
        "resultado_impositivo_utilidad",
        "resultado_impositivo_perdida_casos",
        "resultado_impositivo_perdida",
    }
    if any(
        variable.variable_name in {"quebranto_computable_casos", "quebranto_computable"}
        for variable in variables_by_column.values()
    ):
        expected.update({"quebranto_computable_casos", "quebranto_computable"})
    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_23114_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.4."""

    effective_header_rows = _trim_header_rows_from_markers(
        header_rows,
        ("ACTIVIDAD ECONOMICA", "PRESENTACIONES"),
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}
    paired_mappings = (
        ("RESULTADO NETO FINAL", "resultado_neto_final"),
        ("RESULTADO ATRIBUIBLE A SOCIOS", "resultado_atribuible_socios"),
        ("RESULTADO NETO", "resultado_neto"),
    )

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            effective_header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif "IMPUESTO DETERMINADO" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "impuesto_determinado_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "impuesto_determinado",
                    "millones_pesos_corrientes",
                    True,
                )
        else:
            for concept_text, variable_prefix in paired_mappings:
                if concept_text in filled_text:
                    if "UTILIDAD" in filled_text and "CASOS" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            f"{variable_prefix}_utilidad_casos",
                            "casos",
                            False,
                        )
                    elif "UTILIDAD" in filled_text and "IMPORTE" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            f"{variable_prefix}_utilidad",
                            "millones_pesos_corrientes",
                            True,
                        )
                    elif "PERDIDA" in filled_text and "CASOS" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            f"{variable_prefix}_perdida_casos",
                            "casos",
                            False,
                        )
                    elif "PERDIDA" in filled_text and "IMPORTE" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            f"{variable_prefix}_perdida",
                            "millones_pesos_corrientes",
                            True,
                        )
                    break

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {
        "presentaciones_total",
        "impuesto_determinado_casos",
        "impuesto_determinado",
    }
    for _, variable_prefix in paired_mappings:
        expected.update(
            {
                f"{variable_prefix}_utilidad_casos",
                f"{variable_prefix}_utilidad",
                f"{variable_prefix}_perdida_casos",
                f"{variable_prefix}_perdida",
            }
        )

    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_231151_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.5.1."""

    effective_header_rows = _trim_header_rows_from_markers(
        header_rows,
        ("ACTIVIDAD ECONOMICA", "PRESENTACIONES"),
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}
    paired_mappings = (
        ("ACTIVO TOTAL", "activo_total"),
        ("DISPONIBILIDADES", "activo_disponibilidades"),
        ("CREDITOS", "activo_creditos"),
        ("BIENES DE CAMBIO", "activo_bienes_cambio"),
        ("INVERSIONES", "activo_inversiones"),
        ("BIENES DE USO", "activo_bienes_uso"),
        ("BIENES INTANGIBLES", "activo_bienes_intangibles"),
        ("OBRAS EN CONSTRUCCION", "activo_obras_construccion"),
    )

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            effective_header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        else:
            for concept_text, variable_prefix in paired_mappings:
                if concept_text in filled_text:
                    if "CASOS" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            f"{variable_prefix}_casos",
                            "casos",
                            False,
                        )
                    elif "IMPORTE" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            variable_prefix,
                            "millones_pesos_corrientes",
                            True,
                        )
                    break

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {"presentaciones_total"}
    for _, variable_prefix in paired_mappings:
        if variable_prefix == "activo_obras_construccion" and not any(
            variable.variable_name in {
                "activo_obras_construccion_casos",
                "activo_obras_construccion",
            }
            for variable in variables_by_column.values()
        ):
            continue
        expected.update({f"{variable_prefix}_casos", variable_prefix})

    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_2311511_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.5.1.1."""

    effective_header_rows = _trim_header_rows_from_markers(
        header_rows,
        ("ACTIVIDAD ECONOMICA", "PRESENTACIONES"),
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}
    paired_mappings = (
        ("TOTAL BANCOS", "activo_total_bancos"),
        ("DISPONIBILIDADES TOTAL", "activo_disponibilidades"),
        ("CHEQUES EN CARTERA", "activo_cheques_cartera"),
        ("EFECTIVO MONEDA NACIONAL", "activo_efectivo_moneda_nacional"),
        ("EFECTIVO MONEDA EXTRANJERA", "activo_efectivo_moneda_extranjera"),
    )

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            effective_header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        else:
            for concept_text, variable_prefix in paired_mappings:
                if concept_text in filled_text:
                    if "CASOS" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            f"{variable_prefix}_casos",
                            "casos",
                            False,
                        )
                    elif "IMPORTE" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            variable_prefix,
                            "millones_pesos_corrientes",
                            True,
                        )
                    break

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {"presentaciones_total"}
    for _, variable_prefix in paired_mappings:
        expected.update({f"{variable_prefix}_casos", variable_prefix})

    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_2311512_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.5.1.2."""

    effective_header_rows = _trim_header_rows_from_markers(
        header_rows,
        ("ACTIVIDAD ECONOMICA", "PRESENTACIONES"),
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}
    paired_mappings = (
        ("CREDITOS TOTAL", "activo_creditos"),
        ("PREVISIONES", "activo_creditos_previsiones"),
        ("DEUDORES POR VTAS SERVICIOS", "activo_creditos_deudores_ventas_servicios"),
        (
            "SOC. CONTROLADA, CONTROLANTE Y VINCULADA",
            "activo_creditos_soc_controlada_controlante_vinculada",
        ),
        ("CUENTAS PARTICULARES SOCIOS", "activo_creditos_cuentas_particulares_socios"),
        ("OTROS", "activo_creditos_otros"),
    )

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            effective_header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        else:
            for concept_text, variable_prefix in paired_mappings:
                if concept_text in filled_text:
                    if "CASOS" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            f"{variable_prefix}_casos",
                            "casos",
                            False,
                        )
                    elif "IMPORTE" in filled_text:
                        variable = VariableColumn(
                            column_index,
                            variable_prefix,
                            "millones_pesos_corrientes",
                            True,
                        )
                    break

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {"presentaciones_total"}
    for _, variable_prefix in paired_mappings:
        expected.update({f"{variable_prefix}_casos", variable_prefix})

    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_2311513_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.5.1.3."""

    return _detect_p0_paired_columns(
        header_rows,
        (
            ("BIENES DE CAMBIO TOTAL", "activo_bienes_cambio"),
            ("MATERIAS PRIMAS", "activo_bienes_cambio_materias_primas"),
            ("MERCADERIAS", "activo_bienes_cambio_mercaderias"),
            ("PRODUCTOS EN PROCESO", "activo_bienes_cambio_productos_en_proceso"),
            ("PRODUCTOS TERMINADOS", "activo_bienes_cambio_productos_terminados"),
            ("OTROS", "activo_bienes_cambio_otros"),
        ),
    )


def detect_p0_2311514_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.5.1.4."""

    return _detect_p0_paired_columns(
        header_rows,
        (
            ("BIENES DE USO TOTAL", "activo_bienes_uso"),
            ("INMUEBLES", "activo_bienes_uso_inmuebles"),
            ("RODADOS", "activo_bienes_uso_rodados"),
            ("INSTALACIONES", "activo_bienes_uso_instalaciones"),
            ("OTROS BIENES DE USO", "activo_bienes_uso_otros"),
        ),
    )


def detect_p0_231152_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.5.2."""

    return _detect_p0_paired_columns(
        header_rows,
        (
            ("PASIVO TOTAL", "pasivo_total"),
            ("DEUDAS", "pasivo_deudas"),
            ("PREVISIONES", "pasivo_previsiones"),
        ),
    )


def detect_p0_2311521_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.5.2.1."""

    return _detect_p0_paired_columns(
        header_rows,
        (
            ("DEUDAS TOTAL", "pasivo_deudas"),
            ("BANCARIAS Y FINANCIERAS", "pasivo_deudas_bancarias_financieras"),
            ("COMERCIALES", "pasivo_deudas_comerciales"),
            (
                "SOC. CONTROLADA, CONTROLANTE Y VINCULADA",
                "pasivo_deudas_soc_controlada_controlante_vinculada",
            ),
            ("CTA PARTICULARES DE LOS SOCIOS", "pasivo_deudas_cta_particulares_socios"),
            ("FISCALES", "pasivo_deudas_fiscales"),
            ("SOCIALES", "pasivo_deudas_sociales"),
            ("OTRAS DEUDAS DEL EXTERIOR", "pasivo_deudas_otras_exterior"),
            ("OTRAS DEUDAS LOCALES", "pasivo_deudas_otras_locales"),
        ),
    )


def detect_p0_231153_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.5.3."""

    effective_header_rows = _trim_header_rows_from_exact_cell(
        header_rows,
        "ACTIVIDAD ECONOMICA",
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    def header_parts(column_index: int) -> tuple[str, str, str]:
        """Return top concept, subheading, and unit without leaking across groups."""

        top_text = ""
        sub_text = ""
        for current_column in range(column_index + 1):
            top_cell = ""
            sub_cell = ""
            if effective_header_rows and current_column < len(effective_header_rows[0]):
                top_cell = normalize_text(effective_header_rows[0][current_column])
            if len(effective_header_rows) > 1 and current_column < len(effective_header_rows[1]):
                sub_cell = normalize_text(effective_header_rows[1][current_column])
            if top_cell:
                top_text = top_cell
                sub_text = ""
            if sub_cell:
                sub_text = sub_cell
        unit_text = ""
        if len(effective_header_rows) > 2 and column_index < len(effective_header_rows[2]):
            unit_text = normalize_text(effective_header_rows[2][column_index])
        return top_text, sub_text, unit_text

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        top_text, sub_text, unit_text = header_parts(column_index)
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue
        if not direct_text:
            continue

        variable_prefix: str | None = None
        if direct_text == "PRESENTACIONES":
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
            continue
        if top_text == "PATRIMONIO NETO AL INICIO":
            variable_prefix = "patrimonio_neto_inicio"
            if sub_text == "POSITIVO":
                variable_prefix = "patrimonio_neto_inicio_positivo"
            elif sub_text == "NEGATIVO":
                variable_prefix = "patrimonio_neto_inicio_negativo"
        elif top_text == "PATRIMONIO NETO AL CIERRE":
            variable_prefix = "patrimonio_neto_cierre"
            if sub_text == "POSITIVO":
                variable_prefix = "patrimonio_neto_cierre_positivo"
            elif sub_text == "NEGATIVO":
                variable_prefix = "patrimonio_neto_cierre_negativo"
        elif top_text == "AUMENTOS":
            variable_prefix = "patrimonio_neto_aumentos"
        elif top_text == "DISMINUCIONES":
            variable_prefix = "patrimonio_neto_disminuciones"
        elif top_text == "AJUSTE DE EJERCICIOS ANTERIORES":
            if sub_text == "POSITIVO":
                variable_prefix = "patrimonio_neto_ajuste_ejercicios_anteriores_positivo"
            elif sub_text == "NEGATIVO":
                variable_prefix = "patrimonio_neto_ajuste_ejercicios_anteriores_negativo"
        elif top_text.startswith("RESULTADO FINAL DEL EJERCICIO CONTABLE"):
            if sub_text == "BENEFICIO":
                variable_prefix = "resultado_final_ejercicio_contable_beneficio"
            elif sub_text == "PERDIDA":
                variable_prefix = "resultado_final_ejercicio_contable_perdida"

        variable: VariableColumn | None = None
        if variable_prefix is not None:
            if unit_text == "CASOS":
                variable = VariableColumn(
                    column_index,
                    f"{variable_prefix}_casos",
                    "casos",
                    False,
                )
            elif unit_text == "IMPORTE" or (
                not unit_text
                and top_text in {"AUMENTOS", "DISMINUCIONES"}
            ):
                variable = VariableColumn(
                    column_index,
                    variable_prefix,
                    "millones_pesos_corrientes",
                    True,
                )
        if variable is not None:
            variables_by_column[column_index] = variable

    detected = {variable.variable_name for variable in variables_by_column.values()}
    expected = {
        "presentaciones_total",
        "patrimonio_neto_aumentos",
        "patrimonio_neto_disminuciones",
        "patrimonio_neto_ajuste_ejercicios_anteriores_positivo_casos",
        "patrimonio_neto_ajuste_ejercicios_anteriores_positivo",
        "patrimonio_neto_ajuste_ejercicios_anteriores_negativo_casos",
        "patrimonio_neto_ajuste_ejercicios_anteriores_negativo",
    }
    for prefix in ("patrimonio_neto_inicio", "patrimonio_neto_cierre"):
        if {f"{prefix}_positivo_casos", f"{prefix}_positivo"} & detected:
            expected.update(
                {
                    f"{prefix}_positivo_casos",
                    f"{prefix}_positivo",
                    f"{prefix}_negativo_casos",
                    f"{prefix}_negativo",
                }
            )
        else:
            expected.update({f"{prefix}_casos", prefix})
    if "patrimonio_neto_aumentos_casos" in detected:
        expected.add("patrimonio_neto_aumentos_casos")
    if "patrimonio_neto_disminuciones_casos" in detected:
        expected.add("patrimonio_neto_disminuciones_casos")
    if any(
        variable_name.startswith("resultado_final_ejercicio_contable")
        for variable_name in detected
    ):
        expected.update(
            {
                "resultado_final_ejercicio_contable_beneficio_casos",
                "resultado_final_ejercicio_contable_beneficio",
                "resultado_final_ejercicio_contable_perdida_casos",
                "resultado_final_ejercicio_contable_perdida",
            }
        )

    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p0_2311531_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.5.3.1."""

    return _detect_p0_paired_columns(
        header_rows,
        (
            ("CAPITALIZACIONES", "patrimonio_neto_aumentos_capitalizaciones"),
            (
                "TOTAL APORTES DE CAPITAL",
                "patrimonio_neto_aumentos_aportes_capital",
            ),
            ("AUMENTOS TOTAL", "patrimonio_neto_aumentos"),
            ("OTROS", "patrimonio_neto_aumentos_otros"),
        ),
        markers=("ACTIVIDAD ECONOMICA",),
        trim_to_exact_activity_header=True,
    )


def detect_p0_2311532_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect activity and value columns for P0 table 2.3.1.1.5.3.2."""

    return _detect_p0_paired_columns(
        header_rows,
        (
            ("REDUCCION DE CAPITAL", "patrimonio_neto_disminuciones_reduccion_capital"),
            ("TOTAL HONORARIOS", "patrimonio_neto_disminuciones_honorarios"),
            (
                "TOTAL DIVIDENDOS EN EFECTIVO / ESPECIE",
                "patrimonio_neto_disminuciones_dividendos_efectivo_especie",
            ),
            ("DISMINUCIONES TOTAL", "patrimonio_neto_disminuciones"),
            ("OTROS", "patrimonio_neto_disminuciones_otros"),
        ),
        markers=("ACTIVIDAD ECONOMICA",),
        trim_to_exact_activity_header=True,
    )


def detect_p5_33111_legacy_summary_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect P5 legacy summary columns with `ganancia neta imponible` cases."""

    effective_header_rows = _trim_header_rows_from_exact_cell(
        header_rows,
        "ACTIVIDAD ECONOMICA",
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    for column_index in range(max_columns):
        text = _combined_header_text(effective_header_rows, column_index)
        if not text:
            continue
        if "ACTIVIDAD ECONOMICA" in text:
            activity_column = column_index
            continue
        if "PRESENTACIONES" in text and "TOTAL" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif text.startswith("CON VENTAS"):
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "presentaciones_con_ventas",
                "casos",
                False,
            )
        elif text.startswith("CON GANANCIA NETA IMPONIBLE"):
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "presentaciones_con_ganancia_neta_imponible",
                "casos",
                False,
            )
        elif "VENTAS DE BIENES Y SERVICIOS Y LOCACIONES NETAS" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "ventas_bienes_servicios_locaciones_netas",
                "millones_pesos_corrientes",
                True,
            )
        elif "IMPUESTO DETERMINADO" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "impuesto_determinado",
                "millones_pesos_corrientes",
                True,
            )
        elif "GANANCIA NETA IMPONIBLE" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "ganancia_neta_imponible",
                "millones_pesos_corrientes",
                True,
            )

    expected = {
        "presentaciones_total",
        "presentaciones_con_ventas",
        "presentaciones_con_ganancia_neta_imponible",
        "ventas_bienes_servicios_locaciones_netas",
        "ganancia_neta_imponible",
        "impuesto_determinado",
    }
    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p5_33112_legacy_results_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect P5 legacy combined results table 3.3.1.1.2.

    Fiscal years 1999-2000 combine sales, costs, gross result and final
    accounting result in one source table.
    """

    effective_header_rows = _trim_header_rows_from_markers(
        header_rows,
        ("PRESENTACIONES", "RESULTADO FINAL DEL EJERCICIO"),
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            effective_header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if direct_text == "PRESENTACIONES":
            variable = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif "VENTAS DE BIENES Y SERVICIOS Y LOCACIONES NETAS" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "presentaciones_con_ventas",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "ventas_bienes_servicios_locaciones_netas",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "COSTOS" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "costos_total_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "costos_total",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "RESULTADO BRUTO" in filled_text:
            if "UTILIDAD" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_bruto_utilidad_casos",
                    "casos",
                    False,
                )
            elif "UTILIDAD" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_bruto_utilidad",
                    "millones_pesos_corrientes",
                    True,
                )
            elif "PERDIDA" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_bruto_perdida_casos",
                    "casos",
                    False,
                )
            elif "PERDIDA" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_bruto_perdida",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "RESULTADO FINAL DEL EJERCICIO" in filled_text:
            if "UTILIDAD" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_contable_utilidad_casos",
                    "casos",
                    False,
                )
            elif "UTILIDAD" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_contable_utilidad",
                    "millones_pesos_corrientes",
                    True,
                )
            elif "PERDIDA" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_contable_perdida_casos",
                    "casos",
                    False,
                )
            elif "PERDIDA" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_contable_perdida",
                    "millones_pesos_corrientes",
                    True,
                )

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {
        "presentaciones_total",
        "presentaciones_con_ventas",
        "ventas_bienes_servicios_locaciones_netas",
        "costos_total_casos",
        "costos_total",
        "resultado_bruto_utilidad_casos",
        "resultado_bruto_utilidad",
        "resultado_bruto_perdida_casos",
        "resultado_bruto_perdida",
        "resultado_contable_utilidad_casos",
        "resultado_contable_utilidad",
        "resultado_contable_perdida_casos",
        "resultado_contable_perdida",
    }
    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p5_33113_legacy_tax_result_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect P5 legacy tax-result table with `Ganancia` and `Quebranto`."""

    effective_header_rows = _trim_header_rows_from_markers(
        header_rows,
        ("ACTIVIDAD ECONOMICA", "GANANCIA"),
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    for column_index in range(max_columns):
        direct_text = _combined_header_text(effective_header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            effective_header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if "GANANCIA" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_impositivo_utilidad_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_impositivo_utilidad",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "QUEBRANTO" in filled_text:
            if "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_impositivo_perdida_casos",
                    "casos",
                    False,
                )
            elif "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_impositivo_perdida",
                    "millones_pesos_corrientes",
                    True,
                )

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {
        "resultado_impositivo_utilidad_casos",
        "resultado_impositivo_utilidad",
        "resultado_impositivo_perdida_casos",
        "resultado_impositivo_perdida",
    }
    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p5_33114_legacy_balance_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect P5 legacy aggregate balance sheet table 3.3.1.1.4."""

    effective_header_rows = _trim_header_rows_from_markers(
        header_rows,
        ("ACTIVIDAD ECONOMICA", "PATRIMONIO NETO AL CIERRE"),
    )
    max_columns = max((len(row) for row in effective_header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    for column_index in range(max_columns):
        text = _combined_header_text(effective_header_rows, column_index)
        if not text:
            continue
        if "ACTIVIDAD ECONOMICA" in text:
            activity_column = column_index
        elif text == "PRESENTACIONES":
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif text == "ACTIVO":
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "activo_total",
                "millones_pesos_corrientes",
                True,
            )
        elif text == "PASIVO":
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "pasivo_total",
                "millones_pesos_corrientes",
                True,
            )
        elif text == "PATRIMONIO NETO AL CIERRE":
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "patrimonio_neto_cierre",
                "millones_pesos_corrientes",
                True,
            )
        elif text == "PATRIMONIO NETO AL INICIO":
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "patrimonio_neto_inicio",
                "millones_pesos_corrientes",
                True,
            )

    expected = {
        "presentaciones_total",
        "activo_total",
        "pasivo_total",
        "patrimonio_neto_cierre",
        "patrimonio_neto_inicio",
    }
    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p6_legacy_summary_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect P6 summary columns with split legacy XLS headers."""

    max_columns = max((len(row) for row in header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    for column_index in range(max_columns):
        text = _combined_header_text(header_rows, column_index)
        if not text:
            continue
        if "ACTIVIDAD ECONOMICA" in text:
            activity_column = column_index
            continue
        if "PRESENTACIONES" in text and "TOTAL" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "presentaciones_total",
                "casos",
                False,
            )
        elif "CON VENTAS" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "presentaciones_con_ventas",
                "casos",
                False,
            )
        elif "CON GANANCIA NETA IMPONIBLE" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "presentaciones_con_ganancia_neta_imponible",
                "casos",
                False,
            )
        elif "VENTAS DE BIENES Y SERVICIOS Y LOCACIONES NETAS" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "ventas_bienes_servicios_locaciones_netas",
                "millones_pesos_corrientes",
                True,
            )
        elif "IMPUESTO DETERMINADO" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "impuesto_determinado",
                "millones_pesos_corrientes",
                True,
            )
        elif "GANANCIA NETA" in text and "IMPONIBLE" in text:
            variables_by_column[column_index] = VariableColumn(
                column_index,
                "ganancia_neta_imponible",
                "millones_pesos_corrientes",
                True,
            )

    expected = {
        "presentaciones_total",
        "presentaciones_con_ventas",
        "presentaciones_con_ganancia_neta_imponible",
        "ventas_bienes_servicios_locaciones_netas",
        "ganancia_neta_imponible",
        "impuesto_determinado",
    }
    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


def detect_p6_44113_tax_adjustment_columns(
    header_rows: Sequence[Sequence[Any]],
) -> tuple[int, list[VariableColumn]]:
    """Detect P6 fiscal-1997 tax-adjustment table 4.4.1.1.3 columns."""

    max_columns = max((len(row) for row in header_rows), default=0)
    activity_column: int | None = None
    variables_by_column: dict[int, VariableColumn] = {}

    for column_index in range(max_columns):
        direct_text = _combined_header_text(header_rows, column_index)
        filled_text = _forward_filled_column_header_text(
            header_rows,
            column_index,
            max_columns,
        )
        if "ACTIVIDAD ECONOMICA" in direct_text:
            activity_column = column_index
            continue

        variable: VariableColumn | None = None
        if "AJUSTES POR REEXPRESION A MONEDA CONSTANTE" in filled_text:
            if "NEGATIVO" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "ajustes_reexpresion_moneda_constante_negativo_casos",
                    "casos",
                    False,
                )
            elif "NEGATIVO" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "ajustes_reexpresion_moneda_constante_negativo",
                    "millones_pesos_corrientes",
                    True,
                )
            elif "POSITIVO" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "ajustes_reexpresion_moneda_constante_positivo_casos",
                    "casos",
                    False,
                )
            elif "POSITIVO" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "ajustes_reexpresion_moneda_constante_positivo",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "RESULTADO PARA FINES FISCALES" in filled_text:
            if "UTILIDAD" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_fines_fiscales_sin_reexpresar_utilidad_casos",
                    "casos",
                    False,
                )
            elif "UTILIDAD" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_fines_fiscales_sin_reexpresar_utilidad",
                    "millones_pesos_corrientes",
                    True,
                )
            elif "PERDIDA" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_fines_fiscales_sin_reexpresar_perdida_casos",
                    "casos",
                    False,
                )
            elif "PERDIDA" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_fines_fiscales_sin_reexpresar_perdida",
                    "millones_pesos_corrientes",
                    True,
                )
        elif (
            "RESULTADO IMPOSITIVO" in direct_text
            or "GANANCIA" in direct_text
            or "QUEBRANTO" in filled_text
        ):
            if "QUEBRANTO" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_impositivo_perdida_casos",
                    "casos",
                    False,
                )
            elif "QUEBRANTO" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_impositivo_perdida",
                    "millones_pesos_corrientes",
                    True,
                )
            elif "GANANCIA" in filled_text and "CASOS" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_impositivo_utilidad_casos",
                    "casos",
                    False,
                )
            elif "GANANCIA" in filled_text and "IMPORTE" in filled_text:
                variable = VariableColumn(
                    column_index,
                    "resultado_impositivo_utilidad",
                    "millones_pesos_corrientes",
                    True,
                )
        elif "IMPORTES QUE AUMENTAN Y/O DISMINUYEN" in filled_text:
            if "AUMENTAN LA UTILIDAD O DISMINUYEN LA PERDIDA" in filled_text:
                if "CASOS" in filled_text:
                    variable = VariableColumn(
                        column_index,
                        "ajustes_impositivos_aumentan_utilidad_disminuyen_perdida_casos",
                        "casos",
                        False,
                    )
                elif "IMPORTE" in filled_text:
                    variable = VariableColumn(
                        column_index,
                        "ajustes_impositivos_aumentan_utilidad_disminuyen_perdida",
                        "millones_pesos_corrientes",
                        True,
                    )
            elif "DISMINUYEN LA UTILIDAD O AUMENTAN LA PERDIDA" in filled_text:
                if "CASOS" in filled_text:
                    variable = VariableColumn(
                        column_index,
                        "ajustes_impositivos_disminuyen_utilidad_aumentan_perdida_casos",
                        "casos",
                        False,
                    )
                elif "IMPORTE" in filled_text:
                    variable = VariableColumn(
                        column_index,
                        "ajustes_impositivos_disminuyen_utilidad_aumentan_perdida",
                        "millones_pesos_corrientes",
                        True,
                    )

        if variable is not None:
            variables_by_column[column_index] = variable

    expected = {
        "ajustes_reexpresion_moneda_constante_positivo_casos",
        "ajustes_reexpresion_moneda_constante_positivo",
        "ajustes_reexpresion_moneda_constante_negativo_casos",
        "ajustes_reexpresion_moneda_constante_negativo",
        "resultado_fines_fiscales_sin_reexpresar_utilidad_casos",
        "resultado_fines_fiscales_sin_reexpresar_utilidad",
        "resultado_fines_fiscales_sin_reexpresar_perdida_casos",
        "resultado_fines_fiscales_sin_reexpresar_perdida",
        "ajustes_impositivos_aumentan_utilidad_disminuyen_perdida_casos",
        "ajustes_impositivos_aumentan_utilidad_disminuyen_perdida",
        "ajustes_impositivos_disminuyen_utilidad_aumentan_perdida_casos",
        "ajustes_impositivos_disminuyen_utilidad_aumentan_perdida",
        "resultado_impositivo_utilidad_casos",
        "resultado_impositivo_utilidad",
        "resultado_impositivo_perdida_casos",
        "resultado_impositivo_perdida",
    }
    detected = {variable.variable_name for variable in variables_by_column.values()}
    missing = sorted(expected - detected)
    if activity_column is None:
        raise ValueError("Could not detect the activity column.")
    if missing:
        raise ValueError(f"Could not detect variable columns: {', '.join(missing)}")

    return activity_column, [
        variables_by_column[column_index]
        for column_index in sorted(variables_by_column)
    ]


P0_ACTIVITY_COLUMN_DETECTORS = {
    P0_ACTIVITY_SUMMARY_TABLE_ID: detect_p0_23111_columns,
    P0_ACTIVITY_COSTS_TABLE_ID: detect_p0_231121_columns,
    P0_ACTIVITY_SALES_DETAIL_TABLE_ID: detect_p0_231122_columns,
    P0_ACTIVITY_COST_LINKED_EXPENSES_TABLE_ID: detect_p0_231123_columns,
    P0_ACTIVITY_GROSS_RESULT_TABLE_ID: detect_p0_231124_columns,
    P0_ACTIVITY_OPERATING_EXPENSES_TABLE_ID: detect_p0_231125_columns,
    P0_ACTIVITY_OTHER_RESULTS_TABLE_ID: detect_p0_231126_columns,
    P0_ACTIVITY_ACCOUNTING_RESULT_TABLE_ID: detect_p0_231127_columns,
    P0_ACTIVITY_TAX_RESULT_TABLE_ID: detect_p0_23113_columns,
    P0_ACTIVITY_TAX_DETERMINATION_TABLE_ID: detect_p0_23114_columns,
    P0_ACTIVITY_ASSETS_TABLE_ID: detect_p0_231151_columns,
    P0_ACTIVITY_LIABILITIES_TABLE_ID: detect_p0_231152_columns,
    P0_ACTIVITY_EQUITY_TABLE_ID: detect_p0_231153_columns,
}


def _p3_column_detector(table_id: str, fiscal_year: int) -> Any:
    if fiscal_year == 2008:
        fiscal_2008_detectors = {
            P0_ACTIVITY_COSTS_TABLE_ID: detect_p3_2008_231121_columns,
            P0_ACTIVITY_SALES_DETAIL_TABLE_ID: detect_p0_231124_columns,
            P0_ACTIVITY_COST_LINKED_EXPENSES_TABLE_ID: detect_p0_231126_columns,
            P0_ACTIVITY_GROSS_RESULT_TABLE_ID: detect_p0_231127_columns,
        }
        if table_id in fiscal_2008_detectors:
            return fiscal_2008_detectors[table_id]
    return P0_ACTIVITY_COLUMN_DETECTORS[table_id]


def _p4_column_detector(table_id: str) -> Any:
    p4_detectors = {
        P0_ACTIVITY_COSTS_TABLE_ID: detect_p3_2008_231121_columns,
        P0_ACTIVITY_SALES_DETAIL_TABLE_ID: detect_p0_231124_columns,
        P0_ACTIVITY_COST_LINKED_EXPENSES_TABLE_ID: detect_p0_231126_columns,
        P0_ACTIVITY_GROSS_RESULT_TABLE_ID: detect_p0_231127_columns,
    }
    return p4_detectors.get(table_id, P0_ACTIVITY_COLUMN_DETECTORS[table_id])


def _p5_activity_table_ids(fiscal_year: int) -> tuple[str, ...]:
    if fiscal_year in {1999, 2000}:
        return P5_ACTIVITY_TABLE_IDS_1999_2000
    if fiscal_year == 2001:
        return P5_ACTIVITY_TABLE_IDS_2001
    raise ValueError(f"Unsupported P5 fiscal year: {fiscal_year}")


def _p5_column_detector(table_id: str, fiscal_year: int) -> Any:
    if fiscal_year in {1999, 2000}:
        legacy_detectors = {
            P5_LEGACY_ACTIVITY_SUMMARY_TABLE_ID: detect_p5_33111_legacy_summary_columns,
            P5_LEGACY_ACTIVITY_RESULTS_TABLE_ID: detect_p5_33112_legacy_results_columns,
            P5_LEGACY_ACTIVITY_TAX_RESULT_TABLE_ID: detect_p5_33113_legacy_tax_result_columns,
            P5_LEGACY_ACTIVITY_BALANCE_TABLE_ID: detect_p5_33114_legacy_balance_columns,
        }
        return legacy_detectors[table_id]

    fiscal_2001_detectors = {
        P5_LEGACY_ACTIVITY_SUMMARY_TABLE_ID: detect_p0_23111_columns,
        P5_LEGACY_ACTIVITY_COSTS_TABLE_ID: detect_p3_2008_231121_columns,
        P5_LEGACY_ACTIVITY_GROSS_RESULT_TABLE_ID: detect_p0_231124_columns,
        P5_LEGACY_ACTIVITY_OTHER_RESULTS_TABLE_ID: detect_p0_231126_columns,
        P5_LEGACY_ACTIVITY_ACCOUNTING_RESULT_TABLE_ID: detect_p0_231127_columns,
        P5_LEGACY_ACTIVITY_TAX_RESULT_TABLE_ID: detect_p0_23113_columns,
        P5_LEGACY_ACTIVITY_BALANCE_TABLE_ID: detect_p0_23114_columns,
        P5_LEGACY_ACTIVITY_ASSETS_TABLE_ID: detect_p0_231151_columns,
        P5_LEGACY_ACTIVITY_LIABILITIES_TABLE_ID: detect_p0_231152_columns,
        P5_LEGACY_ACTIVITY_EQUITY_TABLE_ID: detect_p0_231153_columns,
    }
    return fiscal_2001_detectors[table_id]


def _p6_activity_table_ids(fiscal_year: int) -> tuple[str, ...]:
    if fiscal_year == 1997:
        return P6_ACTIVITY_TABLE_IDS_1997
    if fiscal_year == 1998:
        return P6_ACTIVITY_TABLE_IDS_1998
    raise ValueError(f"Unsupported P6 fiscal year: {fiscal_year}")


def _p6_column_detector(table_id: str, fiscal_year: int) -> Any:
    if fiscal_year == 1997:
        detectors = {
            P6_1997_ACTIVITY_SUMMARY_TABLE_ID: detect_p6_legacy_summary_columns,
            P6_1997_ACTIVITY_RESULTS_TABLE_ID: detect_p5_33112_legacy_results_columns,
            P6_1997_ACTIVITY_TAX_ADJUSTMENTS_TABLE_ID: detect_p6_44113_tax_adjustment_columns,
            P6_1997_ACTIVITY_BALANCE_TABLE_ID: detect_p5_33114_legacy_balance_columns,
        }
        return detectors[table_id]
    if fiscal_year == 1998:
        detectors = {
            P6_1998_ACTIVITY_SUMMARY_TABLE_ID: detect_p6_legacy_summary_columns,
            P6_1998_ACTIVITY_RESULTS_TABLE_ID: detect_p5_33112_legacy_results_columns,
            P6_1998_ACTIVITY_TAX_RESULT_TABLE_ID: detect_p5_33113_legacy_tax_result_columns,
            P6_1998_ACTIVITY_BALANCE_TABLE_ID: detect_p5_33114_legacy_balance_columns,
        }
        return detectors[table_id]
    raise ValueError(f"Unsupported P6 fiscal year: {fiscal_year}")


P6_BROAD_ACTIVITY_PREFIXES = (
    ("AGRICULTURA, CAZA, SILVICULTURA Y PESCA", "AGRICULTURA_CAZA_SILVICULTURA_PESCA"),
    ("EXPLOTACION DE MINAS Y CANTERAS", "EXPLOTACION_MINAS_CANTERAS"),
    ("INDUSTRIAS MANUFACTURERAS", "INDUSTRIAS_MANUFACTURERAS"),
    ("ELECTRICIDAD, GAS Y AGUA", "ELECTRICIDAD_GAS_AGUA"),
    ("CONSTRUCCION", "CONSTRUCCION"),
    (
        "COMERCIO AL POR MAYOR Y AL POR MENOR Y RESTAURANTES Y HOTELES",
        "COMERCIO_RESTAURANTES_HOTELES",
    ),
    ("TRANSPORTES, ALMACENAMIENTO Y COMUNICACIONES", "TRANSPORTE_ALMACENAMIENTO_COMUNICACIONES"),
    ("ESTABLECIMIENTOS FINANCIEROS, SEGUROS", "FINANZAS_SEGUROS_INMUEBLES_SERVICIOS"),
    ("SERVICIOS COMUNALES, SOCIALES Y PERSONALES", "SERVICIOS_COMUNALES_SOCIALES_PERSONALES"),
)


def _p6_activity_metadata(
    label: str,
    current_section: str,
) -> tuple[str, str, str, str]:
    normalized = normalize_text(label)
    if normalized == "TOTAL":
        return "total", "TOTAL", label, ""

    activity_code_ranges = re.findall(r"\b([0-9]{3})\s*-\s*([0-9]{3})\s*\.", normalized)
    if activity_code_ranges:
        codes = [code for pair in activity_code_ranges for code in pair]
        return "activity_3digit", ";".join(codes), label, current_section

    activity_codes = re.findall(r"\b([0-9]{3})\s*\.", normalized)
    if activity_codes:
        return "activity_3digit", ";".join(activity_codes), label, current_section

    if normalized.startswith("ACTIVIDADES NO BIEN ESPECIFICADAS"):
        return "other_activity", "ACTIVIDADES_NO_BIEN_ESPECIFICADAS", label, current_section

    for prefix, code in P6_BROAD_ACTIVITY_PREFIXES:
        if normalized.startswith(prefix):
            return "broad_activity", code, label, label

    return _activity_metadata(label, current_section)


def _activity_metadata(
    label: str,
    current_section: str,
) -> tuple[str, str, str, str]:
    normalized = normalize_text(label)
    if normalized == "TOTAL":
        return "total", "TOTAL", label, ""

    section_match = re.match(r"^([A-Z])\s*-\s*", normalized)
    if section_match:
        return "section", section_match.group(1), label, label

    activity_code_ranges = re.findall(r"\b([0-9]{3})\s*-\s*([0-9]{3})\s*\.", normalized)
    if activity_code_ranges:
        codes = [code for pair in activity_code_ranges for code in pair]
        return "activity_3digit", ";".join(codes), label, current_section

    activity_codes = re.findall(r"\b([0-9]{3})\s*\.", normalized)
    if activity_codes:
        return "activity_3digit", ";".join(activity_codes), label, current_section

    if normalized == "OTRAS ACTIVIDADES":
        return "other_activity", "OTRAS_ACTIVIDADES", label, ""

    if normalized.startswith("ACTIVIDADES NO BIEN ESPECIFICADAS"):
        suffix_match = re.search(r"\b([0-9]+)\s*/?$", normalized)
        suffix = f"_{suffix_match.group(1)}" if suffix_match else ""
        return (
            "other_activity",
            f"ACTIVIDADES_NO_BIEN_ESPECIFICADAS{suffix}",
            label,
            current_section,
        )

    slug = "_".join(normalized.lower().split())
    return "other", slug, label, current_section


def _html_cell_text(cell: Any) -> str:
    text = cell.get_text(" ", strip=True).replace("\xa0", " ")
    return " ".join(text.split())


def html_rows_from_bytes(file_contents: bytes) -> list[list[str]]:
    """Read an Excel-exported HTML sheet into a rectangular row-value matrix.

    The AFIP 2009-2014 archives store Excel workbooks as HTML framesets. The
    statistical table is in `*_archivos/sheet001.htm`. Excel uses `rowspan` and
    `colspan` in those HTML tables, so this parser expands spans into blank
    cells to emulate the row matrix returned by `xlrd` for XLS files.
    """

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(file_contents, "lxml", from_encoding="windows-1252")
    best_rows: list[list[str]] = []
    for table in soup.find_all("table"):
        rows: list[list[str]] = []
        active_rowspans: dict[int, int] = {}
        for table_row in table.find_all("tr"):
            row: list[str] = []
            column_index = 0
            for cell in table_row.find_all(["td", "th"]):
                while active_rowspans.get(column_index, 0) > 0:
                    row.append("")
                    active_rowspans[column_index] -= 1
                    column_index += 1

                rowspan = int(cell.get("rowspan", "1") or 1)
                colspan = int(cell.get("colspan", "1") or 1)
                row.append(_html_cell_text(cell))
                if rowspan > 1:
                    active_rowspans[column_index] = max(
                        active_rowspans.get(column_index, 0),
                        rowspan - 1,
                    )

                for offset in range(1, colspan):
                    row.append("")
                    if rowspan > 1:
                        active_rowspans[column_index + offset] = max(
                            active_rowspans.get(column_index + offset, 0),
                            rowspan - 1,
                        )
                column_index += colspan

            max_active_column = max(
                (column for column, count in active_rowspans.items() if count > 0),
                default=-1,
            )
            while column_index <= max_active_column:
                row.append("")
                if active_rowspans.get(column_index, 0) > 0:
                    active_rowspans[column_index] -= 1
                column_index += 1

            while row and row[-1] == "":
                row.pop()
            if row:
                rows.append(row)
        if len(rows) > len(best_rows):
            best_rows = rows
    return best_rows


def _p1_sheet_member(zip_file: ZipFile, table_id: str) -> tuple[str, bool]:
    detail_member = f"archivos/{table_id}_2_archivos/sheet001.htm"
    if detail_member in zip_file.namelist():
        return detail_member, True
    return f"archivos/{table_id}_archivos/sheet001.htm", False


def _p2_sheet_member(zip_file: ZipFile, table_id: str) -> tuple[str, bool]:
    detail_member = f"Archivos/{table_id}_archivos/sheet002.htm"
    if detail_member in zip_file.namelist():
        return detail_member, True
    return f"Archivos/{table_id}_archivos/sheet001.htm", False


def _p3_sheet_member(zip_file: ZipFile, table_id: str) -> tuple[str, bool] | None:
    detail_members = sorted(
        name
        for name in zip_file.namelist()
        if name.endswith(f"/{table_id}_archivos/sheet002.htm")
    )
    if detail_members:
        return detail_members[0], True

    base_members = sorted(
        name
        for name in zip_file.namelist()
        if name.endswith(f"/{table_id}_archivos/sheet001.htm")
    )
    if base_members:
        return base_members[0], False
    return None


def _extract_cab_xls_members_from_zip(
    archive_path: Path,
    destination_dir: Path,
    member_pattern: str = "2.3.1.1*.xls",
) -> list[Path]:
    """Extract AFIP CAB-nested XLS members matching a pattern into a temp folder.

    Older AFIP publications wrap the statistical XLS files inside `AFIP.CAB`.
    The Python standard library has no CAB reader, so this uses the local
    `cabextract` executable and keeps all extracted files in a temporary
    directory controlled by the calling function.
    """

    cabextract = shutil.which("cabextract")
    if cabextract is None:
        raise RuntimeError("cabextract is required to read AFIP.CAB archives.")

    with ZipFile(archive_path) as zip_file:
        cab_members = [name for name in zip_file.namelist() if name.upper() == "AFIP.CAB"]
        if not cab_members:
            raise ValueError(f"AFIP.CAB not found in {archive_path.name}")
        cab_path = destination_dir / "AFIP.CAB"
        cab_path.write_bytes(zip_file.read(cab_members[0]))

    xls_dir = destination_dir / "xls"
    xls_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            cabextract,
            "-F",
            member_pattern,
            "-d",
            str(xls_dir),
            str(cab_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(xls_dir.glob("*.xls"))


def _p4_cab_member_path(member_name: str) -> str:
    return f"AFIP.CAB/{member_name}"


def _p4_cab_member_name(source_table_path: str) -> str:
    return source_table_path.split("/", maxsplit=1)[-1]


def _p4_preferred_member(
    xls_paths: Sequence[Path],
    table_id: str,
) -> tuple[Path, bool] | None:
    by_name = {path.name: path for path in xls_paths}
    detail_name = f"{table_id}_2.xls"
    if detail_name in by_name:
        return by_name[detail_name], True
    base_name = f"{table_id}.xls"
    if base_name in by_name:
        return by_name[base_name], False
    return None


def _p5_source_year_suffix(fiscal_year: int) -> str:
    suffix_by_fiscal_year = {
        1999: "2000",
        2000: "2001",
        2001: "2002",
    }
    return suffix_by_fiscal_year[fiscal_year]


def _p5_preferred_member(
    xls_paths: Sequence[Path],
    table_id: str,
    fiscal_year: int,
) -> tuple[Path, bool] | None:
    by_name = {path.name: path for path in xls_paths}
    suffix = _p5_source_year_suffix(fiscal_year)
    detail_name = f"{table_id}_{suffix}_2.xls"
    if detail_name in by_name:
        return by_name[detail_name], True
    base_name = f"{table_id}_{suffix}.xls"
    if base_name in by_name:
        return by_name[base_name], False
    return None


def _p6_archive_name(publication_year: int) -> str:
    return P6_DIRECT_XLS_ARCHIVES[publication_year]


def _p6_preferred_member(
    member_names: Sequence[str],
    table_id: str,
    fiscal_year: int,
) -> tuple[str, bool] | None:
    by_stem = {Path(member).stem: member for member in member_names}
    detail_stem = f"{table_id}_2"
    if fiscal_year == 1998 and detail_stem in by_stem:
        return by_stem[detail_stem], True
    if table_id in by_stem:
        return by_stem[table_id], False
    return None


def _data_end_before_percentage_section(
    rows: Sequence[Sequence[Any]],
    data_start_row: int,
) -> int:
    for row_index in range(data_start_row, len(rows)):
        if "ESTRUCTURA PORCENTUAL" in row_text(rows[row_index]):
            return row_index
    return len(rows)


def _align_activity_column_to_data(
    rows: Sequence[Sequence[Any]],
    data_start_row: int,
    data_end_row: int,
    detected_activity_column: int,
) -> int:
    """Return the nearby column with the strongest activity-label evidence."""

    candidate_scores: dict[int, int] = {}
    for candidate in range(
        max(0, detected_activity_column - 2),
        detected_activity_column + 3,
    ):
        score = 0
        for row in rows[data_start_row:min(data_end_row, data_start_row + 40)]:
            if candidate >= len(row):
                continue
            label = cell_display_text(row[candidate])
            if not label or decimal_from_cell(label) is not None:
                continue
            normalized = normalize_text(label)
            if normalized == "TOTAL":
                score += 3
            elif re.match(r"^[A-Z]\s*-\s*", normalized):
                score += 3
            elif re.match(r"^[0-9]{3}\.", normalized):
                score += 2
            else:
                score += 1
        candidate_scores[candidate] = score

    return max(
        candidate_scores,
        key=lambda column: (candidate_scores[column], column == detected_activity_column),
    )


def _p0_activity_inventory_rows(
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in inventory_rows
        if str(row["period_id"]) == "P0_new_xls_detail"
        and str(row["source_table_id"]) == table_id
    ]
    return sorted(rows, key=lambda row: int(row["publication_year"]))


def _p1_activity_inventory_rows(
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in inventory_rows
        if str(row["period_id"]) == "P1_new_html_detail"
        and str(row["source_table_id"]) == table_id
    ]
    return sorted(rows, key=lambda row: int(row["publication_year"]))


def _p2_activity_inventory_rows(
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in inventory_rows
        if str(row["period_id"]) == "P2_old_html_detail_millions"
        and str(row["source_table_id"]) == table_id
    ]
    return sorted(rows, key=lambda row: int(row["publication_year"]))


def _p3_activity_inventory_rows(
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in inventory_rows
        if str(row["period_id"]) == "P3_old_html_detail_thousands"
        and str(row["source_table_id"]) == table_id
    ]
    return sorted(rows, key=lambda row: int(row["publication_year"]))


def _p4_activity_inventory_rows(
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in inventory_rows
        if str(row["period_id"]) == "P4_old_cab_xls_detail_thousands"
        and str(row["source_table_id"]) == table_id
    ]
    return sorted(rows, key=lambda row: int(row["publication_year"]))


def _p5_activity_inventory_rows(
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in inventory_rows
        if str(row["period_id"]) == "P5_old_cab_xls_detail_legacy_numbering"
        and str(row["source_table_id"]) == table_id
    ]
    return sorted(rows, key=lambda row: int(row["fiscal_year"]))


def _p6_activity_inventory_rows(
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in inventory_rows
        if str(row["period_id"]) == "P6_legacy_broad_activity"
        and str(row["source_table_id"]) == table_id
    ]
    return sorted(rows, key=lambda row: int(row["fiscal_year"]))


def _extract_p0_activity_table(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
    column_detector: Any,
) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for inventory_row in _p0_activity_inventory_rows(inventory_rows, table_id):
        archive_path = raw_archive_dir / str(inventory_row["archive_filename"])
        with ZipFile(archive_path) as zip_file:
            rows = xls_rows_from_bytes(zip_file.read(str(inventory_row["source_table_path"])))

        bounds = detect_xls_table_bounds(rows)
        header_rows = rows[bounds.header_start_row:bounds.data_start_row]
        activity_column, variable_columns = column_detector(header_rows)
        current_section = ""

        for source_row_index in range(bounds.data_start_row, len(rows)):
            source_row = rows[source_row_index]
            if activity_column >= len(source_row):
                continue

            activity_label = cell_display_text(source_row[activity_column])
            if not activity_label:
                continue
            numeric_values = [
                decimal_from_cell(source_row[variable.column_index])
                for variable in variable_columns
                if variable.column_index < len(source_row)
            ]
            if not any(value is not None for value in numeric_values):
                continue

            (
                activity_level,
                activity_code,
                activity_label_original,
                activity_section_original,
            ) = _activity_metadata(activity_label, current_section)
            if activity_level == "section":
                current_section = activity_label_original

            for variable in variable_columns:
                cell_value = None
                if variable.column_index < len(source_row):
                    cell_value = decimal_from_cell(source_row[variable.column_index])
                if cell_value is None:
                    continue

                value_pesos_current = (
                    cell_value * Decimal("1000000")
                    if variable.is_monetary
                    else None
                )
                output_rows.append(
                    {
                        "publication_year": str(inventory_row["publication_year"]),
                        "fiscal_year": str(inventory_row["fiscal_year"]),
                        "archive_filename": str(inventory_row["archive_filename"]),
                        "period_id": str(inventory_row["period_id"]),
                        "source_table_id": str(inventory_row["source_table_id"]),
                        "source_table_path": str(inventory_row["source_table_path"]),
                        "source_table_title": str(inventory_row["source_table_title"]),
                        "table_family": str(inventory_row["table_family"]),
                        "universe": str(inventory_row["universe"]),
                        "dimension_type": str(inventory_row["dimension_type"]),
                        "dimension_value": activity_code,
                        "activity_level": activity_level,
                        "activity_code": activity_code,
                        "activity_label_original": activity_label_original,
                        "activity_section_original": activity_section_original,
                        "classifier_period": "new",
                        "variable_name": variable.variable_name,
                        "value": decimal_to_text(cell_value),
                        "unit_original": variable.unit_original,
                        "value_pesos_current": decimal_to_text(value_pesos_current),
                        "source_note": "",
                        "header_start_row_zero_based": str(bounds.header_start_row),
                        "data_start_row_zero_based": str(bounds.data_start_row),
                        "source_row_zero_based": str(source_row_index),
                        "source_column_zero_based": str(variable.column_index),
                    }
                )

    return output_rows


def _extract_p1_activity_table(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
    column_detector: Any,
) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for inventory_row in _p1_activity_inventory_rows(inventory_rows, table_id):
        archive_path = raw_archive_dir / str(inventory_row["archive_filename"])
        with ZipFile(archive_path) as zip_file:
            rows = html_rows_from_bytes(zip_file.read(str(inventory_row["source_table_path"])))

        bounds = detect_xls_table_bounds(rows)
        header_rows = rows[bounds.header_start_row:bounds.data_start_row]
        data_end_row = _data_end_before_percentage_section(rows, bounds.data_start_row)
        activity_column, variable_columns = column_detector(header_rows)
        current_section = ""

        for source_row_index in range(bounds.data_start_row, data_end_row):
            source_row = rows[source_row_index]
            if activity_column >= len(source_row):
                continue

            activity_label = cell_display_text(source_row[activity_column])
            if not activity_label:
                continue
            numeric_values = [
                decimal_from_cell(source_row[variable.column_index])
                for variable in variable_columns
                if variable.column_index < len(source_row)
            ]
            if not any(value is not None for value in numeric_values):
                continue

            (
                activity_level,
                activity_code,
                activity_label_original,
                activity_section_original,
            ) = _activity_metadata(activity_label, current_section)
            if activity_level == "section":
                current_section = activity_label_original

            for variable in variable_columns:
                cell_value = None
                if variable.column_index < len(source_row):
                    cell_value = decimal_from_cell(source_row[variable.column_index])
                if cell_value is None:
                    continue

                value_pesos_current = (
                    cell_value * Decimal("1000000")
                    if variable.is_monetary
                    else None
                )
                output_rows.append(
                    {
                        "publication_year": str(inventory_row["publication_year"]),
                        "fiscal_year": str(inventory_row["fiscal_year"]),
                        "archive_filename": str(inventory_row["archive_filename"]),
                        "period_id": str(inventory_row["period_id"]),
                        "source_table_id": str(inventory_row["source_table_id"]),
                        "source_table_path": str(inventory_row["source_table_path"]),
                        "source_table_title": str(inventory_row["source_table_title"]),
                        "table_family": str(inventory_row["table_family"]),
                        "universe": str(inventory_row["universe"]),
                        "dimension_type": str(inventory_row["dimension_type"]),
                        "dimension_value": activity_code,
                        "activity_level": activity_level,
                        "activity_code": activity_code,
                        "activity_label_original": activity_label_original,
                        "activity_section_original": activity_section_original,
                        "classifier_period": "new",
                        "variable_name": variable.variable_name,
                        "value": decimal_to_text(cell_value),
                        "unit_original": variable.unit_original,
                        "value_pesos_current": decimal_to_text(value_pesos_current),
                        "source_note": "html_excel_detail_sheet",
                        "header_start_row_zero_based": str(bounds.header_start_row),
                        "data_start_row_zero_based": str(bounds.data_start_row),
                        "source_row_zero_based": str(source_row_index),
                        "source_column_zero_based": str(variable.column_index),
                    }
                )

    return output_rows


def _extract_p2_activity_table(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
    column_detector: Any,
) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for inventory_row in _p2_activity_inventory_rows(inventory_rows, table_id):
        archive_path = raw_archive_dir / str(inventory_row["archive_filename"])
        with ZipFile(archive_path) as zip_file:
            rows = html_rows_from_bytes(zip_file.read(str(inventory_row["source_table_path"])))

        bounds = detect_xls_table_bounds(rows)
        header_rows = rows[bounds.header_start_row:bounds.data_start_row]
        data_end_row = _data_end_before_percentage_section(rows, bounds.data_start_row)
        activity_column, variable_columns = column_detector(header_rows)
        current_section = ""

        for source_row_index in range(bounds.data_start_row, data_end_row):
            source_row = rows[source_row_index]
            if activity_column >= len(source_row):
                continue

            activity_label = cell_display_text(source_row[activity_column])
            if not activity_label:
                continue
            numeric_values = [
                decimal_from_cell(source_row[variable.column_index])
                for variable in variable_columns
                if variable.column_index < len(source_row)
            ]
            if not any(value is not None for value in numeric_values):
                continue

            (
                activity_level,
                activity_code,
                activity_label_original,
                activity_section_original,
            ) = _activity_metadata(activity_label, current_section)
            if activity_level == "section":
                current_section = activity_label_original

            for variable in variable_columns:
                cell_value = None
                if variable.column_index < len(source_row):
                    cell_value = decimal_from_cell(source_row[variable.column_index])
                if cell_value is None:
                    continue

                value_pesos_current = (
                    cell_value * Decimal("1000000")
                    if variable.is_monetary
                    else None
                )
                output_rows.append(
                    {
                        "publication_year": str(inventory_row["publication_year"]),
                        "fiscal_year": str(inventory_row["fiscal_year"]),
                        "archive_filename": str(inventory_row["archive_filename"]),
                        "period_id": str(inventory_row["period_id"]),
                        "source_table_id": str(inventory_row["source_table_id"]),
                        "source_table_path": str(inventory_row["source_table_path"]),
                        "source_table_title": str(inventory_row["source_table_title"]),
                        "table_family": str(inventory_row["table_family"]),
                        "universe": str(inventory_row["universe"]),
                        "dimension_type": str(inventory_row["dimension_type"]),
                        "dimension_value": activity_code,
                        "activity_level": activity_level,
                        "activity_code": activity_code,
                        "activity_label_original": activity_label_original,
                        "activity_section_original": activity_section_original,
                        "classifier_period": "old",
                        "variable_name": variable.variable_name,
                        "value": decimal_to_text(cell_value),
                        "unit_original": variable.unit_original,
                        "value_pesos_current": decimal_to_text(value_pesos_current),
                        "source_note": "html_excel_sheet002_detail",
                        "header_start_row_zero_based": str(bounds.header_start_row),
                        "data_start_row_zero_based": str(bounds.data_start_row),
                        "source_row_zero_based": str(source_row_index),
                        "source_column_zero_based": str(variable.column_index),
                    }
                )

    return output_rows


def _extract_p3_activity_table(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for inventory_row in _p3_activity_inventory_rows(inventory_rows, table_id):
        archive_path = raw_archive_dir / str(inventory_row["archive_filename"])
        with ZipFile(archive_path) as zip_file:
            rows = html_rows_from_bytes(zip_file.read(str(inventory_row["source_table_path"])))

        bounds = detect_xls_table_bounds(rows)
        header_rows = rows[bounds.header_start_row:bounds.data_start_row]
        data_end_row = _data_end_before_percentage_section(rows, bounds.data_start_row)
        fiscal_year = int(inventory_row["fiscal_year"])
        column_detector = _p3_column_detector(table_id, fiscal_year)
        activity_column, variable_columns = column_detector(header_rows)
        activity_column = _align_activity_column_to_data(
            rows,
            bounds.data_start_row,
            data_end_row,
            activity_column,
        )
        current_section = ""

        for source_row_index in range(bounds.data_start_row, data_end_row):
            source_row = rows[source_row_index]
            if activity_column >= len(source_row):
                continue

            activity_label = cell_display_text(source_row[activity_column])
            if not activity_label:
                continue
            numeric_values = [
                decimal_from_cell(source_row[variable.column_index])
                for variable in variable_columns
                if variable.column_index < len(source_row)
            ]
            if not any(value is not None for value in numeric_values):
                continue

            (
                activity_level,
                activity_code,
                activity_label_original,
                activity_section_original,
            ) = _activity_metadata(activity_label, current_section)
            if activity_level == "section":
                current_section = activity_label_original

            for variable in variable_columns:
                cell_value = None
                if variable.column_index < len(source_row):
                    cell_value = decimal_from_cell(source_row[variable.column_index])
                if cell_value is None:
                    continue

                unit_original = (
                    str(inventory_row["unit_original"])
                    if variable.is_monetary
                    else variable.unit_original
                )
                multiplier = _monetary_multiplier(unit_original)
                value_pesos_current = (
                    cell_value * multiplier
                    if variable.is_monetary and multiplier is not None
                    else None
                )
                output_rows.append(
                    {
                        "publication_year": str(inventory_row["publication_year"]),
                        "fiscal_year": str(inventory_row["fiscal_year"]),
                        "archive_filename": str(inventory_row["archive_filename"]),
                        "period_id": str(inventory_row["period_id"]),
                        "source_table_id": str(inventory_row["source_table_id"]),
                        "source_table_path": str(inventory_row["source_table_path"]),
                        "source_table_title": str(inventory_row["source_table_title"]),
                        "table_family": str(inventory_row["table_family"]),
                        "universe": str(inventory_row["universe"]),
                        "dimension_type": str(inventory_row["dimension_type"]),
                        "dimension_value": activity_code,
                        "activity_level": activity_level,
                        "activity_code": activity_code,
                        "activity_label_original": activity_label_original,
                        "activity_section_original": activity_section_original,
                        "classifier_period": "old",
                        "variable_name": variable.variable_name,
                        "value": decimal_to_text(cell_value),
                        "unit_original": unit_original,
                        "value_pesos_current": decimal_to_text(value_pesos_current),
                        "source_note": str(inventory_row["notes"]),
                        "header_start_row_zero_based": str(bounds.header_start_row),
                        "data_start_row_zero_based": str(bounds.data_start_row),
                        "source_row_zero_based": str(source_row_index),
                        "source_column_zero_based": str(variable.column_index),
                    }
                )

    return output_rows


def _extract_p4_activity_table(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for inventory_row in _p4_activity_inventory_rows(inventory_rows, table_id):
        archive_path = raw_archive_dir / str(inventory_row["archive_filename"])
        member_name = _p4_cab_member_name(str(inventory_row["source_table_path"]))
        with tempfile.TemporaryDirectory(prefix="afip_p4_") as temp_name:
            xls_paths = _extract_cab_xls_members_from_zip(
                archive_path,
                Path(temp_name),
            )
            xls_by_name = {path.name: path for path in xls_paths}
            if member_name not in xls_by_name:
                raise FileNotFoundError(
                    f"{member_name} not found in {inventory_row['archive_filename']}"
                )
            rows = xls_rows_from_bytes(xls_by_name[member_name].read_bytes())

        bounds = detect_xls_table_bounds(rows)
        header_rows = rows[bounds.header_start_row:bounds.data_start_row]
        data_end_row = _data_end_before_percentage_section(rows, bounds.data_start_row)
        column_detector = _p4_column_detector(table_id)
        activity_column, variable_columns = column_detector(header_rows)
        activity_column = _align_activity_column_to_data(
            rows,
            bounds.data_start_row,
            data_end_row,
            activity_column,
        )
        current_section = ""

        for source_row_index in range(bounds.data_start_row, data_end_row):
            source_row = rows[source_row_index]
            if activity_column >= len(source_row):
                continue

            activity_label = cell_display_text(source_row[activity_column])
            if not activity_label:
                continue
            numeric_values = [
                decimal_from_cell(source_row[variable.column_index])
                for variable in variable_columns
                if variable.column_index < len(source_row)
            ]
            if not any(value is not None for value in numeric_values):
                continue

            (
                activity_level,
                activity_code,
                activity_label_original,
                activity_section_original,
            ) = _activity_metadata(activity_label, current_section)
            if activity_level == "section":
                current_section = activity_label_original

            for variable in variable_columns:
                cell_value = None
                if variable.column_index < len(source_row):
                    cell_value = decimal_from_cell(source_row[variable.column_index])
                if cell_value is None:
                    continue

                unit_original = (
                    str(inventory_row["unit_original"])
                    if variable.is_monetary
                    else variable.unit_original
                )
                multiplier = _monetary_multiplier(unit_original)
                value_pesos_current = (
                    cell_value * multiplier
                    if variable.is_monetary and multiplier is not None
                    else None
                )
                output_rows.append(
                    {
                        "publication_year": str(inventory_row["publication_year"]),
                        "fiscal_year": str(inventory_row["fiscal_year"]),
                        "archive_filename": str(inventory_row["archive_filename"]),
                        "period_id": str(inventory_row["period_id"]),
                        "source_table_id": str(inventory_row["source_table_id"]),
                        "source_table_path": str(inventory_row["source_table_path"]),
                        "source_table_title": str(inventory_row["source_table_title"]),
                        "table_family": str(inventory_row["table_family"]),
                        "universe": str(inventory_row["universe"]),
                        "dimension_type": str(inventory_row["dimension_type"]),
                        "dimension_value": activity_code,
                        "activity_level": activity_level,
                        "activity_code": activity_code,
                        "activity_label_original": activity_label_original,
                        "activity_section_original": activity_section_original,
                        "classifier_period": "old",
                        "variable_name": variable.variable_name,
                        "value": decimal_to_text(cell_value),
                        "unit_original": unit_original,
                        "value_pesos_current": decimal_to_text(value_pesos_current),
                        "source_note": str(inventory_row["notes"]),
                        "header_start_row_zero_based": str(bounds.header_start_row),
                        "data_start_row_zero_based": str(bounds.data_start_row),
                        "source_row_zero_based": str(source_row_index),
                        "source_column_zero_based": str(variable.column_index),
                    }
                )

    return output_rows


def _extract_p5_activity_table(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for inventory_row in _p5_activity_inventory_rows(inventory_rows, table_id):
        archive_path = raw_archive_dir / str(inventory_row["archive_filename"])
        member_name = _p4_cab_member_name(str(inventory_row["source_table_path"]))
        with tempfile.TemporaryDirectory(prefix="afip_p5_") as temp_name:
            xls_paths = _extract_cab_xls_members_from_zip(
                archive_path,
                Path(temp_name),
                "3.3.1.1*.xls",
            )
            xls_by_name = {path.name: path for path in xls_paths}
            if member_name not in xls_by_name:
                raise FileNotFoundError(
                    f"{member_name} not found in {inventory_row['archive_filename']}"
                )
            rows = xls_rows_from_bytes(xls_by_name[member_name].read_bytes())

        bounds = detect_xls_table_bounds(rows)
        header_rows = rows[bounds.header_start_row:bounds.data_start_row]
        data_end_row = _data_end_before_percentage_section(rows, bounds.data_start_row)
        fiscal_year = int(inventory_row["fiscal_year"])
        column_detector = _p5_column_detector(table_id, fiscal_year)
        activity_column, variable_columns = column_detector(header_rows)
        activity_column = _align_activity_column_to_data(
            rows,
            bounds.data_start_row,
            data_end_row,
            activity_column,
        )
        current_section = ""

        for source_row_index in range(bounds.data_start_row, data_end_row):
            source_row = rows[source_row_index]
            if activity_column >= len(source_row):
                continue

            activity_label = cell_display_text(source_row[activity_column])
            if not activity_label:
                continue
            numeric_values = [
                decimal_from_cell(source_row[variable.column_index])
                for variable in variable_columns
                if variable.column_index < len(source_row)
            ]
            if not any(value is not None for value in numeric_values):
                continue

            (
                activity_level,
                activity_code,
                activity_label_original,
                activity_section_original,
            ) = _activity_metadata(activity_label, current_section)
            if activity_level == "section":
                current_section = activity_label_original

            for variable in variable_columns:
                cell_value = None
                if variable.column_index < len(source_row):
                    cell_value = decimal_from_cell(source_row[variable.column_index])
                if cell_value is None:
                    continue

                unit_original = (
                    str(inventory_row["unit_original"])
                    if variable.is_monetary
                    else variable.unit_original
                )
                multiplier = _monetary_multiplier(unit_original)
                value_pesos_current = (
                    cell_value * multiplier
                    if variable.is_monetary and multiplier is not None
                    else None
                )
                output_rows.append(
                    {
                        "publication_year": str(inventory_row["publication_year"]),
                        "fiscal_year": str(inventory_row["fiscal_year"]),
                        "archive_filename": str(inventory_row["archive_filename"]),
                        "period_id": str(inventory_row["period_id"]),
                        "source_table_id": str(inventory_row["source_table_id"]),
                        "source_table_path": str(inventory_row["source_table_path"]),
                        "source_table_title": str(inventory_row["source_table_title"]),
                        "table_family": str(inventory_row["table_family"]),
                        "universe": str(inventory_row["universe"]),
                        "dimension_type": str(inventory_row["dimension_type"]),
                        "dimension_value": activity_code,
                        "activity_level": activity_level,
                        "activity_code": activity_code,
                        "activity_label_original": activity_label_original,
                        "activity_section_original": activity_section_original,
                        "classifier_period": "old",
                        "variable_name": variable.variable_name,
                        "value": decimal_to_text(cell_value),
                        "unit_original": unit_original,
                        "value_pesos_current": decimal_to_text(value_pesos_current),
                        "source_note": str(inventory_row["notes"]),
                        "header_start_row_zero_based": str(bounds.header_start_row),
                        "data_start_row_zero_based": str(bounds.data_start_row),
                        "source_row_zero_based": str(source_row_index),
                        "source_column_zero_based": str(variable.column_index),
                    }
                )

    return output_rows


def _extract_p6_activity_table(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
    table_id: str,
) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for inventory_row in _p6_activity_inventory_rows(inventory_rows, table_id):
        archive_path = raw_archive_dir / str(inventory_row["archive_filename"])
        with ZipFile(archive_path) as zip_file:
            rows = xls_rows_from_bytes(zip_file.read(str(inventory_row["source_table_path"])))

        bounds = detect_xls_table_bounds(rows)
        header_rows = rows[max(0, bounds.header_start_row - 1):bounds.data_start_row]
        data_end_row = _data_end_before_percentage_section(rows, bounds.data_start_row)
        fiscal_year = int(inventory_row["fiscal_year"])
        column_detector = _p6_column_detector(table_id, fiscal_year)
        activity_column, variable_columns = column_detector(header_rows)
        activity_column = _align_activity_column_to_data(
            rows,
            bounds.data_start_row,
            data_end_row,
            activity_column,
        )
        current_section = ""

        for source_row_index in range(bounds.data_start_row, data_end_row):
            source_row = rows[source_row_index]
            if activity_column >= len(source_row):
                continue

            activity_label = cell_display_text(source_row[activity_column])
            if not activity_label:
                continue
            numeric_values = [
                decimal_from_cell(source_row[variable.column_index])
                for variable in variable_columns
                if variable.column_index < len(source_row)
            ]
            if not any(value is not None for value in numeric_values):
                continue

            (
                activity_level,
                activity_code,
                activity_label_original,
                activity_section_original,
            ) = _p6_activity_metadata(activity_label, current_section)
            if activity_level in {"section", "broad_activity"}:
                current_section = activity_label_original

            for variable in variable_columns:
                cell_value = None
                if variable.column_index < len(source_row):
                    cell_value = decimal_from_cell(source_row[variable.column_index])
                if cell_value is None:
                    continue

                unit_original = (
                    str(inventory_row["unit_original"])
                    if variable.is_monetary
                    else variable.unit_original
                )
                multiplier = _monetary_multiplier(unit_original)
                value_pesos_current = (
                    cell_value * multiplier
                    if variable.is_monetary and multiplier is not None
                    else None
                )
                output_rows.append(
                    {
                        "publication_year": str(inventory_row["publication_year"]),
                        "fiscal_year": str(inventory_row["fiscal_year"]),
                        "archive_filename": str(inventory_row["archive_filename"]),
                        "period_id": str(inventory_row["period_id"]),
                        "source_table_id": str(inventory_row["source_table_id"]),
                        "source_table_path": str(inventory_row["source_table_path"]),
                        "source_table_title": str(inventory_row["source_table_title"]),
                        "table_family": str(inventory_row["table_family"]),
                        "universe": str(inventory_row["universe"]),
                        "dimension_type": str(inventory_row["dimension_type"]),
                        "dimension_value": activity_code,
                        "activity_level": activity_level,
                        "activity_code": activity_code,
                        "activity_label_original": activity_label_original,
                        "activity_section_original": activity_section_original,
                        "classifier_period": "old",
                        "variable_name": variable.variable_name,
                        "value": decimal_to_text(cell_value),
                        "unit_original": unit_original,
                        "value_pesos_current": decimal_to_text(value_pesos_current),
                        "source_note": str(inventory_row["notes"]),
                        "header_start_row_zero_based": str(bounds.header_start_row),
                        "data_start_row_zero_based": str(bounds.data_start_row),
                        "source_row_zero_based": str(source_row_index),
                        "source_column_zero_based": str(variable.column_index),
                    }
                )

    return output_rows


def extract_p0_23111_activity_summary(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.1 into canonical long rows.

    Scope is deliberately narrow: publication years 2015-2023, fiscal years
    2014-2022, direct XLS files, table 2.3.1.1.1. The function detects table
    bounds and variable columns from each workbook, preserving the original
    activity labels and creating one output row per observed cell.
    """

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_SUMMARY_TABLE_ID,
        detect_p0_23111_columns,
    )


def extract_p0_231121_activity_costs(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.2.1 into canonical long rows.

    This second pilot covers the sales/costs state-of-results table. It tests
    paired `Casos` and `Importe` columns under merged Excel headers before the
    approach is generalized to more table families.
    """

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_COSTS_TABLE_ID,
        detect_p0_231121_columns,
    )


def extract_p0_231122_activity_sales_detail(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.2.2 into canonical long rows.

    This third pilot covers detailed sales, exports and export-duty concepts
    before extending the approach to the remaining state-of-results tables.
    """

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_SALES_DETAIL_TABLE_ID,
        detect_p0_231122_columns,
    )


def extract_p0_231123_activity_cost_linked_expenses(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.2.3 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_COST_LINKED_EXPENSES_TABLE_ID,
        detect_p0_231123_columns,
    )


def extract_p0_231124_activity_gross_result(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.2.4 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_GROSS_RESULT_TABLE_ID,
        detect_p0_231124_columns,
    )


def extract_p0_231125_activity_operating_expenses(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.2.5 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_OPERATING_EXPENSES_TABLE_ID,
        detect_p0_231125_columns,
    )


def extract_p0_231126_activity_other_results(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.2.6 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_OTHER_RESULTS_TABLE_ID,
        detect_p0_231126_columns,
    )


def extract_p0_231127_activity_accounting_result(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.2.7 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_ACCOUNTING_RESULT_TABLE_ID,
        detect_p0_231127_columns,
    )


def extract_p0_23113_activity_tax_result(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.3 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_TAX_RESULT_TABLE_ID,
        detect_p0_23113_columns,
    )


def extract_p0_23114_activity_tax_determination(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.4 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_TAX_DETERMINATION_TABLE_ID,
        detect_p0_23114_columns,
    )


def extract_p0_231151_activity_assets(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.5.1 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_ASSETS_TABLE_ID,
        detect_p0_231151_columns,
    )


def extract_p0_2311511_activity_cash_assets(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.5.1.1 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_CASH_ASSETS_TABLE_ID,
        detect_p0_2311511_columns,
    )


def extract_p0_2311512_activity_credit_assets(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.5.1.2 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_CREDIT_ASSETS_TABLE_ID,
        detect_p0_2311512_columns,
    )


def extract_p0_2311513_activity_inventory_assets(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.5.1.3 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_INVENTORY_ASSETS_TABLE_ID,
        detect_p0_2311513_columns,
    )


def extract_p0_2311514_activity_fixed_assets(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.5.1.4 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_FIXED_ASSETS_TABLE_ID,
        detect_p0_2311514_columns,
    )


def extract_p0_231152_activity_liabilities(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.5.2 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_LIABILITIES_TABLE_ID,
        detect_p0_231152_columns,
    )


def extract_p0_2311521_activity_debt_liabilities(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.5.2.1 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_DEBT_LIABILITIES_TABLE_ID,
        detect_p0_2311521_columns,
    )


def extract_p0_231153_activity_equity(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.5.3 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_EQUITY_TABLE_ID,
        detect_p0_231153_columns,
    )


def extract_p0_2311531_activity_equity_increases(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.5.3.1 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_EQUITY_INCREASES_TABLE_ID,
        detect_p0_2311531_columns,
    )


def extract_p0_2311532_activity_equity_decreases(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P0 table 2.3.1.1.5.3.2 into canonical long rows."""

    return _extract_p0_activity_table(
        raw_archive_dir,
        inventory_rows,
        P0_ACTIVITY_EQUITY_DECREASES_TABLE_ID,
        detect_p0_2311532_columns,
    )


def extract_p1_new_html_detail(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P1 HTML activity tables into canonical long rows.

    Scope is publication year 2014 / fiscal year 2013. When the Excel HTML
    export includes a `_2` sheet for a table, this function uses that detail
    sheet to preserve activity rows at the maximum available disaggregation.
    """

    output_rows: list[dict[str, str]] = []
    for table_id in P1_ACTIVITY_TABLE_IDS:
        detector = P0_ACTIVITY_COLUMN_DETECTORS[table_id]
        output_rows.extend(
            _extract_p1_activity_table(
                raw_archive_dir,
                inventory_rows,
                table_id,
                detector,
            )
        )
    return output_rows


def extract_p2_old_html_detail_millions(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P2 HTML activity tables into canonical long rows.

    Scope is publication year 2013 / fiscal year 2012. This is the first
    backward period using the old activity classifier, still reported in
    millions of current pesos. The Excel HTML detail sheet is `sheet002.htm`.
    """

    output_rows: list[dict[str, str]] = []
    for table_id in P2_ACTIVITY_TABLE_IDS:
        detector = P0_ACTIVITY_COLUMN_DETECTORS[table_id]
        output_rows.extend(
            _extract_p2_activity_table(
                raw_archive_dir,
                inventory_rows,
                table_id,
                detector,
            )
        )
    return output_rows


def extract_p3_old_html_detail_thousands(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P3 HTML activity tables into canonical long rows.

    Scope is publication years 2009-2012 / fiscal years 2008-2011. This period
    keeps the old activity classifier and reports monetary values in thousands
    of current pesos.
    """

    output_rows: list[dict[str, str]] = []
    for table_id in P3_ACTIVITY_TABLE_IDS:
        output_rows.extend(
            _extract_p3_activity_table(
                raw_archive_dir,
                inventory_rows,
                table_id,
            )
        )
    return output_rows


def extract_p4_old_cab_xls_detail_thousands(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P4 CAB-nested XLS activity tables into canonical long rows.

    Scope is publication years 2003-2008 / fiscal years 2002-2007. This period
    uses the old activity classifier, reports monetary values in thousands of
    current pesos, and stores the XLS files inside `AFIP.CAB`.
    """

    output_rows: list[dict[str, str]] = []
    for table_id in P4_ACTIVITY_TABLE_IDS:
        output_rows.extend(
            _extract_p4_activity_table(
                raw_archive_dir,
                inventory_rows,
                table_id,
            )
        )
    return output_rows


def extract_p5_old_cab_xls_detail_legacy_numbering(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P5 legacy-numbered CAB/XLS activity tables into long rows.

    Scope is fiscal years 1999-2001 from the publication-year 2002 CAB, using
    the latest-source rule for duplicated historical fiscal years.
    """

    output_rows: list[dict[str, str]] = []
    table_ids = tuple(
        dict.fromkeys(
            table_id
            for fiscal_year in (1999, 2000, 2001)
            for table_id in _p5_activity_table_ids(fiscal_year)
        )
    )
    for table_id in table_ids:
        output_rows.extend(
            _extract_p5_activity_table(
                raw_archive_dir,
                inventory_rows,
                table_id,
            )
        )
    return output_rows


def extract_p6_legacy_broad_activity(
    raw_archive_dir: Path,
    inventory_rows: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract P6 direct-XLS legacy activity tables into canonical long rows.

    Scope is publication years 1998-1999 / fiscal years 1997-1998. Fiscal
    year 1997 is available only at broad activity level in the total-universe
    tables, while fiscal year 1998 has `_2` continuation workbooks with 3-digit
    activity detail.
    """

    output_rows: list[dict[str, str]] = []
    table_ids = tuple(
        dict.fromkeys(
            table_id
            for fiscal_year in (1997, 1998)
            for table_id in _p6_activity_table_ids(fiscal_year)
        )
    )
    for table_id in table_ids:
        output_rows.extend(
            _extract_p6_activity_table(
                raw_archive_dir,
                inventory_rows,
                table_id,
            )
        )
    return output_rows


def inventory_p0_modern_xls(raw_archive_dir: Path) -> list[dict[str, Any]]:
    """Inventory Ganancias Sociedades XLS tables for the newest homogeneous period.

    Scope is intentionally limited to `P0_new_xls_detail`: publication years
    2015-2023, fiscal years 2014-2022, direct XLS files, and source-table ids
    beginning with `2.3.`.

    The function reads metadata and detects table bounds, but it does not
    extract statistical values. It is the inventory step needed before the
    long-format extraction function can be implemented.
    """

    inventory: list[dict[str, Any]] = []
    for publication_year, archive_name in P0_MODERN_XLS_ARCHIVES.items():
        archive_path = raw_archive_dir / archive_name
        with ZipFile(archive_path) as zip_file:
            members = sorted(
                name
                for name in zip_file.namelist()
                if name.lower().endswith(".xls") and "/2.3." in name
            )
            for member_name in members:
                rows = xls_rows_from_bytes(zip_file.read(member_name))
                title_lines = _title_lines(rows)
                title_text = " // ".join(title_lines)
                fiscal_year = _find_fiscal_year(title_text)
                unit_original = _unit_from_text(title_text)
                table_family = _table_family_from_text(title_text)
                dimension_type = _dimension_type_from_text(title_text + " " + " ".join(row_text(row) for row in rows[:12]))
                universe = _universe_from_text(title_text)
                has_section, has_detail = _activity_detail_flags(rows)
                source_id = _source_table_id(member_name)
                notes = ""
                try:
                    bounds = detect_xls_table_bounds(rows)
                    header_start_row_zero_based = bounds.header_start_row
                    data_start_row_zero_based = bounds.data_start_row
                    first_data_label = bounds.first_data_label
                except ValueError as error:
                    header_start_row_zero_based = ""
                    data_start_row_zero_based = ""
                    first_data_label = ""
                    notes = f"bounds_detection_failed: {error}"

                inventory.append(
                    {
                        "publication_year": publication_year,
                        "fiscal_year": fiscal_year if fiscal_year is not None else "",
                        "archive_filename": archive_name,
                        "period_id": "P0_new_xls_detail",
                        "source_table_id": source_id,
                        "source_table_title": title_text,
                        "source_table_path": member_name,
                        "chapter_code_original": _chapter_code(source_id),
                        "table_family": table_family,
                        "dimension_type": dimension_type,
                        "universe": universe,
                        "format": "xls",
                        "unit_original": unit_original,
                        "has_activity_section": has_section,
                        "has_activity_3digit": has_detail,
                        "is_continuation": "_" in source_id,
                        "header_start_row_zero_based": header_start_row_zero_based,
                        "data_start_row_zero_based": data_start_row_zero_based,
                        "first_data_label": first_data_label,
                        "n_rows": len(rows),
                        "n_cols": max((len(row) for row in rows), default=0),
                        "notes": notes,
                    }
                )
    return inventory


def inventory_p1_new_html(raw_archive_dir: Path) -> list[dict[str, Any]]:
    """Inventory Ganancias Sociedades P1 Excel-exported HTML activity tables.

    P1 covers publication year 2014 / fiscal year 2013. The archive stores a
    frameset plus one support directory per table; the actual worksheet is
    `sheet001.htm`. For maximum activity detail, `_2` sheets are preferred when
    present.
    """

    inventory: list[dict[str, Any]] = []
    for publication_year, archive_name in P1_HTML_ARCHIVES.items():
        archive_path = raw_archive_dir / archive_name
        with ZipFile(archive_path) as zip_file:
            for table_id in P1_ACTIVITY_TABLE_IDS:
                member_name, is_detail_sheet = _p1_sheet_member(zip_file, table_id)
                rows = html_rows_from_bytes(zip_file.read(member_name))
                title_lines = _title_lines(rows)
                title_text = " // ".join(title_lines)
                fiscal_year = _find_fiscal_year(title_text)
                unit_original = _unit_from_text(title_text)
                table_family = _table_family_from_text(title_text)
                dimension_type = _dimension_type_from_text(
                    title_text + " " + " ".join(row_text(row) for row in rows[:12])
                )
                universe = _universe_from_text(title_text)
                has_section, has_detail = _activity_detail_flags(rows)
                notes_parts = ["detail_sheet_preferred"] if is_detail_sheet else []
                try:
                    bounds = detect_xls_table_bounds(rows)
                    header_start_row_zero_based = bounds.header_start_row
                    data_start_row_zero_based = bounds.data_start_row
                    first_data_label = bounds.first_data_label
                except ValueError as error:
                    header_start_row_zero_based = ""
                    data_start_row_zero_based = ""
                    first_data_label = ""
                    notes_parts.append(f"bounds_detection_failed: {error}")

                inventory.append(
                    {
                        "publication_year": publication_year,
                        "fiscal_year": fiscal_year if fiscal_year is not None else "",
                        "archive_filename": archive_name,
                        "period_id": "P1_new_html_detail",
                        "source_table_id": table_id,
                        "source_table_title": title_text,
                        "source_table_path": member_name,
                        "chapter_code_original": _chapter_code(table_id),
                        "table_family": table_family,
                        "dimension_type": dimension_type,
                        "universe": universe,
                        "format": "html_excel",
                        "unit_original": unit_original,
                        "has_activity_section": has_section,
                        "has_activity_3digit": has_detail,
                        "is_continuation": is_detail_sheet,
                        "header_start_row_zero_based": header_start_row_zero_based,
                        "data_start_row_zero_based": data_start_row_zero_based,
                        "first_data_label": first_data_label,
                        "n_rows": len(rows),
                        "n_cols": max((len(row) for row in rows), default=0),
                        "notes": "; ".join(notes_parts),
                    }
                )
    return inventory


def inventory_p2_old_html_millions(raw_archive_dir: Path) -> list[dict[str, Any]]:
    """Inventory Ganancias Sociedades P2 Excel-exported HTML activity tables.

    P2 covers publication year 2013 / fiscal year 2012. It keeps monetary
    values in millions of current pesos but switches to the old activity
    classifier. For maximum activity detail, `sheet002.htm` is preferred when
    present.
    """

    inventory: list[dict[str, Any]] = []
    for publication_year, archive_name in P2_HTML_ARCHIVES.items():
        archive_path = raw_archive_dir / archive_name
        with ZipFile(archive_path) as zip_file:
            for table_id in P2_ACTIVITY_TABLE_IDS:
                member_name, is_detail_sheet = _p2_sheet_member(zip_file, table_id)
                rows = html_rows_from_bytes(zip_file.read(member_name))
                title_lines = _title_lines(rows)
                title_text = " // ".join(title_lines)
                fiscal_year = _find_fiscal_year(title_text)
                unit_original = _unit_from_text(title_text)
                table_family = _table_family_from_text(title_text)
                dimension_type = _dimension_type_from_text(
                    title_text + " " + " ".join(row_text(row) for row in rows[:12])
                )
                universe = _universe_from_text(title_text)
                has_section, has_detail = _activity_detail_flags(rows)
                notes_parts = ["sheet002_detail_preferred"] if is_detail_sheet else []
                try:
                    bounds = detect_xls_table_bounds(rows)
                    header_start_row_zero_based = bounds.header_start_row
                    data_start_row_zero_based = bounds.data_start_row
                    first_data_label = bounds.first_data_label
                except ValueError as error:
                    header_start_row_zero_based = ""
                    data_start_row_zero_based = ""
                    first_data_label = ""
                    notes_parts.append(f"bounds_detection_failed: {error}")

                inventory.append(
                    {
                        "publication_year": publication_year,
                        "fiscal_year": fiscal_year if fiscal_year is not None else "",
                        "archive_filename": archive_name,
                        "period_id": "P2_old_html_detail_millions",
                        "source_table_id": table_id,
                        "source_table_title": title_text,
                        "source_table_path": member_name,
                        "chapter_code_original": _chapter_code(table_id),
                        "table_family": table_family,
                        "dimension_type": dimension_type,
                        "universe": universe,
                        "format": "html_excel",
                        "unit_original": unit_original,
                        "has_activity_section": has_section,
                        "has_activity_3digit": has_detail,
                        "is_continuation": is_detail_sheet,
                        "header_start_row_zero_based": header_start_row_zero_based,
                        "data_start_row_zero_based": data_start_row_zero_based,
                        "first_data_label": first_data_label,
                        "n_rows": len(rows),
                        "n_cols": max((len(row) for row in rows), default=0),
                        "notes": "; ".join(notes_parts),
                    }
                )
    return inventory


def inventory_p3_old_html_thousands(raw_archive_dir: Path) -> list[dict[str, Any]]:
    """Inventory Ganancias Sociedades P3 Excel-exported HTML activity tables.

    P3 covers publication years 2009-2012 / fiscal years 2008-2011. The source
    paths vary by archive, so table members are found by suffix and
    `sheet002.htm` is preferred when present.
    """

    inventory: list[dict[str, Any]] = []
    for publication_year, archive_name in P3_HTML_ARCHIVES.items():
        archive_path = raw_archive_dir / archive_name
        with ZipFile(archive_path) as zip_file:
            for table_id in P3_ACTIVITY_TABLE_IDS:
                member = _p3_sheet_member(zip_file, table_id)
                if member is None:
                    continue
                member_name, is_detail_sheet = member
                rows = html_rows_from_bytes(zip_file.read(member_name))
                title_lines = _title_lines(rows)
                title_text = " // ".join(title_lines)
                fiscal_year = _find_fiscal_year(title_text)
                unit_original = _unit_from_text(title_text)
                table_family = _table_family_from_text(title_text)
                dimension_type = _dimension_type_from_text(
                    title_text + " " + " ".join(row_text(row) for row in rows[:12])
                )
                universe = _universe_from_text(title_text)
                has_section, has_detail = _activity_detail_flags(rows)
                notes_parts = [
                    "sheet002_detail_preferred" if is_detail_sheet else "sheet001_only"
                ]
                if fiscal_year == 2008 and table_id == P0_ACTIVITY_COSTS_TABLE_ID:
                    notes_parts.append("fiscal_2008_costs_otros_component")
                if fiscal_year == 2008 and table_id in {
                    P0_ACTIVITY_SALES_DETAIL_TABLE_ID,
                    P0_ACTIVITY_COST_LINKED_EXPENSES_TABLE_ID,
                    P0_ACTIVITY_GROSS_RESULT_TABLE_ID,
                }:
                    notes_parts.append("fiscal_2008_source_table_id_semantic_shift")
                try:
                    bounds = detect_xls_table_bounds(rows)
                    header_start_row_zero_based = bounds.header_start_row
                    data_start_row_zero_based = bounds.data_start_row
                    first_data_label = bounds.first_data_label
                except ValueError as error:
                    header_start_row_zero_based = ""
                    data_start_row_zero_based = ""
                    first_data_label = ""
                    notes_parts.append(f"bounds_detection_failed: {error}")

                inventory.append(
                    {
                        "publication_year": publication_year,
                        "fiscal_year": fiscal_year if fiscal_year is not None else "",
                        "archive_filename": archive_name,
                        "period_id": "P3_old_html_detail_thousands",
                        "source_table_id": table_id,
                        "source_table_title": title_text,
                        "source_table_path": member_name,
                        "chapter_code_original": _chapter_code(table_id),
                        "table_family": table_family,
                        "dimension_type": dimension_type,
                        "universe": universe,
                        "format": "html_excel",
                        "unit_original": unit_original,
                        "has_activity_section": has_section,
                        "has_activity_3digit": has_detail,
                        "is_continuation": is_detail_sheet,
                        "header_start_row_zero_based": header_start_row_zero_based,
                        "data_start_row_zero_based": data_start_row_zero_based,
                        "first_data_label": first_data_label,
                        "n_rows": len(rows),
                        "n_cols": max((len(row) for row in rows), default=0),
                        "notes": "; ".join(notes_parts),
                    }
                )
    return inventory


def inventory_p4_old_cab_xls_thousands(raw_archive_dir: Path) -> list[dict[str, Any]]:
    """Inventory P4 Ganancias Sociedades CAB-nested XLS activity tables.

    P4 covers publication years 2003-2008 / fiscal years 2002-2007. Each ZIP
    contains `AFIP.CAB`; within it, `_2.xls` files are preferred because they
    contain the maximum available activity detail.
    """

    inventory: list[dict[str, Any]] = []
    for publication_year, archive_name in P4_CAB_XLS_ARCHIVES.items():
        archive_path = raw_archive_dir / archive_name
        with tempfile.TemporaryDirectory(prefix="afip_p4_inventory_") as temp_name:
            xls_paths = _extract_cab_xls_members_from_zip(archive_path, Path(temp_name))
            for table_id in P4_ACTIVITY_TABLE_IDS:
                preferred = _p4_preferred_member(xls_paths, table_id)
                if preferred is None:
                    continue
                xls_path, is_detail_file = preferred
                rows = xls_rows_from_bytes(xls_path.read_bytes())
                title_lines = _title_lines(rows)
                title_text = " // ".join(title_lines)
                fiscal_year = _find_fiscal_year(title_text)
                unit_original = _unit_from_text(title_text)
                table_family = _table_family_from_text(title_text)
                dimension_type = _dimension_type_from_text(
                    title_text + " " + " ".join(row_text(row) for row in rows[:12])
                )
                universe = _universe_from_text(title_text)
                has_section, has_detail = _activity_detail_flags(rows)
                notes_parts = [
                    "cab_nested_xls",
                    "xls_2_detail_preferred" if is_detail_file else "base_xls_only",
                ]
                if table_id == P0_ACTIVITY_COSTS_TABLE_ID:
                    notes_parts.append("old_costs_otros_component")
                if table_id in {
                    P0_ACTIVITY_SALES_DETAIL_TABLE_ID,
                    P0_ACTIVITY_COST_LINKED_EXPENSES_TABLE_ID,
                    P0_ACTIVITY_GROSS_RESULT_TABLE_ID,
                }:
                    notes_parts.append("old_result_table_numbering")
                try:
                    bounds = detect_xls_table_bounds(rows)
                    header_start_row_zero_based = bounds.header_start_row
                    data_start_row_zero_based = bounds.data_start_row
                    first_data_label = bounds.first_data_label
                except ValueError as error:
                    header_start_row_zero_based = ""
                    data_start_row_zero_based = ""
                    first_data_label = ""
                    notes_parts.append(f"bounds_detection_failed: {error}")

                inventory.append(
                    {
                        "publication_year": publication_year,
                        "fiscal_year": fiscal_year if fiscal_year is not None else "",
                        "archive_filename": archive_name,
                        "period_id": "P4_old_cab_xls_detail_thousands",
                        "source_table_id": table_id,
                        "source_table_title": title_text,
                        "source_table_path": _p4_cab_member_path(xls_path.name),
                        "chapter_code_original": _chapter_code(table_id),
                        "table_family": table_family,
                        "dimension_type": dimension_type,
                        "universe": universe,
                        "format": "xls_in_cab",
                        "unit_original": unit_original,
                        "has_activity_section": has_section,
                        "has_activity_3digit": has_detail,
                        "is_continuation": is_detail_file,
                        "header_start_row_zero_based": header_start_row_zero_based,
                        "data_start_row_zero_based": data_start_row_zero_based,
                        "first_data_label": first_data_label,
                        "n_rows": len(rows),
                        "n_cols": max((len(row) for row in rows), default=0),
                        "notes": "; ".join(notes_parts),
                    }
                )
    return inventory


def inventory_p5_old_cab_xls_legacy_numbering(raw_archive_dir: Path) -> list[dict[str, Any]]:
    """Inventory P5 legacy-numbered Ganancias Sociedades CAB/XLS tables.

    P5 uses the publication-year 2002 CAB as the canonical source for fiscal
    years 1999-2001 because that archive contains the latest available copies
    for the duplicated historical fiscal years.
    """

    inventory: list[dict[str, Any]] = []
    publication_year = 2002
    archive_name = P5_CAB_XLS_ARCHIVES[publication_year]
    archive_path = raw_archive_dir / archive_name
    with tempfile.TemporaryDirectory(prefix="afip_p5_inventory_") as temp_name:
        xls_paths = _extract_cab_xls_members_from_zip(
            archive_path,
            Path(temp_name),
            "3.3.1.1*.xls",
        )
        for fiscal_year in (1999, 2000, 2001):
            for table_id in _p5_activity_table_ids(fiscal_year):
                preferred = _p5_preferred_member(xls_paths, table_id, fiscal_year)
                if preferred is None:
                    continue
                xls_path, is_detail_file = preferred
                rows = xls_rows_from_bytes(xls_path.read_bytes())
                title_lines = _title_lines(rows)
                title_text = " // ".join(title_lines)
                detected_fiscal_year = _find_fiscal_year(title_text)
                unit_original = _unit_from_text(title_text)
                table_family = _table_family_from_text(title_text)
                dimension_type = _dimension_type_from_text(
                    title_text + " " + " ".join(row_text(row) for row in rows[:12])
                )
                universe = _universe_from_text(title_text)
                has_section, has_detail = _activity_detail_flags(rows)
                notes_parts = [
                    "cab_nested_xls",
                    "xls_2_detail_preferred" if is_detail_file else "base_xls_only",
                    "canonical_latest_publication_2002",
                    f"source_year_suffix_{_p5_source_year_suffix(fiscal_year)}",
                ]
                if fiscal_year in {1999, 2000}:
                    notes_parts.append("legacy_four_table_schema")
                    notes_parts.append("supersedes_publication_2000_2001_duplicates")
                if fiscal_year in {1999, 2000} and table_id == P5_LEGACY_ACTIVITY_SUMMARY_TABLE_ID:
                    notes_parts.append("summary_count_is_ganancia_neta_imponible")
                if fiscal_year in {1999, 2000} and table_id == P5_LEGACY_ACTIVITY_RESULTS_TABLE_ID:
                    notes_parts.append("old_result_final_ejercicio_mapped_to_resultado_contable")
                if fiscal_year in {1999, 2000} and table_id == P5_LEGACY_ACTIVITY_TAX_RESULT_TABLE_ID:
                    notes_parts.append("old_tax_quebranto_mapped_to_resultado_impositivo_perdida")
                if fiscal_year in {1999, 2000} and table_id == P5_LEGACY_ACTIVITY_BALANCE_TABLE_ID:
                    notes_parts.append("old_aggregate_balance_sheet")
                if fiscal_year == 2001:
                    notes_parts.append("legacy_numbering_expanded_2001")
                if fiscal_year == 2001 and table_id == P5_LEGACY_ACTIVITY_COSTS_TABLE_ID:
                    notes_parts.append("old_costs_otros_component")
                try:
                    bounds = detect_xls_table_bounds(rows)
                    header_start_row_zero_based = bounds.header_start_row
                    data_start_row_zero_based = bounds.data_start_row
                    first_data_label = bounds.first_data_label
                except ValueError as error:
                    header_start_row_zero_based = ""
                    data_start_row_zero_based = ""
                    first_data_label = ""
                    notes_parts.append(f"bounds_detection_failed: {error}")

                inventory.append(
                    {
                        "publication_year": publication_year,
                        "fiscal_year": detected_fiscal_year if detected_fiscal_year is not None else "",
                        "archive_filename": archive_name,
                        "period_id": "P5_old_cab_xls_detail_legacy_numbering",
                        "source_table_id": table_id,
                        "source_table_title": title_text,
                        "source_table_path": _p4_cab_member_path(xls_path.name),
                        "chapter_code_original": _chapter_code(table_id),
                        "table_family": table_family,
                        "dimension_type": dimension_type,
                        "universe": universe,
                        "format": "xls_in_cab",
                        "unit_original": unit_original,
                        "has_activity_section": has_section,
                        "has_activity_3digit": has_detail,
                        "is_continuation": is_detail_file,
                        "header_start_row_zero_based": header_start_row_zero_based,
                        "data_start_row_zero_based": data_start_row_zero_based,
                        "first_data_label": first_data_label,
                        "n_rows": len(rows),
                        "n_cols": max((len(row) for row in rows), default=0),
                        "notes": "; ".join(notes_parts),
                    }
                )
    return inventory


def inventory_p6_legacy_broad_activity(raw_archive_dir: Path) -> list[dict[str, Any]]:
    """Inventory P6 Ganancias Sociedades direct-XLS legacy activity tables."""

    inventory: list[dict[str, Any]] = []
    publication_fiscal_pairs = ((1998, 1997), (1999, 1998))
    for publication_year, fiscal_year in publication_fiscal_pairs:
        archive_name = _p6_archive_name(publication_year)
        archive_path = raw_archive_dir / archive_name
        with ZipFile(archive_path) as zip_file:
            member_names = [
                member
                for member in zip_file.namelist()
                if member.lower().endswith(".xls")
            ]
            for table_id in _p6_activity_table_ids(fiscal_year):
                preferred = _p6_preferred_member(member_names, table_id, fiscal_year)
                if preferred is None:
                    continue
                member_name, is_detail_file = preferred
                rows = xls_rows_from_bytes(zip_file.read(member_name))
                title_lines = _title_lines(rows)
                title_text = " // ".join(title_lines)
                detected_fiscal_year = _find_fiscal_year(title_text)
                unit_original = _unit_from_text(title_text)
                table_family = _table_family_from_text(title_text)
                dimension_type = _dimension_type_from_text(
                    title_text + " " + " ".join(row_text(row) for row in rows[:12])
                )
                universe = _universe_from_text(title_text)
                has_section, has_detail = _activity_detail_flags(rows)
                notes_parts = ["direct_xls_install_layout", "legacy_four_table_schema"]
                if fiscal_year == 1997:
                    notes_parts.append("legacy_44_numbering_1997")
                    notes_parts.append("broad_activity_only")
                    notes_parts.append("no_3digit_detail_observed")
                if fiscal_year == 1998:
                    notes_parts.append("legacy_33_numbering_1998")
                    notes_parts.append(
                        "xls_2_detail_preferred" if is_detail_file else "base_xls_only"
                    )
                    if has_detail:
                        notes_parts.append("p6_1998_has_3digit_detail")
                if table_id in {
                    P6_1997_ACTIVITY_SUMMARY_TABLE_ID,
                    P6_1998_ACTIVITY_SUMMARY_TABLE_ID,
                }:
                    notes_parts.append("summary_count_is_ganancia_neta_imponible")
                if table_id in {
                    P6_1997_ACTIVITY_RESULTS_TABLE_ID,
                    P6_1998_ACTIVITY_RESULTS_TABLE_ID,
                }:
                    notes_parts.append("old_result_final_ejercicio_mapped_to_resultado_contable")
                if table_id == P6_1997_ACTIVITY_TAX_ADJUSTMENTS_TABLE_ID:
                    notes_parts.append("tax_adjustment_columns_only_in_fiscal_1997")
                if table_id == P6_1998_ACTIVITY_TAX_RESULT_TABLE_ID:
                    notes_parts.append("old_tax_quebranto_mapped_to_resultado_impositivo_perdida")
                if table_id in {
                    P6_1997_ACTIVITY_BALANCE_TABLE_ID,
                    P6_1998_ACTIVITY_BALANCE_TABLE_ID,
                }:
                    notes_parts.append("old_aggregate_balance_sheet")
                try:
                    bounds = detect_xls_table_bounds(rows)
                    header_start_row_zero_based = bounds.header_start_row
                    data_start_row_zero_based = bounds.data_start_row
                    first_data_label = bounds.first_data_label
                except ValueError as error:
                    header_start_row_zero_based = ""
                    data_start_row_zero_based = ""
                    first_data_label = ""
                    notes_parts.append(f"bounds_detection_failed: {error}")

                inventory.append(
                    {
                        "publication_year": publication_year,
                        "fiscal_year": (
                            detected_fiscal_year
                            if detected_fiscal_year is not None
                            else fiscal_year
                        ),
                        "archive_filename": archive_name,
                        "period_id": "P6_legacy_broad_activity",
                        "source_table_id": table_id,
                        "source_table_title": title_text,
                        "source_table_path": member_name,
                        "chapter_code_original": _chapter_code(table_id),
                        "table_family": table_family,
                        "dimension_type": dimension_type,
                        "universe": universe,
                        "format": "direct_xls",
                        "unit_original": unit_original,
                        "has_activity_section": has_section,
                        "has_activity_3digit": has_detail,
                        "is_continuation": is_detail_file,
                        "header_start_row_zero_based": header_start_row_zero_based,
                        "data_start_row_zero_based": data_start_row_zero_based,
                        "first_data_label": first_data_label,
                        "n_rows": len(rows),
                        "n_cols": max((len(row) for row in rows), default=0),
                        "notes": "; ".join(notes_parts),
                    }
                )
    return inventory


def inventory_p0_backward_xls(raw_archive_dir: Path) -> list[dict[str, Any]]:
    """Inventory P0 backward-extension Ganancias Sociedades activity XLS tables.

    Scope is publication years 2015-2020, fiscal years 2014-2019, direct XLS
    files and `2.3.1.1.*` activity tables. This is a structural Fase 3
    inventory: it deliberately does not modify the already validated P0 recent
    inventory or extract statistical values.
    """

    inventory: list[dict[str, Any]] = []
    for publication_year, archive_name in P0_BACKWARD_XLS_ARCHIVES.items():
        archive_path = raw_archive_dir / archive_name
        with ZipFile(archive_path) as zip_file:
            members = sorted(
                name
                for name in zip_file.namelist()
                if name.lower().endswith(".xls") and "/2.3.1.1." in name
            )
            for member_name in members:
                rows = xls_rows_from_bytes(zip_file.read(member_name))
                title_lines = _title_lines(rows)
                title_text = " // ".join(title_lines)
                fiscal_year = _find_fiscal_year(title_text)
                unit_original = _unit_from_text(title_text)
                table_family = _table_family_from_text(title_text)
                dimension_text = title_text + " " + " ".join(row_text(row) for row in rows[:12])
                dimension_type = _dimension_type_from_text(dimension_text)
                universe = _universe_from_text(title_text)
                has_section, has_detail = _activity_detail_flags(rows)
                source_id = _source_table_id(member_name)
                notes_parts: list[str] = []
                if re.search(r"_2-?$", source_id):
                    notes_parts.append("continuation_suffix")
                try:
                    bounds = detect_xls_table_bounds(rows)
                    header_start_row_zero_based = bounds.header_start_row
                    data_start_row_zero_based = bounds.data_start_row
                    first_data_label = bounds.first_data_label
                except ValueError as error:
                    header_start_row_zero_based = ""
                    data_start_row_zero_based = ""
                    first_data_label = ""
                    notes_parts.append(f"bounds_detection_failed: {error}")

                inventory.append(
                    {
                        "publication_year": publication_year,
                        "fiscal_year": fiscal_year if fiscal_year is not None else "",
                        "archive_filename": archive_name,
                        "period_id": "P0_new_xls_backward_probe",
                        "source_table_id": source_id,
                        "source_table_title": title_text,
                        "source_table_path": member_name,
                        "chapter_code_original": _chapter_code(source_id),
                        "table_family": table_family,
                        "dimension_type": dimension_type,
                        "universe": universe,
                        "format": "xls",
                        "unit_original": unit_original,
                        "has_activity_section": has_section,
                        "has_activity_3digit": has_detail,
                        "is_continuation": bool(re.search(r"_2-?$", source_id)),
                        "header_start_row_zero_based": header_start_row_zero_based,
                        "data_start_row_zero_based": data_start_row_zero_based,
                        "first_data_label": first_data_label,
                        "n_rows": len(rows),
                        "n_cols": max((len(row) for row in rows), default=0),
                        "notes": "; ".join(notes_parts),
                    }
                )
    return inventory


def inventory_fieldnames() -> list[str]:
    """Return the canonical CSV field order for the table inventory."""

    return [
        "publication_year",
        "fiscal_year",
        "archive_filename",
        "period_id",
        "source_table_id",
        "source_table_title",
        "source_table_path",
        "chapter_code_original",
        "table_family",
        "dimension_type",
        "universe",
        "format",
        "unit_original",
        "has_activity_section",
        "has_activity_3digit",
        "is_continuation",
        "header_start_row_zero_based",
        "data_start_row_zero_based",
        "first_data_label",
        "n_rows",
        "n_cols",
        "notes",
    ]


def long_fieldnames() -> list[str]:
    """Return the canonical CSV field order for long-format extracts."""

    return [
        "publication_year",
        "fiscal_year",
        "archive_filename",
        "period_id",
        "source_table_id",
        "source_table_path",
        "source_table_title",
        "table_family",
        "universe",
        "dimension_type",
        "dimension_value",
        "activity_level",
        "activity_code",
        "activity_label_original",
        "activity_section_original",
        "classifier_period",
        "variable_name",
        "value",
        "unit_original",
        "value_pesos_current",
        "source_note",
        "header_start_row_zero_based",
        "data_start_row_zero_based",
        "source_row_zero_based",
        "source_column_zero_based",
    ]
