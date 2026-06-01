# AFIP Ganancias Sociedades P6 Warnings

Scope: `P6_legacy_broad_activity`.

Coverage:

- Publication years: 1998-1999.
- Fiscal years: 1997-1998.
- Source archives: `estadisticasTributarias1998.zip` and `estadisticasTributarias1999.zip`.
- Source format: direct XLS files in installer-style ZIP layouts.
- Output: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p6.csv`.

Validation result:

- Inventory rows: 8 fiscal/table pairs.
- Long rows: 3,044.
- Variables observed: 36.
- Validation failures: 0.
- Validation warnings: 24.
- Validation report: `data/output-data/validation_reports/ganancias_sociedades_p6_long_validation.md`.

## Structural Warnings

Fiscal year 1997 uses legacy `4.4.*` numbering and only broad activity rows in
the four total-universe tables:

- `4.4.1.1.1`: presentations, sales, taxable net income and assessed tax.
- `4.4.1.1.2`: combined result table.
- `4.4.1.1.3`: tax-adjustment and tax-result table.
- `4.4.1.1.4`: aggregate balance sheet.

Fiscal year 1998 uses legacy `3.3.*` numbering and has `_2.xls` continuation
files with 3-digit activity detail:

- `3.3.1.1.1_2`
- `3.3.1.1.2_2`
- `3.3.1.1.3_2`
- `3.3.1.1.4_2`

This corrects the initial working assumption that all P6 years were broad-only:
fiscal year 1997 is broad-only, but fiscal year 1998 preserves 3-digit detail.

## Variable Comparability Notes

- P6 uses the old count `presentaciones_con_ganancia_neta_imponible`; it should not be merged automatically with `presentaciones_con_impuesto_determinado`.
- Fiscal year 1997 table `4.4.1.1.3` contains tax-adjustment variables that are not present in fiscal year 1998 table `3.3.1.1.3`.
- The old `resultado final del ejercicio` label is mapped to canonical accounting-result variables.
- The old `quebranto` label is mapped to canonical tax-result loss variables.
- Balance-sheet tables are aggregate only; no asset, liability or equity components are available in P6.

## Activity Labels

- Fiscal year 1997 rows are classified as `total`, `broad_activity` or `other_activity`.
- Fiscal year 1998 rows include `activity_3digit`, `broad_activity`, `other_activity` and `total`.
- Broad activity labels are preserved as original text and mapped to stable broad codes only for row identity; no sector harmonization is performed.

Homologation of economic branches remains pending for a later phase.
