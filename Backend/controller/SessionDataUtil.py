from pathlib import Path
from datetime import datetime
import json
import time


class SessionDataUtil:
    HISTORY_LIMIT = 10

    def data_dir(self):
        return Path(__file__).resolve().parent.parent / "data"
    
    def txtdata_dir(self):
        return Path(__file__).resolve().parent.parent / "data" / "txt"

    def history_path(self):
        history_dir = self.data_dir() / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir / "sessions.json"

    def load_session_history(self):
        history_path = self.history_path()
        if not history_path.exists():
            return {"sessions": []}

        try:
            with open(history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return {"sessions": []}

        sessions = data.get("sessions", [])
        if not isinstance(sessions, list):
            sessions = []
        return {"sessions": sessions}

    def save_session_history(self, history):
        with open(self.history_path(), "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)

    def next_session_id(self, sessions):
        existing_ids = [
            session.get("SessionId", 0)
            for session in sessions
            if isinstance(session.get("SessionId"), int)
        ]
        return (max(existing_ids) if existing_ids else 0) + 1

    def upsert_session_history(self, data):
        history = self.load_session_history()
        sessions = history["sessions"]
        session_id = data.get("SessionId")

        for index, session in enumerate(sessions):
            if session.get("SessionId") == session_id:
                sessions[index] = data
                self.save_session_history(history)
                return

        sessions.append(data)
        sessions.sort(key=lambda session: session.get("StartTime", ""))
        if len(sessions) > self.HISTORY_LIMIT:
            del sessions[: len(sessions) - self.HISTORY_LIMIT]
        self.save_session_history(history)

    def clear_session_files(self):
        data_dir = self.data_dir()
        for name in ("folder_paths.json", "folder_paths.txt", "sessionData.txt"):
            path = data_dir / name
            if path.exists():
                path.unlink()

    def save_folders(self, selected_folders, image_type, microscope, channels, num_fovs=None, disabled_fovs=None):
        self.clear_session_files()

        tracks = set()
        data = set()

        for folder in selected_folders:
            root = Path(folder)
            # Check for _RAW in folder name to categorize as a 'Track'
            if "_RAW" in root.name.upper():
                tracks.add(str(root))
            else:
                data.add(str(root))

        # Handle empty tracks 
        if tracks:
            raw_path = Path(list(tracks)[0])
            clean_path = raw_path.parent / "CLEANED"
        else:
            clean_path = "N/A"

        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        json_data = {
            "Tracks": sorted(tracks),
            "Tracks1": [str(clean_path)] if clean_path != "N/A" else [],
            "Data": sorted(data),
            "ImageType": image_type,
            "Microscope": microscope,
            "NumFOVs": num_fovs,
            "DisabledFOVs": disabled_fovs if disabled_fovs else [],
            "Channels": [
                {
                    "code": f"CH{ch['num']}", 
                    "label": ch["label"],
                    "active": not ch.get("disabled", False)
                }
                for ch in channels
            ],
            "StartTime": start_time
        }

        history = self.load_session_history()
        json_data["SessionId"] = self.next_session_id(history["sessions"])

        json_dir = self.data_dir()
        json_dir.mkdir(parents=True, exist_ok=True) # Ensure data directory exists
        json_path = json_dir / "folder_paths.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

        # Update files
        self.save_txt(json_data)
        self.session_data(json_data)  
        self.upsert_session_history(json_data)

    def save_end_time(self, end_time=None):
        json_path = self.data_dir() / "folder_paths.json"
        if not json_path.exists():
            return

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if end_time is None:
            end_time = self.endDateTime()

        data["EndTime"] = end_time

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        self.save_txt(data)
        self.session_data(data)  
        self.upsert_session_history(data)

    def save_txt(self, data):
        txt_path = self.txtdata_dir() / "folder_paths.txt"

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Experiment Start Time: {data.get('StartTime', 'N/A')}\n")

            if data.get("EndTime"):
                f.write(f"Experiment End Time: {data['EndTime']}\n")

            f.write("\nFolder Path to Tracks (Raw)\n")
            for p in data.get("Tracks", []):
                f.write(p + "\n")

            f.write("\nFolder Path to Tracks1 (Cleaned)\n")
            for p in data.get("Tracks1", []):
                f.write(p + "\n")

            f.write(f"\nMicroscope Used: {data.get('Microscope', 'N/A')}\n")
            f.write(f"Image Type Used: {data.get('ImageType', 'N/A')}\n")
            f.write(f"Number of Fields of View: {data.get('NumFOVs', 0)}\n")

            f.write("\nChannels Used:\n")
            for ch in data.get("Channels", []):
                status = "Active" if ch.get('active') else "Disabled"
                f.write(f"{ch['code']}: {ch['label']} ({status})\n")

            f.write("\nExperiment Data:\n")
            for d in data.get("Data", []):
                f.write(d + "\n")

    def get_folder_name(self, path: str) -> str:
        return Path(path).name

    def session_data(self, data):
        txt_path = self.txtdata_dir() / "sessionData.txt"

        tracks_list = data.get("Tracks", [])
        raw_path = tracks_list[0] if tracks_list else None
        folder_name = self.get_folder_name(raw_path) if raw_path else "No Raw Folder Selected"

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Name of Folder: {folder_name}\n")
            f.write("\nChannels Used:\n")
            for ch in data.get("Channels", []):
                f.write(f"{ch['code']}: {ch['label']}\n")

    def runtime(self, func, *args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = end - start
        print(f"{func.__name__} took {int(elapsed // 60)} min {elapsed % 60:.2f} sec")
        return result

    def endDateTime(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
