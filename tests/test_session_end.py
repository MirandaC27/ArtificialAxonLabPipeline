from types import SimpleNamespace
from unittest.mock import MagicMock

from view.SessionEnd import SessionEnd


class _FakePath:
    def __init__(self, exists=False, parent=None, children=None):
        self._exists = exists
        self.parent = parent if parent is not None else self
        self._children = children or {}

    def resolve(self):
        return self

    def __truediv__(self, key):
        return self._children[key]

    def exists(self):
        return self._exists


def test_rerun_configuration_uses_saved_config_and_autofill(monkeypatch):
    fake_config_path = _FakePath(exists=True)
    fake_data_dir = _FakePath(children={"upload_settings.json": fake_config_path})
    fake_project_dir = _FakePath(children={"data": fake_data_dir})
    fake_root = _FakePath()
    fake_parent = _FakePath(parent=fake_root)
    fake_root.parent = fake_parent
    fake_parent.parent = fake_project_dir
    fake_path_cls = MagicMock(return_value=fake_root)
    monkeypatch.setattr("view.SessionEnd.Path", fake_path_cls)

    controller = SimpleNamespace(show_page=MagicMock(), quit=MagicMock())
    page = SessionEnd.__new__(SessionEnd)
    page.controller = controller
    page.autofill = MagicMock()

    page.rerun_configuration()

    page.autofill.set_selected_config.assert_called_once_with(fake_config_path)
    page.autofill.autofill_and_navigate.assert_called_once_with(controller)


def test_rerun_configuration_shows_error_when_saved_config_missing(monkeypatch):
    errors = MagicMock()
    monkeypatch.setattr("view.SessionEnd.messagebox.showerror", errors)

    fake_config_path = _FakePath(exists=False)
    fake_data_dir = _FakePath(children={"upload_settings.json": fake_config_path})
    fake_project_dir = _FakePath(children={"data": fake_data_dir})
    fake_root = _FakePath()
    fake_parent = _FakePath(parent=fake_root)
    fake_root.parent = fake_parent
    fake_parent.parent = fake_project_dir
    fake_path_cls = MagicMock(return_value=fake_root)
    monkeypatch.setattr("view.SessionEnd.Path", fake_path_cls)

    controller = SimpleNamespace(show_page=MagicMock(), quit=MagicMock())
    page = SessionEnd.__new__(SessionEnd)
    page.controller = controller
    page.autofill = MagicMock()

    page.rerun_configuration()

    errors.assert_called_once_with("Error", "No saved configuration found to rerun")
    page.autofill.set_selected_config.assert_not_called()
