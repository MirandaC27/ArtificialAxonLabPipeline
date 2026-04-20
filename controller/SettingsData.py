# SettingsData.py
from pathlib import Path
from datetime import datetime
import json


class SettingsData:

    def data_dir(self):
        return Path(__file__).resolve().parent.parent / "data"

    def clear_session_files(self):
        json_path = self.data_dir() / "settingsInputs.json"
        if json_path.exists():
            json_path.unlink()

    def save_settings(self, experiment, frames, ezra, distance):
        self.clear_session_files()

        json_data = {
            "experiment": experiment,
            "frames": int(frames) if frames else None,
            "run_ezra": bool(ezra),
            "distance_between_frames": float(distance) if distance else None,
        }

        json_dir = self.data_dir()
        json_dir.mkdir(parents=True, exist_ok=True)

        json_path = json_dir / "settingsInputs.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)
