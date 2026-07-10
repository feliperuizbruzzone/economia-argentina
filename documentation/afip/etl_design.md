# AFIP Ganancias Sociedades ETL Design

Este documento define el diseno modular del pipeline ETL para el capitulo
`Impuesto a las Ganancias Sociedades`.

No resuelve el pipeline completo. El desarrollo debe avanzar iterativamente:
una funcion, un ejemplo real, una validacion, y recien despues ampliar cobertura.

Estado actual: el periodo `P0_new_xls_detail` ya esta implementado para
publication years 2015-2023 / fiscal years 2014-2022. El ensamble largo P0
contiene 491.435 filas y la validacion consolidada termina con 0 fallas y
0 advertencias. El periodo `P1_new_html_detail` tambien esta implementado
para publication year 2014 / fiscal year 2013, con 37.088 filas largas y
validacion de 0 fallas y 0 advertencias. El periodo
`P2_old_html_detail_millions` esta implementado para publication year 2013 /
fiscal year 2012, con 27.208 filas largas y validacion de 0 fallas y 0
advertencias. El periodo `P3_old_html_detail_thousands` esta implementado
para publication years 2009-2012 / fiscal years 2008-2011, con 97.775 filas
largas, validacion de 0 fallas y 10 advertencias estructurales. Las
advertencias y notas de periodo P0-P6 quedan documentadas en
`documentation/afip/warnings_by_period.md`.

Las secciones de probes iniciales que siguen quedan como historial de
desarrollo incremental; el estado operativo vigente es el resumido arriba.

## Objetivo Del Pipeline

Construir una base larga con columnas canonicas consistentes entre epocas,
preservando el maximo nivel de desagregacion disponible en cada periodo.

Salidas finales actuales:

```text
data/analysis-data/2026-05-31_afip_ganancias_sociedades_long_sin_homologar.csv
data/analysis-data/2026-05-31_afip_ganancias_sociedades_long_homologada.csv
```

## Columnas Canonicas

Campos minimos de la base larga:

- `publication_year`
- `fiscal_year`
- `archive_filename`
- `period_id`
- `source_table_id`
- `source_table_path`
- `source_table_title`
- `table_family`
- `universe`
- `dimension_type`
- `dimension_value`
- `activity_level`
- `activity_code`
- `activity_label_original`
- `activity_section_original`
- `classifier_period`
- `variable_name`
- `value`
- `unit_original`
- `value_pesos_current`
- `source_note`
- `header_start_row_zero_based`
- `data_start_row_zero_based`

## Funciones Modulares Propuestas

```python
def build_ganancias_sociedades_inventory(raw_dir: Path) -> list[dict]:
    """Inventory all Ganancias Sociedades tables, continuations and sheets.

    The function identifies publication year, fiscal year, source table id,
    source path, table family, original unit, universe and whether the member
    contains activity-section or activity-detail rows.
    """
```

```python
def detect_xls_table_bounds(rows: Sequence[Sequence[Any]]) -> TableBounds:
    """Detect header and data-start rows in an AFIP XLS statistical table.

    Detection must use semantic labels and numeric/data-row evidence, not fixed
    row numbers. This is the first implemented function.
    """
```

```python
def extract_p0_new_xls_detail(inventory_rows: list[dict]) -> Iterable[dict]:
    """Extract fiscal years 2014-2022 from direct XLS files.

    Covers publication years 2015-2023. This is the baseline extractor because
    it uses the newest classifier, direct XLS files and the most regular layout.
    """
```

```python
def extract_p1_new_html_detail(inventory_rows: list[dict]) -> Iterable[dict]:
    """Extract fiscal year 2013 from Excel-exported HTML with the new classifier.

    Must preserve secondary sheet/detail files when the maximum activity detail
    is not in the first visible sheet.
    """
```

```python
def extract_p2_p3_old_html_detail(inventory_rows: list[dict]) -> Iterable[dict]:
    """Extract fiscal years 2008-2012 from Excel-exported HTML.

    Must inspect `sheet002.htm` and other continuations before concluding that
    activity detail is absent.
    """
```

```python
def extract_p4_old_xls_cab_detail(inventory_rows: list[dict]) -> Iterable[dict]:
    """Extract fiscal years 2002-2007 from XLS files embedded in AFIP.CAB.

    Must read CAB members, map `2.3.*` tables and include continuation files
    such as `_2` when they contain activity-detail rows.
    """
```

```python
def extract_p5_old_xls_legacy_numbering(inventory_rows: list[dict]) -> Iterable[dict]:
    """Extract fiscal years 1999-2001 from legacy-numbered `3.3.*` tables.

    Must resolve fiscal-year duplicates embedded in 2001-2002 ZIPs before
    selecting canonical source tables.
    """
```

```python
def extract_p6_legacy_broad_activity(inventory_rows: list[dict]) -> Iterable[dict]:
    """Extract fiscal years 1997-1998 from legacy direct-XLS tables.

    Must preserve broad activity rows for fiscal 1997 and observed 3-digit
    continuation rows for fiscal 1998.
    """
```

```python
def normalize_long_rows(rows: Iterable[dict]) -> Iterable[dict]:
    """Normalize units, variable names and metadata to the canonical long schema.

    This function should preserve original labels and units while adding
    normalized fields such as `value_pesos_current`.
    """
```

## Iterative Development Order

1. Implement and test `detect_xls_table_bounds()` against one 2023 XLS table.
2. Build the Ganancias Sociedades inventory for 2021-2023 first.
3. Extract one table family from 2021-2023 into long format.
4. Expand to all `2.3.*` Ganancias Sociedades tables in 2021-2023.
5. Extend P0 backward to 2015-2020. Estado: completado.
6. Add HTML parser for 2014, then 2013, then 2009-2012. Estado: completado.
7. Add CAB/XLS parser for 2003-2008. Estado: completado.
8. Add legacy `3.3.*` parser for 1999-2001. Estado: completado.
9. Add broad/mixed activity parser for 1997-1998. Estado: completado.

## First Implemented Probe

Implemented function:

```text
command-files/processing-command-files/afip_ganancias_sociedades.py::detect_xls_table_bounds
```

Implemented inventory function:

```text
command-files/processing-command-files/afip_ganancias_sociedades.py::inventory_p0_modern_xls
```

Inventory command:

```bash
python3 command-files/processing-command-files/02_build_ganancias_sociedades_inventory.py
```

Inventory output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory.csv
```

First validation command:

```bash
python3 command-files/processing-command-files/03_validate_ganancias_sociedades_p0_activity_inventory.py
```

Validation scope:

- `P0_new_xls_detail`
- tables with source-table id prefix `2.3.1.1.`
- dimension type `actividad_economica`

Validation outputs:

```text
data/output-data/validation_reports/ganancias_sociedades_p0_activity_inventory_validation.md
data/output-data/validation_reports/ganancias_sociedades_p0_activity_inventory_validation.csv
```

Current validation result:

- 60 rows validated.
- fiscal years 2020, 2021 and 2022.
- 20 activity tables per fiscal year.
- 0 hard failures.
- 1 warning: fiscal year 2022, table `2.3.1.1.5.2.1`, starts at activity section `A - Agricultura, ganaderia, caza, silvicultura y pesca` because no `TOTAL` row is present in that source sheet.

First long extraction command:

```bash
python3 command-files/processing-command-files/04_extract_ganancias_sociedades_p0_2_3_1_1_1.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.1`
- fiscal years 2020, 2021 and 2022
- activity dimension
- six variables: presentations total, presentations with sales, presentations with assessed tax, sales, taxable net income and assessed tax

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_1.csv
```

First long extraction validation command:

```bash
python3 command-files/processing-command-files/05_validate_ganancias_sociedades_p0_2_3_1_1_1.py
```

Current extraction validation result:

- 4,344 long rows.
- 724 rows per variable.
- 0 hard failures.
- 0 warnings.
- `casos` used for presentation-count variables.
- `millones_pesos_corrientes` used for monetary variables, with `value_pesos_current` normalized by multiplying by 1,000,000.

Second long extraction command:

```bash
python3 command-files/processing-command-files/06_extract_ganancias_sociedades_p0_2_3_1_1_2_1.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.2.1`
- fiscal years 2020, 2021 and 2022
- activity dimension
- paired `Casos` and `Importe` columns for sales, total costs, purchases, production expenses, cost-linked expenses, opening inventories and closing inventories

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_1.csv
```

Second long extraction validation command:

```bash
python3 command-files/processing-command-files/07_validate_ganancias_sociedades_p0_2_3_1_1_2_1.py
```

Current second extraction validation result:

- 10,860 long rows.
- 724 rows per variable.
- 15 variables.
- 0 hard failures.
- 0 warnings.
- 2,172 overlapping rows checked against table `2.3.1.1.1` with no discrepancies.

Third long extraction command:

```bash
python3 command-files/processing-command-files/08_extract_ganancias_sociedades_p0_2_3_1_1_2_2.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.2.2`
- fiscal years 2020, 2021 and 2022
- activity dimension
- paired `Casos` and `Importe` columns for detailed sales, exports and export duties

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_2.csv
```

Third long extraction validation command:

```bash
python3 command-files/processing-command-files/09_validate_ganancias_sociedades_p0_2_3_1_1_2_2.py
```

Current third extraction validation result:

- 15,204 long rows.
- 724 rows per variable.
- 21 variables.
- 0 hard failures.
- 0 warnings.
- 2,172 overlapping rows checked against table `2.3.1.1.1`.
- 2,172 overlapping rows checked against table `2.3.1.1.2.1`.
- Internal sales identities pass: net sales plus export duties equals total sales of the fiscal year, and detailed sales components sum to total sales of the fiscal year.

Fourth long extraction command:

```bash
python3 command-files/processing-command-files/10_extract_ganancias_sociedades_p0_2_3_1_1_2_3.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.2.3`
- fiscal years 2020, 2021 and 2022
- activity dimension
- cost-linked expense total and paired `Casos`/`Importe` component columns

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_3.csv
```

Fourth long extraction validation command:

```bash
python3 command-files/processing-command-files/11_validate_ganancias_sociedades_p0_2_3_1_1_2_3.py
```

Current fourth extraction validation result:

- 7,240 long rows.
- 724 rows per variable.
- 10 variables.
- 0 hard failures.
- 0 warnings.
- 1,448 overlapping rows checked against table `2.3.1.1.2.1`.
- Internal component identity passes: depreciation, fees, other cost-linked expenses and wages/social contributions sum to total cost-linked expenses.

Fifth long extraction command:

```bash
python3 command-files/processing-command-files/12_extract_ganancias_sociedades_p0_2_3_1_1_2_4.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.2.4`
- fiscal years 2020, 2021 and 2022
- activity dimension
- gross result utility/loss pairs, share-sale result utility/loss pairs, bad-debt charge and operating expenses

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_4.csv
```

Fifth long extraction validation command:

```bash
python3 command-files/processing-command-files/13_validate_ganancias_sociedades_p0_2_3_1_1_2_4.py
```

Current fifth extraction validation result:

- 9,412 long rows.
- 724 rows per variable.
- 13 variables.
- 0 hard failures.
- 0 warnings.
- 724 overlapping rows checked against table `2.3.1.1.2.1` for `presentaciones_total`.
- Cross-table identity passes: `resultado_bruto_utilidad - resultado_bruto_perdida` equals `ventas_bienes_servicios_locaciones_netas - costos_total`.

Sixth long extraction command:

```bash
python3 command-files/processing-command-files/14_extract_ganancias_sociedades_p0_2_3_1_1_2_5.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.2.5`
- fiscal years 2020, 2021 and 2022
- activity dimension
- operating expense total and paired `Casos`/`Importe` component columns

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_5.csv
```

Sixth long extraction validation command:

```bash
python3 command-files/processing-command-files/15_validate_ganancias_sociedades_p0_2_3_1_1_2_5.py
```

Current sixth extraction validation result:

- 10,136 long rows.
- 724 rows per variable.
- 14 variables.
- 0 hard failures.
- 1 warning.
- 1,448 overlapping rows checked against table `2.3.1.1.2.4`.
- Internal component identity passes: depreciation, representation expenses, directors' fees, service fees, other operating expenses and wages/social contributions sum to total operating expenses.
- Source warning: fiscal year 2022, activity `071;072`, `gastos_operativos` differs between table `2.3.1.1.2.5` and table `2.3.1.1.2.4`; extraction keeps each table-specific source value.

Seventh long extraction command:

```bash
python3 command-files/processing-command-files/16_extract_ganancias_sociedades_p0_2_3_1_1_2_6.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.2.6`
- fiscal years 2020, 2021 and 2022
- activity dimension
- utility/quebranto pairs for permanent investments, financial results, derivative contracts, and other income/expenses

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_6.csv
```

Seventh long extraction validation command:

```bash
python3 command-files/processing-command-files/17_validate_ganancias_sociedades_p0_2_3_1_1_2_6.py
```

Current seventh extraction validation result:

- 12,308 long rows.
- 724 rows per variable.
- 17 variables.
- 0 hard failures.
- 0 warnings.
- 724 overlapping rows checked against table `2.3.1.1.1` for `presentaciones_total`.
- Coverage is complete by fiscal year, variable and activity dimension. No accounting identity was enforced because the table does not expose a closed total already available in extracted tables.

Eighth long extraction command:

```bash
python3 command-files/processing-command-files/18_extract_ganancias_sociedades_p0_2_3_1_1_2_7.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.2.7`
- fiscal years 2020, 2021 and 2022
- activity dimension
- extraordinary results, income tax, accounting result, and the fiscal-year-2022-only games/gambling accounting-result columns

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_7.csv
```

Eighth long extraction validation command:

```bash
python3 command-files/processing-command-files/19_validate_ganancias_sociedades_p0_2_3_1_1_2_7.py
```

Current eighth extraction validation result:

- 8,448 long rows.
- 724 rows per common variable.
- 242 rows per fiscal-year-2022-only games/gambling variable.
- 13 variables total, with 11 common variables and 2 source-specific variables observed only in fiscal year 2022.
- 0 hard failures.
- 1 warning for the fiscal-year-2022-only structural addition.
- 724 overlapping rows checked against table `2.3.1.1.1` for `presentaciones_total`.
- No accounting identity was enforced for `resultado_contable`; doing so would require a documented methodological decision about which components and the games/gambling adjustment to include.

Ninth long extraction command:

```bash
python3 command-files/processing-command-files/20_extract_ganancias_sociedades_p0_2_3_1_1_3.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.3`
- fiscal years 2020, 2021 and 2022
- activity dimension
- tax-result adjustments, tax-result utility/loss pairs, and computable tax-loss variables

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_3.csv
```

Ninth long extraction validation command:

```bash
python3 command-files/processing-command-files/21_validate_ganancias_sociedades_p0_2_3_1_1_3.py
```

Current ninth extraction validation result:

- 7,964 long rows.
- 724 rows per variable.
- 11 variables.
- 0 hard failures.
- 1 warning for the fiscal-year-2020 degraded header on `resultado_impositivo_perdida`.
- 724 overlapping rows checked against table `2.3.1.1.1` for `presentaciones_total`.
- No identity was enforced against taxable net income because that requires a methodological decision about utility, loss and computable tax-loss treatment.

Tenth long extraction command:

```bash
python3 command-files/processing-command-files/22_extract_ganancias_sociedades_p0_2_3_1_1_4.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.4`
- fiscal years 2020, 2021 and 2022
- activity dimension
- net result, partner-attributable result, final net result and assessed-tax variables

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_4.csv
```

Tenth long extraction validation command:

```bash
python3 command-files/processing-command-files/23_validate_ganancias_sociedades_p0_2_3_1_1_4.py
```

Current tenth extraction validation result:

- 10,860 long rows.
- 724 rows per variable.
- 15 variables.
- 0 hard failures.
- 0 warnings.
- 2,172 overlapping rows checked against table `2.3.1.1.1`.
- Cross-table checks pass for `presentaciones_total`, `resultado_neto_final_utilidad` against `ganancia_neta_imponible`, and `impuesto_determinado`.

Eleventh long extraction command:

```bash
python3 command-files/processing-command-files/24_extract_ganancias_sociedades_p0_2_3_1_1_5_1.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.5.1`
- fiscal years 2020, 2021 and 2022
- activity dimension
- balance-sheet asset total and paired `Casos`/`Importe` columns for cash assets, credits, inventories, investments, fixed assets, intangible assets and construction work in progress

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_5_1.csv
```

Eleventh long extraction validation command:

```bash
python3 command-files/processing-command-files/25_validate_ganancias_sociedades_p0_2_3_1_1_5_1.py
```

Current eleventh extraction validation result:

- 12,308 long rows.
- 724 rows per variable.
- 17 variables.
- 0 hard failures.
- 0 warnings.
- 724 overlapping rows checked against table `2.3.1.1.1` for `presentaciones_total`.
- Internal asset identity passes: cash assets, credits, inventories, investments, fixed assets, intangible assets and construction work in progress sum to total assets.

Twelfth long extraction command:

```bash
python3 command-files/processing-command-files/26_extract_ganancias_sociedades_p0_2_3_1_1_5_1_1.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.5.1.1`
- fiscal years 2020, 2021 and 2022
- activity dimension
- cash-assets total and paired `Casos`/`Importe` component columns for checks in portfolio, cash in national currency, total banks and cash in foreign currency

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_5_1_1.csv
```

Twelfth long extraction validation command:

```bash
python3 command-files/processing-command-files/27_validate_ganancias_sociedades_p0_2_3_1_1_5_1_1.py
```

Current twelfth extraction validation result:

- 7,964 long rows.
- 724 rows per variable.
- 11 variables.
- 0 hard failures.
- 0 warnings.
- 1,448 overlapping rows checked against table `2.3.1.1.5.1` for `presentaciones_total` and `activo_disponibilidades`.
- Internal cash-asset identity passes: checks in portfolio, cash in national currency, total banks and cash in foreign currency sum to total cash assets.
- The column detector resolves the source header overlap by checking the more specific `TOTAL BANCOS` pattern before the broad `DISPONIBILIDADES TOTAL` pattern, without fixed row or column positions.

Thirteenth long extraction command:

```bash
python3 command-files/processing-command-files/28_extract_ganancias_sociedades_p0_2_3_1_1_5_1_2.py
```

Extraction scope:

- `P0_new_xls_detail`
- table `2.3.1.1.5.1.2`
- fiscal years 2020, 2021 and 2022
- activity dimension
- credit-assets total and paired `Casos`/`Importe` component columns for provisions, trade/service debtors, controlled/controlling/linked companies, partners' current accounts and other credits

Extraction output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_5_1_2.csv
```

Thirteenth long extraction validation command:

```bash
python3 command-files/processing-command-files/29_validate_ganancias_sociedades_p0_2_3_1_1_5_1_2.py
```

Current thirteenth extraction validation result:

- 9,400 long rows.
- 723 rows per credit variable and 724 rows for `presentaciones_total`.
- 13 variables.
- 0 hard failures.
- 2 warnings for the same source anomaly: fiscal year 2020, activity `352;353`, has `presentaciones_total=40` in the detail table but blank credit-value columns, while aggregate table `2.3.1.1.5.1` reports `activo_creditos=79244.52968623998`.
- 1,447 overlapping rows checked against table `2.3.1.1.5.1`.
- Internal credit-asset identity passes where detail values are observed: trade/service debtors, linked companies, partners' current accounts and other credits, net of provisions, sum to total credits.
- The extraction preserves observed source cells only; do not impute the missing detailed credit row from aggregate table `2.3.1.1.5.1` in the base extract.

Remaining P0 balance-sheet extraction commands:

| Table | Extract command | Validate command | Rows | Validation result |
|---|---|---|---:|---|
| `2.3.1.1.5.1.3` | `30_extract_ganancias_sociedades_p0_2_3_1_1_5_1_3.py` | `31_validate_ganancias_sociedades_p0_2_3_1_1_5_1_3.py` | 9,412 | 0 failures, 0 warnings |
| `2.3.1.1.5.1.4` | `32_extract_ganancias_sociedades_p0_2_3_1_1_5_1_4.py` | `33_validate_ganancias_sociedades_p0_2_3_1_1_5_1_4.py` | 7,964 | 0 failures, 0 warnings |
| `2.3.1.1.5.2` | `34_extract_ganancias_sociedades_p0_2_3_1_1_5_2.py` | `35_validate_ganancias_sociedades_p0_2_3_1_1_5_2.py` | 5,068 | 0 failures, 0 warnings |
| `2.3.1.1.5.2.1` | `36_extract_ganancias_sociedades_p0_2_3_1_1_5_2_1.py` | `37_validate_ganancias_sociedades_p0_2_3_1_1_5_2_1.py` | 13,737 | 0 failures, 2 warnings |
| `2.3.1.1.5.3` | `38_extract_ganancias_sociedades_p0_2_3_1_1_5_3.py` | `39_validate_ganancias_sociedades_p0_2_3_1_1_5_3.py` | 12,308 | 0 failures, 0 warnings |
| `2.3.1.1.5.3.1` | `40_extract_ganancias_sociedades_p0_2_3_1_1_5_3_1.py` | `41_validate_ganancias_sociedades_p0_2_3_1_1_5_3_1.py` | 6,516 | 0 failures, 0 warnings |
| `2.3.1.1.5.3.2` | `42_extract_ganancias_sociedades_p0_2_3_1_1_5_3_2.py` | `43_validate_ganancias_sociedades_p0_2_3_1_1_5_3_2.py` | 7,954 | 0 failures, 2 warnings |

Notes for the last P0 balance-sheet block:

- `2.3.1.1.5.2.1` has no source `TOTAL` row in fiscal year 2022; validation treats the missing `TOTAL` overlap against `2.3.1.1.5.2` as a warning, not an imputation target.
- `2.3.1.1.5.3.2` has a fiscal-year-2020 presentation-only row for activity `267;268`; the detail values are blank while `2.3.1.1.5.3` reports the aggregate variable. The base extract preserves observed cells only.
- A reusable validation helper now lives in `command-files/processing-command-files/afip_p0_validation.py` for standard P0 checks: canonical keys, units, cross-table overlaps and component identities.

P0 assembly command:

```bash
python3 command-files/processing-command-files/44_assemble_ganancias_sociedades_p0_long.py
```

P0 assembly output:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0.csv
```

P0 assembly validation command:

```bash
python3 command-files/processing-command-files/45_validate_ganancias_sociedades_p0_long.py
```

Current P0 assembly validation result:

- 491,435 long rows.
- 20 source tables.
- fiscal years 2014-2022.
- 0 hard failures.
- 0 warnings.

Current P0 progress:

- 20 of 20 `2.3.1.1.*` activity tables implemented.
- Relative progress in the current P0 phase: 100%.
- Current generated and assembled P0 long rows: 491,435.

## Fase 3 Retrospective P0 Probe

The backward P0 phase is complete for publication years 2015-2023 / fiscal
years 2014-2022. Fiscal years 2014-2019 have been moved into the main
`P0_new_xls_detail` extraction.

Commands:

```bash
python3 command-files/processing-command-files/46_build_ganancias_sociedades_p0_backward_inventory.py
python3 command-files/processing-command-files/47_validate_ganancias_sociedades_p0_backward_inventory.py
python3 command-files/processing-command-files/48_probe_ganancias_sociedades_p0_backward_detectors.py
```

Outputs:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_p0_backward_inventory.csv
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_p0_backward_detector_probe.csv
data/output-data/validation_reports/ganancias_sociedades_p0_backward_inventory_validation.md
data/output-data/validation_reports/ganancias_sociedades_p0_backward_detector_probe.md
documentation/afip/warnings_by_period.md
```

Current result:

- Backward inventory: 112 rows.
- Inventory validation: 0 hard failures and 17 structural warnings.
- Detector probe: 112 rows and 0 compatibility warnings after detector updates.
- Fiscal years 2014-2022 have been extracted, assembled and validated.
- Main P0 assembled output now covers fiscal years 2014-2022 with 491,435 long
  rows and 0 assembly-validation failures.

Implementation rule after P6:

- Build the first complete analysis CSV from P0-P6 validated intermediate
  extracts.
- Keep branch/economic-activity harmonization out of this phase. Preserve
  source `activity_code`, `activity_label_original` and
  `activity_section_original`.

## Fase 4 P1 HTML New Classifier

The `P1_new_html_detail` phase is complete for publication year 2014 / fiscal
year 2013.

Commands:

```bash
python3 command-files/processing-command-files/49_build_ganancias_sociedades_p1_inventory.py
python3 command-files/processing-command-files/50_extract_ganancias_sociedades_p1_long.py
python3 command-files/processing-command-files/51_validate_ganancias_sociedades_p1_long.py
```

Outputs:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p1.csv
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p1.csv
data/output-data/validation_reports/ganancias_sociedades_p1_long_validation.md
data/output-data/validation_reports/ganancias_sociedades_p1_long_counts.csv
documentation/afip/warnings_by_period.md
```

Current result:

- P1 inventory: 13 activity tables.
- P1 long extraction: 37,088 rows.
- Canonical variables observed: 127.
- Validation: 0 hard failures and 0 warnings.
- Source format: Excel-exported HTML.
- Detail rule: prefer `_2` sheet/member when available, then cut before
  percentage-structure sections.

P2 was the first backward step with the old activity classifier and is now
complete.

## Fase 5 P2 HTML Old Classifier Millions

The `P2_old_html_detail_millions` phase is complete for publication year 2013 /
fiscal year 2012.

Commands:

```bash
python3 command-files/processing-command-files/52_build_ganancias_sociedades_p2_inventory.py
python3 command-files/processing-command-files/53_extract_ganancias_sociedades_p2_long.py
python3 command-files/processing-command-files/54_validate_ganancias_sociedades_p2_long.py
```

Outputs:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p2.csv
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p2.csv
data/output-data/validation_reports/ganancias_sociedades_p2_long_validation.md
data/output-data/validation_reports/ganancias_sociedades_p2_long_counts.csv
documentation/afip/warnings_by_period.md
```

Current result:

- P2 inventory: 13 activity tables.
- P2 long extraction: 27,208 rows.
- Canonical variables observed: 127.
- Validation: 0 hard failures and 0 warnings.
- Source format: Excel-exported HTML.
- Detail rule: prefer `sheet002.htm`, then cut before percentage-structure
  sections.
- Classifier and unit: `classifier_period = old`, monetary values in millions
  of current pesos.

P3 is now complete.

## Fase 5 P3 HTML Old Classifier Thousands

The `P3_old_html_detail_thousands` phase is complete for publication years
2009-2012 / fiscal years 2008-2011.

Commands:

```bash
python3 command-files/processing-command-files/55_build_ganancias_sociedades_p3_inventory.py
python3 command-files/processing-command-files/56_extract_ganancias_sociedades_p3_long.py
python3 command-files/processing-command-files/57_validate_ganancias_sociedades_p3_long.py
```

Outputs:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p3.csv
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p3.csv
data/output-data/validation_reports/ganancias_sociedades_p3_long_validation.md
data/output-data/validation_reports/ganancias_sociedades_p3_long_counts.csv
documentation/afip/warnings_by_period.md
```

Current result:

- P3 inventory: 49 publication-year/source-table pairs.
- P3 long extraction: 97,775 rows.
- Canonical variables observed: 129.
- Validation: 0 hard failures and 10 structural warnings.
- Source format: Excel-exported HTML.
- Detail rule: prefer `sheet002.htm`; use `sheet001.htm` when no detail sheet
  exists.
- Classifier and unit: `classifier_period = old`, monetary values in thousands
  of current pesos.
- Special handling: fiscal year 2008 has shifted table semantics in part of
  the `2.3.1.1.2.*` block and an `OTROS` cost component.

## Fase 6 P4 CAB/XLS Old Classifier Thousands

The `P4_old_cab_xls_detail_thousands` phase is complete for publication years
2003-2008 / fiscal years 2002-2007.

Commands:

```bash
python3 command-files/processing-command-files/58_build_ganancias_sociedades_p4_inventory.py
python3 command-files/processing-command-files/59_extract_ganancias_sociedades_p4_long.py
python3 command-files/processing-command-files/60_validate_ganancias_sociedades_p4_long.py
```

Outputs:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p4.csv
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p4.csv
data/output-data/validation_reports/ganancias_sociedades_p4_long_validation.md
data/output-data/validation_reports/ganancias_sociedades_p4_long_counts.csv
documentation/afip/warnings_by_period.md
```

Current result:

- P4 inventory: 60 publication-year/source-table pairs.
- P4 long extraction: 132,088 rows.
- Canonical variables observed: 111.
- Validation: 0 hard failures and 25 documented warnings.
- Source format: XLS files embedded in `AFIP.CAB`.
- Detail rule: extract CAB to a temporary directory and prefer `_2.xls`.
- Dependency: local `cabextract` executable.
- Classifier and unit: `classifier_period = old`, monetary values in thousands
  of current pesos.
- Special handling: old numbering maps `2.3.1.1.2.2`, `2.3.1.1.2.3` and
  `2.3.1.1.2.4` to the later result-table semantics; `2.3.1.1.2.1` keeps
  `OTROS` as `costos_otros`.

## Fase 7 P5 CAB/XLS Legacy Numbering

The `P5_old_cab_xls_detail_legacy_numbering` phase is complete for canonical
publication year 2002 / fiscal years 1999-2001.

Commands:

```bash
python3 command-files/processing-command-files/61_build_ganancias_sociedades_p5_inventory.py
python3 command-files/processing-command-files/62_extract_ganancias_sociedades_p5_long.py
python3 command-files/processing-command-files/63_validate_ganancias_sociedades_p5_long.py
```

Outputs:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p5.csv
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p5.csv
data/output-data/validation_reports/ganancias_sociedades_p5_long_validation.md
data/output-data/validation_reports/ganancias_sociedades_p5_long_counts.csv
documentation/afip/warnings_by_period.md
```

Current result:

- P5 inventory: 18 fiscal-year/source-table pairs.
- P5 long extraction: 31,229 rows.
- Canonical variables observed: 114.
- Validation: 0 hard failures and 35 documented warnings.
- Source format: XLS files embedded in `AFIP.CAB`.
- Canonical source rule: use publication year 2002 and map suffixes `_2000`,
  `_2001` and `_2002` to fiscal years 1999, 2000 and 2001.
- Classifier and unit: `classifier_period = old`, monetary values in thousands
  of current pesos.
- Special handling: fiscal years 1999-2000 use a compact four-table schema;
  fiscal year 2001 uses expanded legacy `3.3.*` numbering.

## Fase 8 P6 Direct XLS Legacy Broad/Mixed Activity

The `P6_legacy_broad_activity` phase is complete for publication years
1998-1999 / fiscal years 1997-1998.

Commands:

```bash
python3 command-files/processing-command-files/64_build_ganancias_sociedades_p6_inventory.py
python3 command-files/processing-command-files/65_extract_ganancias_sociedades_p6_long.py
python3 command-files/processing-command-files/66_validate_ganancias_sociedades_p6_long.py
```

Outputs:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p6.csv
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p6.csv
data/output-data/validation_reports/ganancias_sociedades_p6_long_validation.md
data/output-data/validation_reports/ganancias_sociedades_p6_long_counts.csv
documentation/afip/warnings_by_period.md
```

Current result:

- P6 inventory: 8 fiscal-year/source-table pairs.
- P6 long extraction: 3,044 rows.
- Canonical variables observed: 36.
- Validation: 0 hard failures and 24 documented warnings.
- Source format: direct XLS files in installer-style ZIP layouts.
- Classifier and unit: `classifier_period = old`, monetary values in thousands
  of current pesos.
- Special handling: fiscal year 1997 uses `4.4.*` broad-activity tables; fiscal
  year 1998 uses `3.3.*` tables and `_2.xls` continuations with 3-digit detail.

Current final analysis tasks are implemented:

```bash
python3 command-files/processing-command-files/67_assemble_ganancias_sociedades_complete_sin_homologar.py
python3 command-files/processing-command-files/68_homologate_ganancias_sociedades_branches.py
python3 command-files/processing-command-files/69_validate_ganancias_sociedades_analysis_outputs.py
```

Outputs:

```text
data/analysis-data/2026-05-31_afip_ganancias_sociedades_long_sin_homologar.csv
data/analysis-data/2026-05-31_afip_ganancias_sociedades_long_homologada.csv
data/intermediate-data/afip-estadisticas-tributarias/2026-05-31_afip_ganancias_sociedades_ramas_homologacion_diccionario.csv
data/output-data/validation_reports/ganancias_sociedades_analysis_outputs_validation.md
```

The harmonization layer preserves source activity columns and adds common
broad-branch fields for full-series comparability. It does not claim direct
3-digit equivalence between the old and new classifiers.

Current P0 inventory scope:

- `P0_new_xls_detail`
- publication years 2015-2023
- fiscal years 2014-2022
- 892 activity-inventory rows
- no bounds-detection failures observed in the current probe

Concrete probe:

```bash
python3 command-files/processing-command-files/01_probe_ganancias_sociedades_bounds.py
```

Example target:

```text
data/input-data/raw/afip-estadisticas-tributarias/Estadisticas-Tributarias-2023.zip
member ending in /2.3.1.1.1.xls
```

Expected detection:

- zero-based header row: `6`
- spreadsheet header row: `7`
- zero-based data start row: `9`
- spreadsheet data start row: `10`
- first data label: `TOTAL`
