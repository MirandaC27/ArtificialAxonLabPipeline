from pathlib import Path
from datetime import datetime
import json


class SessionDataUtil:

    def save_folders(self, selected_folders, image_type, microscope, channels):

        tracks = set()
        data = set()

        for folder in selected_folders:
            root = Path(folder)
            folder_name = root.name.upper()

            if "_RAW" in folder_name:
                tracks.add(str(root))
            else:
                data.add(str(root))

        if not tracks:
            print("No RAW folder selected")
            return

        raw_path = Path(list(tracks)[0])
        clean_path = raw_path.parent / "CLEANED"

        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        json_data = {
            "Tracks": sorted(tracks),
            "Tracks1": [str(clean_path)],
            "Data": sorted(data),
            "ImageType": image_type,
            "Microscope": microscope,
            "Channels": [
                {"code": f"CH{ch['num']}", "label": ch["label"]}
                for ch in channels
            ],
            "StartTime": start_time  
        }

        json_path = Path(__file__).resolve().parent.parent / "data" / "folder_paths.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

        self.save_txt(json_data)


    def save_txt(self, data):
        txt_path = Path(__file__).resolve().parent.parent / "data" / "folder_paths.txt"

        with open(txt_path, "w", encoding="utf-8") as f:

            f.write("Experiment Start Time: ")
            f.write(data.get("StartTime", "N/A") + "\n")  

            f.write("\nFolder Path to Tracks (Raw)\n")
            for p in data["Tracks"]:
                f.write(p + "\n")

            f.write("\nFolder Path to Tracks1 (Cleaned)\n")
            for p in data["Tracks1"]:
                f.write(p + "\n")

            f.write("\nMicroscope Used: ")
            f.write(data["Microscope"] + "\n")

            f.write("\nImage Type Used: ")
            f.write(data["ImageType"] + "\n")

            f.write("\nChannels Used:\n")
            for ch in data["Channels"]:
                f.write(f"{ch['code']}: {ch['label']}\n")
            
            f.write("\nExperiment Data:\n")
            for d in data["Data"]:
                f.write(d + "\n")


    