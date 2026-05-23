from pathlib import Path
import sys


def is_frozen():
    return getattr(sys, "frozen", False)


def resource_root():
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))

    return Path(__file__).resolve().parent.parent


def app_root():
    if is_frozen():
        return Path(sys.executable).resolve().parent

    return resource_root()


def data_dir():
    path = app_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def results_dir():
    path = app_root() / "results"
    path.mkdir(parents=True, exist_ok=True)
    return path


def csv_dir():
    path = results_dir() / "csv_files"
    path.mkdir(parents=True, exist_ok=True)
    return path


def analysis_dir():
    return resource_root() / "analysis"


def controller_dir():
    return resource_root() / "controller"


def script_path(script_name):
    return analysis_dir() / script_name
