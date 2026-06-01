"""Create the required TIER directory structure."""

from pathlib import Path
import sys


sys.dont_write_bytecode = True

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
sys.path.insert(0, str(CONFIG_DIR))

from project_config import PROJECT_ROOT, REQUIRED_DIRECTORIES, ensure_directories  # noqa: E402


def main() -> None:
    ensure_directories()
    for directory in REQUIRED_DIRECTORIES:
        print(directory.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
