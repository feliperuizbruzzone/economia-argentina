"""Run the current reproducible workflow."""

from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PIPELINE = (
    PROJECT_ROOT / "command-files" / "processing-command-files" / "00_prepare_directories.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "02_build_ganancias_sociedades_inventory.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "03_validate_ganancias_sociedades_p0_activity_inventory.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "04_extract_ganancias_sociedades_p0_2_3_1_1_1.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "05_validate_ganancias_sociedades_p0_2_3_1_1_1.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "06_extract_ganancias_sociedades_p0_2_3_1_1_2_1.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "07_validate_ganancias_sociedades_p0_2_3_1_1_2_1.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "08_extract_ganancias_sociedades_p0_2_3_1_1_2_2.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "09_validate_ganancias_sociedades_p0_2_3_1_1_2_2.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "10_extract_ganancias_sociedades_p0_2_3_1_1_2_3.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "11_validate_ganancias_sociedades_p0_2_3_1_1_2_3.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "12_extract_ganancias_sociedades_p0_2_3_1_1_2_4.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "13_validate_ganancias_sociedades_p0_2_3_1_1_2_4.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "14_extract_ganancias_sociedades_p0_2_3_1_1_2_5.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "15_validate_ganancias_sociedades_p0_2_3_1_1_2_5.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "16_extract_ganancias_sociedades_p0_2_3_1_1_2_6.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "17_validate_ganancias_sociedades_p0_2_3_1_1_2_6.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "18_extract_ganancias_sociedades_p0_2_3_1_1_2_7.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "19_validate_ganancias_sociedades_p0_2_3_1_1_2_7.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "20_extract_ganancias_sociedades_p0_2_3_1_1_3.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "21_validate_ganancias_sociedades_p0_2_3_1_1_3.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "22_extract_ganancias_sociedades_p0_2_3_1_1_4.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "23_validate_ganancias_sociedades_p0_2_3_1_1_4.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "24_extract_ganancias_sociedades_p0_2_3_1_1_5_1.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "25_validate_ganancias_sociedades_p0_2_3_1_1_5_1.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "26_extract_ganancias_sociedades_p0_2_3_1_1_5_1_1.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "27_validate_ganancias_sociedades_p0_2_3_1_1_5_1_1.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "28_extract_ganancias_sociedades_p0_2_3_1_1_5_1_2.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "29_validate_ganancias_sociedades_p0_2_3_1_1_5_1_2.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "30_extract_ganancias_sociedades_p0_2_3_1_1_5_1_3.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "31_validate_ganancias_sociedades_p0_2_3_1_1_5_1_3.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "32_extract_ganancias_sociedades_p0_2_3_1_1_5_1_4.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "33_validate_ganancias_sociedades_p0_2_3_1_1_5_1_4.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "34_extract_ganancias_sociedades_p0_2_3_1_1_5_2.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "35_validate_ganancias_sociedades_p0_2_3_1_1_5_2.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "36_extract_ganancias_sociedades_p0_2_3_1_1_5_2_1.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "37_validate_ganancias_sociedades_p0_2_3_1_1_5_2_1.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "38_extract_ganancias_sociedades_p0_2_3_1_1_5_3.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "39_validate_ganancias_sociedades_p0_2_3_1_1_5_3.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "40_extract_ganancias_sociedades_p0_2_3_1_1_5_3_1.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "41_validate_ganancias_sociedades_p0_2_3_1_1_5_3_1.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "42_extract_ganancias_sociedades_p0_2_3_1_1_5_3_2.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "43_validate_ganancias_sociedades_p0_2_3_1_1_5_3_2.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "44_assemble_ganancias_sociedades_p0_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "45_validate_ganancias_sociedades_p0_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "46_build_ganancias_sociedades_p0_backward_inventory.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "47_validate_ganancias_sociedades_p0_backward_inventory.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "48_probe_ganancias_sociedades_p0_backward_detectors.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "49_build_ganancias_sociedades_p1_inventory.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "50_extract_ganancias_sociedades_p1_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "51_validate_ganancias_sociedades_p1_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "52_build_ganancias_sociedades_p2_inventory.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "53_extract_ganancias_sociedades_p2_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "54_validate_ganancias_sociedades_p2_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "55_build_ganancias_sociedades_p3_inventory.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "56_extract_ganancias_sociedades_p3_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "57_validate_ganancias_sociedades_p3_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "58_build_ganancias_sociedades_p4_inventory.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "59_extract_ganancias_sociedades_p4_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "60_validate_ganancias_sociedades_p4_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "61_build_ganancias_sociedades_p5_inventory.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "62_extract_ganancias_sociedades_p5_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "63_validate_ganancias_sociedades_p5_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "64_build_ganancias_sociedades_p6_inventory.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "65_extract_ganancias_sociedades_p6_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "66_validate_ganancias_sociedades_p6_long.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "67_assemble_ganancias_sociedades_complete_sin_homologar.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "68_homologate_ganancias_sociedades_branches.py",
    PROJECT_ROOT / "command-files" / "processing-command-files" / "69_validate_ganancias_sociedades_analysis_outputs.py",
)


def main() -> None:
    for script in PIPELINE:
        print(f"Running {script.relative_to(PROJECT_ROOT)}", flush=True)
        subprocess.run([sys.executable, str(script)], cwd=PROJECT_ROOT, check=True)


if __name__ == "__main__":
    main()
