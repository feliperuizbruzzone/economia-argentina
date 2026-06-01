"""Validate the eighteenth P0 long extract for Ganancias Sociedades."""

from pathlib import Path
import sys


sys.dont_write_bytecode = True

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
PROCESSING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CONFIG_DIR))
sys.path.insert(0, str(PROCESSING_DIR))

from afip_ganancias_sociedades import P0_ACTIVITY_EQUITY_TABLE_ID  # noqa: E402
from afip_p0_validation import (  # noqa: E402
    IdentityRule,
    OverlapSpec,
    load_csv,
    validate_p0_long_extract,
    write_detail,
)
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_P0_23111_LONG_PATH,
    GANANCIAS_SOCIEDADES_P0_231153_LONG_PATH,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = (
    VALIDATION_REPORTS_DIR
    / "ganancias_sociedades_p0_2_3_1_1_5_3_validation.md"
)
DETAIL_PATH = (
    VALIDATION_REPORTS_DIR
    / "ganancias_sociedades_p0_2_3_1_1_5_3_validation_counts.csv"
)

CASE_VARIABLES = {
    "presentaciones_total",
    "patrimonio_neto_inicio_casos",
    "patrimonio_neto_inicio_positivo_casos",
    "patrimonio_neto_inicio_negativo_casos",
    "patrimonio_neto_aumentos_casos",
    "patrimonio_neto_disminuciones_casos",
    "patrimonio_neto_ajuste_ejercicios_anteriores_positivo_casos",
    "patrimonio_neto_ajuste_ejercicios_anteriores_negativo_casos",
    "resultado_final_ejercicio_contable_beneficio_casos",
    "resultado_final_ejercicio_contable_perdida_casos",
    "patrimonio_neto_cierre_casos",
    "patrimonio_neto_cierre_positivo_casos",
    "patrimonio_neto_cierre_negativo_casos",
}
MONETARY_VARIABLES = {
    "patrimonio_neto_inicio",
    "patrimonio_neto_inicio_positivo",
    "patrimonio_neto_inicio_negativo",
    "patrimonio_neto_aumentos",
    "patrimonio_neto_disminuciones",
    "patrimonio_neto_ajuste_ejercicios_anteriores_positivo",
    "patrimonio_neto_ajuste_ejercicios_anteriores_negativo",
    "resultado_final_ejercicio_contable_beneficio",
    "resultado_final_ejercicio_contable_perdida",
    "patrimonio_neto_cierre",
    "patrimonio_neto_cierre_positivo",
    "patrimonio_neto_cierre_negativo",
}
EXPECTED_VARIABLES = CASE_VARIABLES | MONETARY_VARIABLES
RESULTADO_FINAL_VARIABLES = {
    "resultado_final_ejercicio_contable_beneficio",
    "resultado_final_ejercicio_contable_beneficio_casos",
    "resultado_final_ejercicio_contable_perdida",
    "resultado_final_ejercicio_contable_perdida_casos",
}
EARLY_SPLIT_MISSING_AFTER_2016 = {
    "patrimonio_neto_inicio_positivo",
    "patrimonio_neto_inicio_positivo_casos",
    "patrimonio_neto_inicio_negativo",
    "patrimonio_neto_inicio_negativo_casos",
    "patrimonio_neto_cierre_positivo",
    "patrimonio_neto_cierre_positivo_casos",
    "patrimonio_neto_cierre_negativo",
    "patrimonio_neto_cierre_negativo_casos",
}
EARLY_TOTAL_MISSING_BEFORE_2017 = {
    "patrimonio_neto_inicio",
    "patrimonio_neto_inicio_casos",
    "patrimonio_neto_cierre",
    "patrimonio_neto_cierre_casos",
}
KNOWN_MISSING_BY_FISCAL_YEAR = {
    "2014": RESULTADO_FINAL_VARIABLES
    | EARLY_TOTAL_MISSING_BEFORE_2017
    | {"patrimonio_neto_aumentos_casos", "patrimonio_neto_disminuciones_casos"},
    "2015": RESULTADO_FINAL_VARIABLES
    | EARLY_TOTAL_MISSING_BEFORE_2017
    | {"patrimonio_neto_aumentos_casos", "patrimonio_neto_disminuciones_casos"},
    "2016": RESULTADO_FINAL_VARIABLES
    | EARLY_TOTAL_MISSING_BEFORE_2017
    | {"patrimonio_neto_aumentos_casos", "patrimonio_neto_disminuciones_casos"},
    "2017": RESULTADO_FINAL_VARIABLES | EARLY_SPLIT_MISSING_AFTER_2016,
    "2018": RESULTADO_FINAL_VARIABLES | EARLY_SPLIT_MISSING_AFTER_2016,
    "2019": EARLY_SPLIT_MISSING_AFTER_2016,
    "2020": EARLY_SPLIT_MISSING_AFTER_2016,
    "2021": EARLY_SPLIT_MISSING_AFTER_2016,
    "2022": EARLY_SPLIT_MISSING_AFTER_2016,
}


def main() -> None:
    rows = load_csv(GANANCIAS_SOCIEDADES_P0_231153_LONG_PATH)
    summary_rows = load_csv(GANANCIAS_SOCIEDADES_P0_23111_LONG_PATH)
    VALIDATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_detail(rows, DETAIL_PATH)
    failures, warnings, report = validate_p0_long_extract(
        rows,
        table_id=P0_ACTIVITY_EQUITY_TABLE_ID,
        report_title="Ganancias Sociedades P0 2.3.1.1.5.3 Long Extract Validation",
        scope="table `2.3.1.1.5.3`, `P0_new_xls_detail`, activity dimension.",
        expected_variables=EXPECTED_VARIABLES,
        case_variables=CASE_VARIABLES,
        monetary_variables=MONETARY_VARIABLES,
        overlap_specs=(
            OverlapSpec(
                reference_rows=summary_rows,
                reference_label="2.3.1.1.1",
                variables=frozenset({"presentaciones_total"}),
                allowed_mismatch_keys=frozenset(
                    {("2016", "267;268", "presentaciones_total")}
                ),
            ),
        ),
        identity_rules=(
            IdentityRule(
                target="patrimonio_neto_cierre",
                add=(
                    "patrimonio_neto_inicio",
                    "patrimonio_neto_aumentos",
                    "patrimonio_neto_ajuste_ejercicios_anteriores_positivo",
                    "resultado_final_ejercicio_contable_beneficio",
                ),
                subtract=(
                    "patrimonio_neto_disminuciones",
                    "patrimonio_neto_ajuste_ejercicios_anteriores_negativo",
                    "resultado_final_ejercicio_contable_perdida",
                ),
                label="equity-flow identity",
                allow_missing_fiscal_years=frozenset({"2014", "2015", "2016", "2017", "2018"}),
            ),
        ),
        known_missing_variables_by_year=KNOWN_MISSING_BY_FISCAL_YEAR,
        allow_presentation_only_value_rows=True,
    )
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"report={REPORT_PATH}")
    print(f"detail={DETAIL_PATH}")
    print(f"failures={len(failures)}")
    print(f"warnings={len(warnings)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
