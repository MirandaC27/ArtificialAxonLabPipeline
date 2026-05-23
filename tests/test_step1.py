import json
from pathlib import Path
from datetime import datetime
import pytest
from unittest.mock import patch
import tkinter as tk

from view.UploadPageStep1 import UploadPageStep1



# FIXTURES

_root = None

@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    """
    Create an UploadPageStep1 instance with isolated filesystem.
    """
    global _root
    if _root is None:
        _root = tk.Tk()
        _root.withdraw()

    frame = UploadPageStep1(_root)

    # Create fake module directory
    fake_dir = tmp_path / "data"
    fake_dir.mkdir()

    fake_file = fake_dir / "UploadPageStep1.py"
    fake_file.write_text("# dummy")

    # Patch __file__ so JSON writes go to tmp dir
    monkeypatch.setattr(
        "view.UploadPageStep1.__file__",
        str(fake_file)
    )

    yield frame, fake_dir



# save_folders() Tests


def test_save_folders_classifies_directories(app_instance):
    app, fake_dir = app_instance

    app.selected_folders.extend([
        "/data/exp_RAW",
        "/data/other_folder"
    ])

    app.channels.append({"num": 1, "label": "Axons"})
    app.image_type_var.set("2D")

    app.save_folders()

    json_path = fake_dir.parent / "data" / "upload_settings.json"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["Tracks"] == [str(Path("/data/exp_RAW"))]
    assert data["Tracks1"] == [str(Path("/data/CLEANED"))]
    assert data["Data"] == [str(Path("/data/other_folder"))]
    assert data["ImageType"] == "2D"
    assert data["Channels"] == [
        {"code": "CH1", "label": "Axons"}
    ]


def test_save_folders_sorts_tracks(app_instance):
    app, fake_dir = app_instance

    app.selected_folders.extend([
        "/data/B_RAW",
        "/data/A_RAW",
    ])

    app.save_folders()

    json_path = fake_dir.parent / "data" / "upload_settings.json"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["Tracks"] == [
        str(Path("/data/A_RAW")),
        str(Path("/data/B_RAW"))
    ]


@patch("view.UploadPageStep1.platform.system")
def test_save_folders_writes_bash_paths(mock_platform, app_instance):
    mock_platform.return_value = "Windows"
    app, fake_dir = app_instance

    app.selected_folders.extend([
        r"C:\data\exp_RAW",
        r"C:\data\other_folder"
    ])

    app.save_folders()

    json_path = fake_dir.parent / "data" / "upload_settings.json"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["TracksBash"] == ["/c/data/exp_RAW"]
    assert data["DataBash"] == ["/c/data/other_folder"]
    assert data["Tracks1Bash"] == ["/c/data/CLEANED"]
    assert data["OrderedTrackBash"] == ["/c/data/ORDERED"]


def test_save_txt_output(app_instance):
    app, fake_dir = app_instance

    app.selected_folders.append("/data/exp_RAW")
    app.save_folders()
    
    txt_path = fake_dir.parent / "data" / "upload_settings.txt"

    with open(txt_path, "r", encoding="utf-8") as f:
        contents = f.read()

    assert "TRACKS" in contents
    assert str(Path("/data/exp_RAW")) in contents



# start_time() Tests


def test_start_time_adds_timestamp(app_instance):
    app, fake_dir = app_instance

    app.selected_folders.append("/data/exp_RAW")
    app.save_folders()

    app.start_time()

    json_path = fake_dir.parent / "data" / "upload_settings.json"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "START_TIME" in data
    datetime.strptime(data["START_TIME"], "%Y-%m-%d %H:%M:%S")




@patch("view.UploadPageStep1.subprocess.run")
@patch("view.UploadPageStep1.platform.system")
def test_run_step1_windows(mock_platform, mock_run, app_instance):
    app, _ = app_instance

    mock_platform.return_value = "Windows"

    app.run_step1()

    args = mock_run.call_args[0][0]

    assert "bash.exe" in args[0]
    assert args[1].endswith("rename_organize_keyence.sh")


@patch("view.UploadPageStep1.subprocess.run")
@patch("view.UploadPageStep1.platform.system")
def test_run_step1_unix(mock_platform, mock_run, app_instance):
    app, _ = app_instance

    mock_platform.return_value = "Darwin"

    app.run_step1()

    args = mock_run.call_args[0][0]

    assert args[0] == "/bin/bash"
    assert args[1].endswith("rename_organize_keyence.sh")



@patch.object(UploadPageStep1, "run_step1")
@patch.object(UploadPageStep1, "start_time")
@patch.object(UploadPageStep1, "save_folders")
def test_button_run_calls_all(mock_save, mock_start, mock_run, app_instance):
    app, _ = app_instance

    app.button_run()

    mock_save.assert_called_once()
    mock_start.assert_called_once()
    mock_run.assert_called_once()



def test_channels_convert_to_json_format(app_instance):
    app, fake_dir = app_instance

    app.selected_folders.append("/data/exp_RAW")

    app.channels.extend([
        {"num": 2, "label": "Debris"},
        {"num": 1, "label": "Axons"},
    ])

    app.save_folders()

    json_path = fake_dir.parent / "data" / "upload_settings.json"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["Channels"] == [
        {"code": "CH2", "label": "Debris"},
        {"code": "CH1", "label": "Axons"},
    ]