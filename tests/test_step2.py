import json
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

import view.UploadPageStep2 as app


@pytest.fixture(autouse=True)
def reset_globals(tmp_path, monkeypatch):
    #writes to a temporary directory so we don't write to real disk.

    app.selected_folders.clear()

    # Redirect working directory to temp path
    monkeypatch.chdir(tmp_path)

    yield



# save_folders() Tests
def test_save_folders_classifies_directories():
    """
    Ensures folders are correctly categorized into:
    - Cleaned (endswith CLEANED)
    - Ordered (endswith ORDERED)
    - Data (everything else)
    """

    app.selected_folders.extend([
        "/data/sample_CLEANED",
        "/data/sample_ORDERED",
        "/data/raw_data"
    ])

    app.save_folders()

    with open("folder_paths.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["Cleaned"] == ["/data/sample_CLEANED"]
    assert data["Ordered"] == ["/data/sample_ORDERED"]
    assert data["Data"] == ["/data/raw_data"]


def test_save_folders_sorts_output():
    """
    Ensures output lists are sorted alphabetically.
    """

    app.selected_folders.extend([
        "/data/B_CLEANED",
        "/data/A_CLEANED",
    ])

    app.save_folders()

    with open("folder_paths.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["Cleaned"] == [
        "/data/A_CLEANED",
        "/data/B_CLEANED"
    ]


def test_save_folders_empty():
    """
    If no folders are selected, JSON should contain empty lists.
    """

    app.save_folders()

    with open("folder_paths.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["Cleaned"] == []
    assert data["Ordered"] == []
    assert data["Data"] == []



# add_folder() Tests
@patch("view.UploadPageStep2.save_folders")
@patch("view.UploadPageStep2.filedialog.askdirectory")
def test_add_folder_appends_and_updates_label(mock_dialog, mock_save):
    """
    Ensures:
    - Folder returned from dialog is appended
    - status_label is updated
    - save_folders() is called
    """

    mock_dialog.return_value = "/data/new_folder"

    # Mock status_label
    app.status_label = MagicMock()

    app.add_folder()

    assert "/data/new_folder" in app.selected_folders
    mock_save.assert_called_once()
    app.status_label.config.assert_called_once()


@patch("view.UploadPageStep2.filedialog.askdirectory")
def test_add_folder_cancel_does_nothing(mock_dialog):
    """
    If dialog returns empty string (user cancels),
    nothing should be added.
    """

    mock_dialog.return_value = ""

    initial_len = len(app.selected_folders)

    app.add_folder()

    assert len(app.selected_folders) == initial_len

# run_step2() Tests
@patch("view.UploadPageStep2.subprocess.run")
@patch("view.UploadPageStep2.platform.system")
def test_run_step2_windows(mock_platform, mock_run):
    """
    On Windows, Git bash path should be used.
    """

    mock_platform.return_value = "Windows"

    app.run_step2()

    args = mock_run.call_args[0][0]

    assert r"C:\Program Files\Git\bin\bash.exe" in args[0]
    assert args[1].endswith("step2_organize-keyence-multichan-lowe.sh")


@patch("view.UploadPageStep2.subprocess.run")
@patch("view.UploadPageStep2.platform.system")
def test_run_step2_unix(mock_platform, mock_run):
    """
    On macOS/Linux, /bin/bash should be used.
    """

    mock_platform.return_value = "Darwin"

    app.run_step2()

    args = mock_run.call_args[0][0]

    assert args[0] == "/bin/bash"
    assert args[1].endswith("step2_organize-keyence-multichan-lowe.sh")



# button_run() Tests
@patch("view.UploadPageStep2.run_step2")
def test_button_run_calls_run_step2(mock_run):
    """
    Ensures button_run() triggers run_step2().
    """

    app.button_run()

    mock_run.assert_called_once()