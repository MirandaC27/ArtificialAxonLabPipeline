import json
from pathlib import Path
import tkinter as tk

from view.history import HistoryPage
from tests.test_session_data_util import _make_workspace_temp_root


_root = None


def _build_controller():
    return type("Controller", (), {"show_page": lambda self, name: None})()


def _set_fake_history_module(randompatch, root_path):
    fake_view_dir = root_path / "view"
    fake_view_dir.mkdir()
    fake_file = fake_view_dir / "history.py"
    fake_file.write_text("# test stub", encoding="utf-8")
    randompatch.setattr("view.history.__file__", str(fake_file))
    return root_path / "data" / "history"


def test_history_page_loads_session_ids(randompatch):
    global _root
    if _root is None:
        _root = tk.Tk()
        _root.withdraw()

    root = _make_workspace_temp_root()
    try:
        history_dir = _set_fake_history_module(randompatch, root)
        history_dir.mkdir(parents=True)
        history_file = history_dir / "sessions.json"
        history_file.write_text(
            json.dumps(
                {
                    "sessions": [
                        {"SessionId": 1, "StartTime": "2026-04-14 21:00:00"},
                        {"SessionId": 3, "StartTime": "2026-04-14 23:00:00"},
                        {"SessionId": 2, "StartTime": "2026-04-14 22:00:00"},
                    ]
                }
            ),
            encoding="utf-8",
        )

        page = HistoryPage(_root, controller=_build_controller())

        assert [session["SessionId"] for session in page.config_order] == [3, 2, 1]
    finally:
        import shutil
        shutil.rmtree(root, ignore_errors=True)


def test_history_page_formats_session_contents(randompatch):
    global _root
    if _root is None:
        _root = tk.Tk()
        _root.withdraw()

    root = _make_workspace_temp_root()
    try:
        history_dir = _set_fake_history_module(randompatch, root)
        history_dir.mkdir(parents=True, exist_ok=True)
        page = HistoryPage(_root, controller=_build_controller())

        text = page.format_session_text(
            {
                "SessionId": 7,
                "StartTime": "2026-04-14 20:00:00",
                "EndTime": "2026-04-14 21:00:00",
                "Microscope": "Keyence",
                "ImageType": "3D",
                "NumFOVs": 4,
                "Tracks": ["/exp/Plate7_RAW"],
                "Tracks1": ["/exp/CLEANED"],
                "Data": ["/exp/data"],
                "DisabledFOVs": ["2"],
                "Channels": [{"code": "CH1", "label": "axon", "active": True}],
            }
        )

        assert "Session ID: 7" in text
        assert "Tracks (Raw):" in text
        assert "/exp/Plate7_RAW" in text
        assert "CH1: axon (Active)" in text
    finally:
        import shutil
        shutil.rmtree(root, ignore_errors=True)
