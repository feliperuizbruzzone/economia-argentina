"""Add reproducible economic-branch harmonization columns to Ganancias Sociedades."""

from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path
import re
import sys


sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR.parents[0] / "config"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(CONFIG_DIR))

from afip_ganancias_sociedades import long_fieldnames, normalize_text  # noqa: E402
from project_config import (  # noqa: E402
    GANANCIAS_SOCIEDADES_BRANCH_HARMONIZATION_DICTIONARY_PATH,
    GANANCIAS_SOCIEDADES_DATED_HARMONIZED_PATH,
    GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH,
)


HARMONIZATION_VERSION = "afip_ganancias_sociedades_ramas_v1_2026-05-31"

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

DICTIONARY_FIELDNAMES = [
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

COMMON_BRANCH_LABELS = {
    "TOTAL": "Total",
    "AGRICULTURA_PESCA": "Agricultura, ganaderia, caza, silvicultura y pesca",
    "MINAS_CANTERAS": "Explotacion de minas y canteras",
    "INDUSTRIA_MANUFACTURERA": "Industria manufacturera",
    "ELECTRICIDAD_GAS_AGUA": "Electricidad, gas, agua y saneamiento",
    "CONSTRUCCION": "Construccion",
    "COMERCIO_HOTELES_RESTAURANTES": "Comercio, hoteles y restaurantes",
    "TRANSPORTE_COMUNICACIONES": "Transporte, almacenamiento y comunicaciones",
    "FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES": (
        "Finanzas, seguros, inmuebles y servicios empresariales"
    ),
    "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS": (
        "Administracion publica, ensenanza, salud y otros servicios"
    ),
    "OTRAS_NO_ESPECIFICADAS": "Otras actividades o actividades no especificadas",
    "NO_HOMOLOGADO": "No homologado",
}

NEW_SECTION_TO_COMMON = {
    "A": "AGRICULTURA_PESCA",
    "B": "MINAS_CANTERAS",
    "C": "INDUSTRIA_MANUFACTURERA",
    "D": "ELECTRICIDAD_GAS_AGUA",
    "E": "ELECTRICIDAD_GAS_AGUA",
    "F": "CONSTRUCCION",
    "G": "COMERCIO_HOTELES_RESTAURANTES",
    "H": "TRANSPORTE_COMUNICACIONES",
    "I": "COMERCIO_HOTELES_RESTAURANTES",
    "J": "TRANSPORTE_COMUNICACIONES",
    "K": "FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES",
    "L": "FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES",
    "M": "FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES",
    "N": "FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES",
    "O": "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS",
    "P": "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS",
    "Q": "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS",
    "R": "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS",
    "S": "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS",
}

OLD_SECTION_TO_COMMON = {
    "A": "AGRICULTURA_PESCA",
    "B": "AGRICULTURA_PESCA",
    "C": "MINAS_CANTERAS",
    "D": "INDUSTRIA_MANUFACTURERA",
    "E": "ELECTRICIDAD_GAS_AGUA",
    "F": "CONSTRUCCION",
    "G": "COMERCIO_HOTELES_RESTAURANTES",
    "H": "COMERCIO_HOTELES_RESTAURANTES",
    "I": "TRANSPORTE_COMUNICACIONES",
    "J": "FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES",
    "K": "FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES",
    "L": "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS",
    "M": "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS",
    "N": "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS",
    "O": "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS",
}

P6_BROAD_CODE_TO_COMMON = {
    "AGRICULTURA_CAZA_SILVICULTURA_PESCA": "AGRICULTURA_PESCA",
    "EXPLOTACION_MINAS_CANTERAS": "MINAS_CANTERAS",
    "INDUSTRIAS_MANUFACTURERAS": "INDUSTRIA_MANUFACTURERA",
    "ELECTRICIDAD_GAS_AGUA": "ELECTRICIDAD_GAS_AGUA",
    "CONSTRUCCION": "CONSTRUCCION",
    "COMERCIO_RESTAURANTES_HOTELES": "COMERCIO_HOTELES_RESTAURANTES",
    "TRANSPORTE_ALMACENAMIENTO_COMUNICACIONES": "TRANSPORTE_COMUNICACIONES",
    "FINANZAS_SEGUROS_INMUEBLES_SERVICIOS": (
        "FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES"
    ),
    "SERVICIOS_COMUNALES_SOCIALES_PERSONALES": (
        "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS"
    ),
}

P6_SECTION_LABEL_TO_COMMON = {
    "AGRICULTURA, CAZA, SILVICULTURA Y PESCA": "AGRICULTURA_PESCA",
    "EXPLOTACION DE MINAS Y CANTERAS": "MINAS_CANTERAS",
    "INDUSTRIAS MANUFACTURERAS": "INDUSTRIA_MANUFACTURERA",
    "ELECTRICIDAD, GAS Y AGUA": "ELECTRICIDAD_GAS_AGUA",
    "CONSTRUCCION": "CONSTRUCCION",
    "COMERCIO AL POR MAYOR Y AL POR MENOR Y RESTAURANTES Y HOTELES": (
        "COMERCIO_HOTELES_RESTAURANTES"
    ),
    "TRANSPORTES, ALMACENAMIENTO Y COMUNICACIONES": "TRANSPORTE_COMUNICACIONES",
    "ESTABLECIMIENTOS FINANCIEROS, SEGUROS, ETC.": (
        "FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES"
    ),
    "ESTABLECIMIENTOS FINANCIEROS, SEGUROS, BIENES INMUEBLES Y SERVICIOS TECNICOS Y PROFESIONALES (EXCEPTO LOS SOCIALES Y COMUNALES) Y ALQUILER Y ARRENDAMIENTO DE MAQUINARIA Y EQUIPO": (
        "FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES"
    ),
    "SERVICIOS COMUNALES, SOCIALES Y PERSONALES": (
        "SERVICIOS_SOCIALES_PERSONALES_PUBLICOS"
    ),
}

SECTION_PATTERN = re.compile(r"^\s*([A-Z])\s*(?:-|$)")


def _slug_code(value: str) -> str:
    text = normalize_text(value)
    text = re.sub(r"[^A-Z0-9]+", "_", text).strip("_")
    return text.lower() or "sin_codigo"


def _section_letter(row: dict[str, str]) -> str:
    code = normalize_text(row["activity_code"])
    if len(code) == 1 and code.isalpha():
        return code
    match = SECTION_PATTERN.match(normalize_text(row["activity_section_original"]))
    if match:
        return match.group(1)
    match = SECTION_PATTERN.match(normalize_text(row["activity_label_original"]))
    if match:
        return match.group(1)
    return ""


def _is_total(row: dict[str, str]) -> bool:
    return row["activity_level"] == "total" or normalize_text(row["activity_code"]) == "TOTAL"


def _is_other_activity(row: dict[str, str]) -> bool:
    label = normalize_text(row["activity_label_original"])
    code = normalize_text(row["activity_code"])
    if row["activity_level"] == "other_activity":
        return True
    return (
        code in {"000", "OTRAS_ACTIVIDADES", "ACTIVIDADES_NO_BIEN_ESPECIFICADAS"}
        or "OTRAS ACTIVIDADES" in label
        or "NO BIEN ESPECIFIC" in label
        or "NO CLASIFIC" in label
    )


def _common_from_source_classifier(row: dict[str, str]) -> str:
    classifier_period = row["classifier_period"]
    section = _section_letter(row)
    if classifier_period == "new" and section:
        return NEW_SECTION_TO_COMMON.get(section, "")
    if classifier_period == "old" and section:
        return OLD_SECTION_TO_COMMON.get(section, "")
    code = normalize_text(row["activity_code"])
    if code in P6_BROAD_CODE_TO_COMMON:
        return P6_BROAD_CODE_TO_COMMON[code]
    section_label = normalize_text(row["activity_section_original"])
    if section_label in P6_SECTION_LABEL_TO_COMMON:
        return P6_SECTION_LABEL_TO_COMMON[section_label]
    label = normalize_text(row["activity_label_original"])
    return P6_SECTION_LABEL_TO_COMMON.get(label, "")


def _common_branch(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    if _is_total(row):
        code = "TOTAL"
        return code, COMMON_BRANCH_LABELS[code], "total", "source_total", "source total"
    if _is_other_activity(row):
        code = "OTRAS_NO_ESPECIFICADAS"
        return (
            code,
            COMMON_BRANCH_LABELS[code],
            "broad_full_series_residual",
            "source_other",
            "source residual or not-specified activity",
        )

    code = _common_from_source_classifier(row)
    if code:
        return (
            code,
            COMMON_BRANCH_LABELS[code],
            "broad_full_series",
            "mapped",
            "mapped from source classifier section or broad activity",
        )

    code = "NO_HOMOLOGADO"
    return code, COMMON_BRANCH_LABELS[code], "unmapped", "unmapped", "no mapping rule matched"


def _detail_branch(row: dict[str, str]) -> tuple[str, str, str]:
    level = row["activity_level"]
    classifier_period = row["classifier_period"] or "unknown"
    label = row["activity_label_original"]
    activity_code = row["activity_code"]
    slug = _slug_code(activity_code)

    if _is_total(row):
        return "source_total", "Total", "total"
    if _is_other_activity(row):
        return (
            f"{classifier_period}_other_{slug}",
            label or "Otras actividades",
            "other_activity",
        )
    if level == "activity_3digit":
        return (
            f"{classifier_period}_3d_{slug}",
            label,
            "activity_3digit_source_classifier",
        )
    if level == "section":
        section = _section_letter(row) or slug
        return (
            f"{classifier_period}_section_{section.lower()}",
            label,
            "section_source_classifier",
        )
    if level == "broad_activity":
        return (
            f"{classifier_period}_broad_{slug}",
            label,
            "broad_activity_source",
        )
    return (
        f"{classifier_period}_{level}_{slug}",
        label,
        level or "unknown_source_level",
    )


def _homologate_row(row: dict[str, str]) -> dict[str, str]:
    common_code, common_label, common_level, status, note = _common_branch(row)
    detail_code, detail_label, detail_level = _detail_branch(row)
    return {
        "rama_homologacion_version": HARMONIZATION_VERSION,
        "rama_homologacion_estado": status,
        "rama_comun_codigo": common_code,
        "rama_comun_label": common_label,
        "rama_comun_nivel": common_level,
        "rama_detalle_homologada_codigo": detail_code,
        "rama_detalle_homologada_label": detail_label,
        "rama_detalle_homologada_nivel": detail_level,
        "rama_homologacion_nota": note,
    }


def _dictionary_key(row: dict[str, str], harmonized: dict[str, str]) -> tuple[str, ...]:
    return (
        row["classifier_period"],
        row["activity_level"],
        row["activity_code"],
        row["activity_label_original"],
        row["activity_section_original"],
        harmonized["rama_comun_codigo"],
        harmonized["rama_detalle_homologada_codigo"],
    )


def main() -> None:
    """Create a dated harmonized CSV and a source-to-branch dictionary."""

    source_fieldnames = long_fieldnames()
    output_fieldnames = source_fieldnames + HARMONIZATION_FIELDNAMES
    status_counts: Counter[str] = Counter()
    common_counts: Counter[str] = Counter()
    dictionary: dict[tuple[str, ...], dict[str, str | int | set[str]]] = {}
    total_rows = 0

    GANANCIAS_SOCIEDADES_DATED_HARMONIZED_PATH.parent.mkdir(parents=True, exist_ok=True)
    GANANCIAS_SOCIEDADES_BRANCH_HARMONIZATION_DICTIONARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH.open(encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        if reader.fieldnames != source_fieldnames:
            raise ValueError(
                f"Unexpected fieldnames in {GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH}"
            )
        with GANANCIAS_SOCIEDADES_DATED_HARMONIZED_PATH.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as output_file:
            writer = csv.DictWriter(output_file, fieldnames=output_fieldnames)
            writer.writeheader()
            for row in reader:
                harmonized = _homologate_row(row)
                writer.writerow({**row, **harmonized})
                total_rows += 1
                status_counts[harmonized["rama_homologacion_estado"]] += 1
                common_counts[harmonized["rama_comun_codigo"]] += 1

                key = _dictionary_key(row, harmonized)
                if key not in dictionary:
                    dictionary[key] = {
                        "classifier_period": row["classifier_period"],
                        "activity_level": row["activity_level"],
                        "activity_code": row["activity_code"],
                        "activity_label_original": row["activity_label_original"],
                        "activity_section_original": row["activity_section_original"],
                        **harmonized,
                        "years": set(),
                        "row_count": 0,
                    }
                dictionary[key]["years"].add(row["fiscal_year"])  # type: ignore[union-attr]
                dictionary[key]["row_count"] += 1  # type: ignore[operator]

    with GANANCIAS_SOCIEDADES_BRANCH_HARMONIZATION_DICTIONARY_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as output_file:
        writer = csv.DictWriter(output_file, fieldnames=DICTIONARY_FIELDNAMES)
        writer.writeheader()
        for row in sorted(
            dictionary.values(),
            key=lambda item: (
                str(item["classifier_period"]),
                str(item["activity_level"]),
                str(item["activity_code"]),
                str(item["activity_label_original"]),
            ),
        ):
            years = sorted(row.pop("years"))  # type: ignore[arg-type]
            writer.writerow(
                {
                    **row,
                    "fiscal_year_min": years[0],
                    "fiscal_year_max": years[-1],
                }
            )

    print(f"wrote={GANANCIAS_SOCIEDADES_DATED_HARMONIZED_PATH}")
    print(f"rows={total_rows}")
    print(f"dictionary={GANANCIAS_SOCIEDADES_BRANCH_HARMONIZATION_DICTIONARY_PATH}")
    print(f"dictionary_rows={len(dictionary)}")
    print(f"status_counts={dict(sorted(status_counts.items()))}")
    print(f"common_branch_counts={dict(sorted(common_counts.items()))}")


if __name__ == "__main__":
    main()
