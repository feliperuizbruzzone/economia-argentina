"""Central project configuration for the TIER workflow."""

from pathlib import Path


# DECISION: Resolve all paths from this file so scripts avoid absolute local paths.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

COMMAND_FILES_DIR = PROJECT_ROOT / "command-files"
DATA_DIR = PROJECT_ROOT / "data"
DOCUMENTATION_DIR = PROJECT_ROOT / "documentation"
TESTS_DIR = PROJECT_ROOT / "tests"

INPUT_DATA_DIR = DATA_DIR / "input-data"
RAW_INPUT_DATA_DIR = INPUT_DATA_DIR / "raw"
INTERMEDIATE_DATA_DIR = DATA_DIR / "intermediate-data"
AFIP_INTERMEDIATE_DATA_DIR = INTERMEDIATE_DATA_DIR / "afip-estadisticas-tributarias"
ANALYSIS_DATA_DIR = DATA_DIR / "analysis-data"
OUTPUT_DATA_DIR = DATA_DIR / "output-data"
VALIDATION_REPORTS_DIR = OUTPUT_DATA_DIR / "validation_reports"

SOURCE_INSTITUTION = "AFIP"
SOURCE_PAGE_URL = (
    "https://www.afip.gob.ar/institucional/estudios/"
    "anuario-estadisticas-tributarias/"
)
SOURCE_YEARS = tuple(range(1998, 2024))
RAW_ARCHIVE_DIR = RAW_INPUT_DATA_DIR / "afip-estadisticas-tributarias"

GANANCIAS_SOCIEDADES_INVENTORY_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_inventory.csv"
)
GANANCIAS_SOCIEDADES_P0_23111_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_1.csv"
)
GANANCIAS_SOCIEDADES_P0_231121_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_2_1.csv"
)
GANANCIAS_SOCIEDADES_P0_231122_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_2_2.csv"
)
GANANCIAS_SOCIEDADES_P0_231123_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_2_3.csv"
)
GANANCIAS_SOCIEDADES_P0_231124_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_2_4.csv"
)
GANANCIAS_SOCIEDADES_P0_231125_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_2_5.csv"
)
GANANCIAS_SOCIEDADES_P0_231126_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_2_6.csv"
)
GANANCIAS_SOCIEDADES_P0_231127_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_2_7.csv"
)
GANANCIAS_SOCIEDADES_P0_23113_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_3.csv"
)
GANANCIAS_SOCIEDADES_P0_23114_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_4.csv"
)
GANANCIAS_SOCIEDADES_P0_231151_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_5_1.csv"
)
GANANCIAS_SOCIEDADES_P0_2311511_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_5_1_1.csv"
)
GANANCIAS_SOCIEDADES_P0_2311512_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_5_1_2.csv"
)
GANANCIAS_SOCIEDADES_P0_2311513_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_5_1_3.csv"
)
GANANCIAS_SOCIEDADES_P0_2311514_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_5_1_4.csv"
)
GANANCIAS_SOCIEDADES_P0_231152_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_5_2.csv"
)
GANANCIAS_SOCIEDADES_P0_2311521_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_5_2_1.csv"
)
GANANCIAS_SOCIEDADES_P0_231153_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_5_3.csv"
)
GANANCIAS_SOCIEDADES_P0_2311531_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_5_3_1.csv"
)
GANANCIAS_SOCIEDADES_P0_2311532_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0_2_3_1_1_5_3_2.csv"
)
GANANCIAS_SOCIEDADES_P0_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p0.csv"
)
GANANCIAS_SOCIEDADES_P1_INVENTORY_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_inventory_p1.csv"
)
GANANCIAS_SOCIEDADES_P1_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p1.csv"
)
GANANCIAS_SOCIEDADES_P2_INVENTORY_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_inventory_p2.csv"
)
GANANCIAS_SOCIEDADES_P2_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p2.csv"
)
GANANCIAS_SOCIEDADES_P3_INVENTORY_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_inventory_p3.csv"
)
GANANCIAS_SOCIEDADES_P3_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p3.csv"
)
GANANCIAS_SOCIEDADES_P4_INVENTORY_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_inventory_p4.csv"
)
GANANCIAS_SOCIEDADES_P4_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p4.csv"
)
GANANCIAS_SOCIEDADES_P5_INVENTORY_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_inventory_p5.csv"
)
GANANCIAS_SOCIEDADES_P5_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p5.csv"
)
GANANCIAS_SOCIEDADES_P6_INVENTORY_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_inventory_p6.csv"
)
GANANCIAS_SOCIEDADES_P6_LONG_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_long_p6.csv"
)
GANANCIAS_SOCIEDADES_P0_BACKWARD_INVENTORY_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_p0_backward_inventory.csv"
)
GANANCIAS_SOCIEDADES_P0_BACKWARD_DETECTOR_PROBE_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR / "afip_ganancias_sociedades_p0_backward_detector_probe.csv"
)
ANALYSIS_CREATION_DATE = "2026-05-31"
# Legacy full CSV paths kept only so validators can flag stale local artifacts.
GANANCIAS_SOCIEDADES_DATED_UNHARMONIZED_PATH = (
    ANALYSIS_DATA_DIR
    / f"{ANALYSIS_CREATION_DATE}_afip_ganancias_sociedades_long_sin_homologar.csv"
)
GANANCIAS_SOCIEDADES_DATED_HARMONIZED_PATH = (
    ANALYSIS_DATA_DIR
    / f"{ANALYSIS_CREATION_DATE}_afip_ganancias_sociedades_long_homologada.csv"
)
GANANCIAS_SOCIEDADES_TIDY_HARMONIZED_PATH = (
    ANALYSIS_DATA_DIR
    / f"{ANALYSIS_CREATION_DATE}_afip_ganancias_sociedades_tidy_homologado.csv.gz"
)
GANANCIAS_SOCIEDADES_FINAL_PATH = GANANCIAS_SOCIEDADES_TIDY_HARMONIZED_PATH
FINAL_ANALYSIS_DATA_PATH = GANANCIAS_SOCIEDADES_FINAL_PATH
GANANCIAS_SOCIEDADES_BRANCH_HARMONIZATION_DICTIONARY_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR
    / f"{ANALYSIS_CREATION_DATE}_afip_ganancias_sociedades_ramas_homologacion_diccionario.csv"
)
GANANCIAS_SOCIEDADES_SOURCE_DICTIONARY_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR
    / f"{ANALYSIS_CREATION_DATE}_afip_ganancias_sociedades_source_dictionary.csv"
)
GANANCIAS_SOCIEDADES_ACTIVITY_DICTIONARY_PATH = (
    AFIP_INTERMEDIATE_DATA_DIR
    / f"{ANALYSIS_CREATION_DATE}_afip_ganancias_sociedades_activity_dictionary.csv"
)

REQUIRED_DIRECTORIES = (
    COMMAND_FILES_DIR / "config",
    COMMAND_FILES_DIR / "processing-command-files",
    COMMAND_FILES_DIR / "analysis-command-files",
    RAW_INPUT_DATA_DIR,
    RAW_ARCHIVE_DIR,
    INTERMEDIATE_DATA_DIR,
    AFIP_INTERMEDIATE_DATA_DIR,
    ANALYSIS_DATA_DIR,
    OUTPUT_DATA_DIR,
    VALIDATION_REPORTS_DIR,
    DOCUMENTATION_DIR,
    TESTS_DIR,
)


def project_path(*parts: str) -> Path:
    """Return a path relative to the repository root."""
    return PROJECT_ROOT.joinpath(*parts)


def ensure_directories() -> None:
    """Create required TIER directories if they are missing."""
    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)
