import json
import os
from pathlib import Path
from datetime import datetime
import pytest
from unittest.mock import patch, MagicMock

import view.UploadPageStep1 as app


@pytest.fixture(autouse=True)
def reset_globals(tmp_path, monkeypatch):
    """
    Reset global state before each test and isolate file writes to tmp dir.
    """
    app.selected_folders.clear()
    app.channels.clear()

    # Redirect working directory to temp path
    monkeypatch.chdir(tmp_path)

    yield


@pytest.fixture
def mock_image_type(monkeypatch):
    mock_var = MagicMock()
    mock_var.get.return_value = "2D"
    monkeypatch.setattr(app, "image_type_var", mock_var)


def test_save_folders_classifies_directories(mock_image_type):
    app.selected_folders.extend([
        "/data/experiment_PLATE01",
        "/data/sample_cleaned",
        "/data/other_folder"
    ])

    app.channels.append({"num": 1, "label": "Axons"})

    app.save_folders()

    with open("folder_paths.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["Tracks"] == ["/data/experiment_PLATE01"]
    assert data["Tracks1"] == ["/data/sample_cleaned"]
    assert data["Data"] == ["/data/other_folder"]
    assert data["ImageType"] == "2D"
    assert data["Channels"] == [
        {"code": "CH1", "label": "Axons"}
    ]


def test_save_folders_sorts_tracks(mock_image_type):
    app.selected_folders.extend([
        "/data/B_PLATE01",
        "/data/A_PLATE01",
    ])

    app.save_folders()

    with open("folder_paths.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["Tracks"] == [
        "/data/A_PLATE01",
        "/data/B_PLATE01"
    ]


def test_save_txt_output(mock_image_type):
    app.selected_folders.append("/data/exp_PLATE01")
    app.save_folders()

    with open("folder_paths.txt", "r", encoding="utf-8") as f:
        contents = f.read()

    assert "TRACKS" in contents
    assert "/data/exp_PLATE01" in contents


# start_time() Tests


def test_start_time_adds_timestamp(mock_image_type):
    # First create valid json
    app.selected_folders.append("/data/exp_PLATE01")
    app.save_folders()

    app.start_time()

    with open("folder_paths.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "START_TIME" in data

    # Ensure timestamp format
    datetime.strptime(data["START_TIME"], "%Y-%m-%d %H:%M:%S")


# run_step1() Tests

@patch("view.UploadPageStep1.subprocess.run")
@patch("view.UploadPageStep1.platform.system")
def test_run_step1_windows(mock_platform, mock_run):
    mock_platform.return_value = "Windows"

    app.run_step1()

    assert mock_run.called
    args = mock_run.call_args[0][0]

    assert "bash.exe" in args[0]
    assert args[1].endswith("step1_rename-keyence.sh")


@patch("view.UploadPageStep1.subprocess.run")
@patch("view.UploadPageStep1.platform.system")
def test_run_step1_unix(mock_platform, mock_run):
    mock_platform.return_value = "Darwin"

    app.run_step1()

    args = mock_run.call_args[0][0]

    assert args[0] == "/bin/bash"
    assert args[1].endswith("step1_rename-keyence.sh")


@patch("view.UploadPageStep1.run_step1")
@patch("view.UploadPageStep1.start_time")
def test_button_run_calls_both(mock_start, mock_run):
    app.button_run()

    mock_start.assert_called_once()
    mock_run.assert_called_once()


def test_channels_convert_to_json_format(mock_image_type):
    app.selected_folders.append("/data/exp_PLATE01")

    app.channels.extend([
        {"num": 2, "label": "Debris"},
        {"num": 1, "label": "Axons"},
    ])

    app.save_folders()

    with open("folder_paths.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["Channels"] == [
        {"code": "CH2", "label": "Debris"},
        {"code": "CH1", "label": "Axons"},
    ]