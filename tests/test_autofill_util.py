from types import SimpleNamespace
from unittest.mock import MagicMock

from ArtificialAxonLabPipeline.Backend.controller.AutoFillUtil import AutoFillUtil


class _Node:
    def __init__(self, master=None):
        self.master = master


def test_find_app_root_walks_up_master_chain():
    util = AutoFillUtil()
    root = _Node()
    child = _Node(master=root)
    grandchild = _Node(master=child)

    assert util._find_app_root(grandchild) is root


def test_parse_config_data_merges_unique_folders_and_sorts_channels():
    util = AutoFillUtil()

    parsed = util.parse_config_data(
        {
            "ImageType": "2D",
            "Microscope": "Olympus",
            "selected_folders": ["/exp/raw", "/exp/raw"],
            "Tracks": ["/exp/raw"],
            "Data": ["/exp/data"],
            "Tracks1": ["/exp/CLEANED"],
            "Channels": [
                {"code": "CH3", "label": "debris"},
                {"num": 1, "label": "axon"},
                {"code": "bad", "label": "ignored"},
                {"code": "CH2", "label": ""},
            ],
        }
    )

    assert parsed == {
        "image_type": "2D",
        "microscope": "Olympus",
        "folders": ["/exp/raw", "/exp/data", "/exp/CLEANED"],
        "channels": [
            {"num": 1, "label": "axon"},
            {"num": 3, "label": "debris"},
        ],
    }


def test_parse_config_data_uses_lowercase_fallback_keys():
    util = AutoFillUtil()

    parsed = util.parse_config_data(
        {
            "image_type": "3D",
            "microscope": "Keyence",
        }
    )

    assert parsed["image_type"] == "3D"
    assert parsed["microscope"] == "Keyence"
    assert parsed["folders"] == []
    assert parsed["channels"] == []


def test_autofill_and_navigate_warns_when_no_config_selected(monkeypatch):
    util = AutoFillUtil()
    warn = MagicMock()
    monkeypatch.setattr("controller.AutoFillUtil.messagebox.showwarning", warn)

    util.autofill_and_navigate(_Node())

    warn.assert_called_once_with("Warning", "Select a config first")


def test_autofill_and_navigate_shows_error_when_config_read_fails(monkeypatch):
    util = AutoFillUtil()
    util.set_selected_config(SimpleNamespace(read_text=MagicMock(side_effect=OSError("boom"))))
    error = MagicMock()
    monkeypatch.setattr("controller.AutoFillUtil.messagebox.showerror", error)

    util.autofill_and_navigate(_Node())

    error.assert_called_once()
    assert "Failed to read config" in error.call_args.args[1]


def test_autofill_and_navigate_navigates_and_applies_config(monkeypatch):
    util = AutoFillUtil()
    config_path = SimpleNamespace(
        read_text=lambda: '{"ImageType":"2D","Microscope":"Keyence","Tracks":["/raw"],"Channels":[{"code":"CH2","label":"myelin"}]}'
    )
    util.set_selected_config(config_path)

    upload_page = MagicMock()
    app_root = SimpleNamespace(show_page=MagicMock(), pages={"Upload": upload_page})
    root = _Node(master=_Node(master=app_root))

    info = MagicMock()
    error = MagicMock()
    monkeypatch.setattr("controller.AutoFillUtil.messagebox.showinfo", info)
    monkeypatch.setattr("controller.AutoFillUtil.messagebox.showerror", error)

    util.autofill_and_navigate(root)

    app_root.show_page.assert_called_once_with("Upload")
    upload_page.apply_config_data.assert_called_once_with(
        {
            "image_type": "2D",
            "microscope": "Keyence",
            "folders": ["/raw"],
            "channels": [{"num": 2, "label": "myelin"}],
        }
    )
    info.assert_called_once_with("Success", "Autofill complete!")
    error.assert_not_called()


def test_autofill_and_navigate_shows_error_when_upload_page_missing(monkeypatch):
    util = AutoFillUtil()
    util.set_selected_config(SimpleNamespace(read_text=lambda: "{}"))

    app_root = SimpleNamespace(show_page=MagicMock(), pages={})
    root = _Node(master=app_root)

    error = MagicMock()
    monkeypatch.setattr("controller.AutoFillUtil.messagebox.showerror", error)

    util.autofill_and_navigate(root)

    error.assert_called_once_with("Error", "Upload page not found")


def test_autofill_and_navigate_shows_error_when_apply_config_fails(monkeypatch):
    util = AutoFillUtil()
    util.set_selected_config(SimpleNamespace(read_text=lambda: "{}"))

    upload_page = MagicMock()
    upload_page.apply_config_data.side_effect = RuntimeError("bad config")
    app_root = SimpleNamespace(show_page=MagicMock(), pages={"Upload": upload_page})
    root = _Node(master=app_root)

    error = MagicMock()
    monkeypatch.setattr("controller.AutoFillUtil.messagebox.showerror", error)

    util.autofill_and_navigate(root)

    error.assert_called_once()
    assert "Failed to apply config" in error.call_args.args[1]
