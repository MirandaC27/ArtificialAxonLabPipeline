import json
from pathlib import Path
import shutil
import uuid

from ArtificialAxonLabPipeline.Backend.controller.SessionDataUtil import SessionDataUtil


def _set_fake_module_file(randompatch, root_path):
    fake_controller_dir = root_path / "controller"
    fake_controller_dir.mkdir()
    fake_module = fake_controller_dir / "SessionDataUtil.py"
    fake_module.write_text("# test stub", encoding="utf-8")
    randompatch.setattr("controller.SessionDataUtil.__file__", str(fake_module))
    return root_path / "data"


def _make_workspace_temp_root():
    root = Path(__file__).resolve().parent / "_tmp" / uuid.uuid4().hex
    root.mkdir(parents=True, exist_ok=False)
    return root


def test_clear_session_files_removes_known_outputs(randompatch):
    removed = []

    randompatch.setattr(
        "controller.SessionDataUtil.Path.exists",
        lambda path: path.name in {"folder_paths.json", "sessionData.txt"},
    )
    randompatch.setattr(
        "controller.SessionDataUtil.Path.unlink",
        lambda path: removed.append(path.name),
    )

    SessionDataUtil().clear_session_files()

    assert removed == ["folder_paths.json", "sessionData.txt"]


def test_save_folders_writes_json_txt_and_session_data(randompatch):
    root = _make_workspace_temp_root()
    try:
        data_dir = _set_fake_module_file(randompatch, root)
        util = SessionDataUtil()

        util.save_folders(
            selected_folders=[
                str(Path("/exp/Plate1_RAW")),
                str(Path("/exp/notes")),
            ],
            image_type="2D",
            microscope="Keyence",
            channels=[
                {"num": 2, "label": "myelin", "disabled": True},
                {"num": 1, "label": "axon"},
            ],
            num_fovs=9,
            disabled_fovs=["3", "7"],
        )

        json_data = json.loads((data_dir / "folder_paths.json").read_text(encoding="utf-8"))
        txt_data = (data_dir / "folder_paths.txt").read_text(encoding="utf-8")
        session_data = (data_dir / "sessionData.txt").read_text(encoding="utf-8")
        history_data = json.loads((data_dir / "history" / "sessions.json").read_text(encoding="utf-8"))

        assert json_data["Tracks"] == [str(Path("/exp/Plate1_RAW"))]
        assert json_data["Tracks1"] == [str(Path("/exp/CLEANED"))]
        assert json_data["Data"] == [str(Path("/exp/notes"))]
        assert json_data["ImageType"] == "2D"
        assert json_data["Microscope"] == "Keyence"
        assert json_data["NumFOVs"] == 9
        assert json_data["DisabledFOVs"] == ["3", "7"]
        assert json_data["Channels"] == [
            {"code": "CH2", "label": "myelin", "active": False},
            {"code": "CH1", "label": "axon", "active": True},
        ]
        assert json_data["SessionId"] == 1
        assert "Experiment Start Time:" in txt_data
        assert "Microscope Used: Keyence" in txt_data
        assert "CH2: myelin (Disabled)" in txt_data
        assert "Name of Folder: Plate1_RAW" in session_data
        assert "CH1: axon" in session_data
        assert len(history_data["sessions"]) == 1
        assert history_data["sessions"][0]["SessionId"] == 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_save_folders_handles_missing_raw_tracks(randompatch):
    root = _make_workspace_temp_root()
    try:
        data_dir = _set_fake_module_file(randompatch, root)
        util = SessionDataUtil()

        util.save_folders(
            selected_folders=[str(Path("/exp/processed"))],
            image_type="3D",
            microscope="Olympus",
            channels=[],
        )

        json_data = json.loads((data_dir / "folder_paths.json").read_text(encoding="utf-8"))
        session_data = (data_dir / "sessionData.txt").read_text(encoding="utf-8")

        assert json_data["Tracks"] == []
        assert json_data["Tracks1"] == []
        assert json_data["Data"] == [str(Path("/exp/processed"))]
        assert session_data.startswith("Name of Folder: No Raw Folder Selected")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_save_end_time_updates_json_and_text_outputs(randompatch):
    root = _make_workspace_temp_root()
    try:
        data_dir = _set_fake_module_file(randompatch, root)
        util = SessionDataUtil()
        util.save_folders(
            selected_folders=[str(Path("/exp/Plate1_RAW"))],
            image_type="3D",
            microscope="Keyence",
            channels=[],
        )

        util.save_end_time("2026-04-14 22:00:00")

        json_data = json.loads((data_dir / "folder_paths.json").read_text(encoding="utf-8"))
        txt_data = (data_dir / "folder_paths.txt").read_text(encoding="utf-8")
        history_data = json.loads((data_dir / "history" / "sessions.json").read_text(encoding="utf-8"))

        assert json_data["EndTime"] == "2026-04-14 22:00:00"
        assert "Experiment End Time: 2026-04-14 22:00:00" in txt_data
        assert history_data["sessions"][0]["EndTime"] == "2026-04-14 22:00:00"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_session_history_keeps_latest_ten_sessions(randompatch):
    root = _make_workspace_temp_root()
    try:
        data_dir = _set_fake_module_file(randompatch, root)
        util = SessionDataUtil()
        randompatch.setattr(util, "clear_session_files", lambda: None)

        for session_num in range(12):
            util.save_folders(
                selected_folders=[str(Path(f"/exp/Plate{session_num}_RAW"))],
                image_type="3D",
                microscope="Keyence",
                channels=[],
            )
            util.save_end_time(f"2026-04-14 22:{session_num:02d}:00")

        history_data = json.loads((data_dir / "history" / "sessions.json").read_text(encoding="utf-8"))
        session_ids = [session["SessionId"] for session in history_data["sessions"]]

        assert len(history_data["sessions"]) == 10
        assert session_ids == list(range(3, 13))
        assert history_data["sessions"][0]["Tracks"] == [str(Path("/exp/Plate2_RAW"))]
        assert history_data["sessions"][-1]["Tracks"] == [str(Path("/exp/Plate11_RAW"))]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_runtime_returns_result(randompatch, capsys):
    util = SessionDataUtil()
    times = iter([10.0, 12.5])
    randompatch.setattr("controller.SessionDataUtil.time.perf_counter", lambda: next(times))

    result = util.runtime(lambda value: value + 1, 4)

    assert result == 5
    assert "took 0 min 2.50 sec" in capsys.readouterr().out
