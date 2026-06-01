"""Validate the fifteenth P0 long extract for Ganancias Sociedades."""

from pathlib import Path
import sys


sys.dont_write_bytecode = True

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
PROCESSING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CONFIG_DIR))
sys.path.insert(0, str(PROCESSING_DIR))

from afip_ganancias_sociedades import P0_ACTIVITY_FIXED_ASSETS_TABLE_ID  # noqa: E402
from afip_p0_validation import (  # noqa: E402
    IdentityRule,
    OverlapSpec,
    load_csv,
    validate_p0_long_extract,
    write_detail,
)
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_P0_231151_LONG_PATH,
    GANANCIAS_SOCIEDADES_P0_2311514_LONG_PATH,
    VALIDATION_REPORTS_DIR,
)


REPORT_PATH = (
    VALIDATION_REPORTS_DIR
    / "ganancias_sociedades_p0_2_3_1_1_5_1_4_validation.md"
)
DETAIL_PATH = (
    VALIDATION_REPORTS_DIR
    / "ganancias_sociedades_p0_2_3_1_1_5_1_4_validation_counts.csv"
)

CASE_VARIABLES = {
    "presentaciones_total",
    "activo_bienes_uso_casos",
    "activo_bienes_uso_inmuebles_casos",
    "activo_bienes_uso_rodados_casos",
    "activo_bienes_uso_instalaciones_casos",
    "activo_bienes_uso_otros_casos",
}
MONETARY_VARIABLES = {
    "activo_bienes_uso",
    "activo_bienes_uso_inmuebles",
    "activo_bienes_uso_rodados",
    "activo_bienes_uso_instalaciones",
    "activo_bienes_uso_otros",
}
EXPECTED_VARIABLES = CASE_VARIABLES | MONETARY_VARIABLES


def main() -> None:
    rows = load_csv(GANANCIAS_SOCIEDADES_P0_2311514_LONG_PATH)
    assets_rows = load_csv(GANANCIAS_SOCIEDADES_P0_231151_LONG_PATH)
    VALIDATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_detail(rows, DETAIL_PATH)
    failures, warnings, report = validate_p0_long_extract(
        rows,
        table_id=P0_ACTIVITY_FIXED_ASSETS_TABLE_ID,
        report_title="Ganancias Sociedades P0 2.3.1.1.5.1.4 Long Extract Validation",
        scope="table `2.3.1.1.5.1.4`, `P0_new_xls_detail`, activity dimension.",
        expected_variables=EXPECTED_VARIABLES,
        case_variables=CASE_VARIABLES,
        monetary_variables=MONETARY_VARIABLES,
        overlap_specs=(
            OverlapSpec(
                reference_rows=assets_rows,
                reference_label="2.3.1.1.5.1",
                variables=frozenset({"presentaciones_total", "activo_bienes_uso"}),
                allowed_missing_fiscal_years=frozenset({"2014", "2015", "2016"}),
            ),
        ),
        identity_rules=(
            IdentityRule(
                target="activo_bienes_uso",
                add=(
                    "activo_bienes_uso_inmuebles",
                    "activo_bienes_uso_rodados",
                    "activo_bienes_uso_instalaciones",
                    "activo_bienes_uso_otros",
                ),
                label="fixed-assets identity",
            ),
        ),
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
