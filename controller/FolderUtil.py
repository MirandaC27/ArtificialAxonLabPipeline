from tkinter import filedialog
from pathlib import Path
import json

def add_folder(self):

        folder = filedialog.askdirectory(title="Select a folder")

        if folder:
            self.selected_folders.append(folder)

            self.status_label.config(
                text="Selected folders:\n" + "\n".join(self.selected_folders)
            )


def save_folders(self):

    tracks = set()
    data = set()

    for folder in self.selected_folders:
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

        json_data = {
            "Tracks": sorted(tracks),
            "Tracks1": [str(clean_path)],
            "Data": sorted(data),
            "ImageType": self.image_type_var.get(),
            "Microscope": self.micro_type_var.get(),
            "Channels": [
                {"code": f"CH{ch['num']}", "label": ch["label"]}
                for ch in self.channels
            ],
        }
    

        json_path = Path(__file__).resolve().parent.parent / "data" / "folder_paths.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)

        # Saves JSON file
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

        # Saves text file 
        self.save_txt(json_data)

        

def save_txt(self, data):
    txt_path = Path(__file__).resolve().parent.parent / "data" / "folder_paths.txt"

    with open(txt_path, "w", encoding="utf-8") as f:

        f.write("Experiment Start Time\n")
        f.write(data.get("StartTime", "N/A") + "\n")

        f.write("\nFolder Path to Tracks\n")
        for p in data["Tracks"]:
            f.write(p + "\n")

        f.write("\nFolder Path to Tracks1\n")
        for p in data["Tracks1"]:
            f.write(p + "\n")

        f.write("\nExperiment Data\n")
        for d in data["Data"]:
            f.write(d + "\n")

        f.write("\nMicroscope Used\n")
        f.write(data["Microscope"] + "\n")

        f.write("\nImage Tyoe Used\n")
        f.write(data["ImageType"] + "\n")

        f.write("\nChannels USed\n")
        for ch in data["Channels"]:
            f.write(f"{ch['code']}: {ch['label']}\n")