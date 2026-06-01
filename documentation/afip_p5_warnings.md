# AFIP Ganancias Sociedades P5 Warnings

Scope: `P5_old_cab_xls_detail_legacy_numbering`.

Coverage:

- Publication year: 2002.
- Fiscal years: 1999-2001.
- Source archive: `estadisticasTributarias2002.zip`.
- Source container: `AFIP.CAB`.
- Source files: XLS members with legacy `3.3.*` numbering.
- Output: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p5.csv`.

Validation result:

- Inventory rows: 18 fiscal/table pairs.
- Long rows: 31,229.
- Variables observed: 114.
- Validation failures: 0.
- Validation warnings: 35.
- Validation report: `data/output-data/validation_reports/ganancias_sociedades_p5_long_validation.md`.

## Canonical Source Rule

Publication year 2002 is the canonical source for fiscal years 1999-2001.
The 2002 CAB includes suffixed XLS members:

- `_2000`: fiscal year 1999.
- `_2001`: fiscal year 2000.
- `_2002`: fiscal year 2001.

Older publication packages for 2000 and 2001 contain overlapping material.
They are treated as superseded duplicate releases for this phase. The pipeline
does not merge them with publication 2002.

## Structural Warnings

Fiscal years 1999-2000 use a compact four-table schema:

- `3.3.1.1.1`: presentations, sales, taxable net income and assessed tax.
- `3.3.1.1.2`: combined result table, mapped to sales, costs, gross result and accounting result variables.
- `3.3.1.1.3`: tax result table, with old `quebranto` labels mapped to tax-result loss variables.
- `3.3.1.1.4`: aggregate balance sheet, without asset/liability/equity components.

Fiscal year 2001 uses expanded legacy numbering:

- `3.3.1.1.1`
- `3.3.1.1.2.1`
- `3.3.1.1.2.2`
- `3.3.1.1.2.3`
- `3.3.1.1.2.4`
- `3.3.1.1.3`
- `3.3.1.1.4`
- `3.3.1.1.5.1`
- `3.3.1.1.5.2`
- `3.3.1.1.5.3`

Fiscal year 2001 therefore has more detailed patrimonial and result-table
coverage than fiscal years 1999-2000.

## Variable Comparability Notes

- `presentaciones_con_ganancia_neta_imponible` appears in the 1999-2000 summary table where later periods use `presentaciones_con_impuesto_determinado`.
- `presentaciones_con_impuesto_determinado` is available for fiscal year 2001 but not for 1999-2000 in the same summary definition.
- `resultado_final_del_ejercicio` in the old result table is mapped to canonical accounting-result variables.
- `quebranto` in the old tax-result table is mapped to canonical tax-result loss variables.
- `costos_otros` is observed in fiscal year 2001 and should not be forced backward to 1999-2000.
- Components of assets, liabilities and equity are available in fiscal year 2001, but not in the aggregate 1999-2000 balance-sheet table.

## Activity Labels

Most extracted rows are section, total, or 3-digit activity rows.
The legacy label `Actividades no bien especificadas 9/` is classified as
`other_activity` with code `ACTIVIDADES_NO_BIEN_ESPECIFICADAS_9`, not as a
3-digit branch.

Homologation of economic branches remains pending for a later phase. This
phase preserves original labels and source table identifiers.
