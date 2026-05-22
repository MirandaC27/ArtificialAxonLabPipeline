from pathlib import Path
import sys


def resource_root():
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


def data_dir():
    return resource_root() / "data"


def results_dir():
    return resource_root() / "results"


def csv_dir():
    return results_dir() / "csv_files"
