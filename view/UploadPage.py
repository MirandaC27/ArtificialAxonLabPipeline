import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from datetime import datetime
import json

selected_folders = []

def add_folder():
    folder = filedialog.askdirectory(title="Select a folder")
    if folder:
        selected_folders.append(folder)    
        status_label.config(
            text="Selected folders:\n" + "\n".join(selected_folders)
        )
        save_folders()

def save_folders():
    global tracks, tracks1
    tracks = set()
    tracks1 = set()

    for folder in selected_folders:
        root = Path(folder)

        folder_name = root.name.upper()
        if folder_name.endswith("RAW"):
            tracks.add(str(root))
        elif folder_name.endswith("CLEANED"):
            tracks1.add(str(root))

    data = {
        "TRACKS": sorted(tracks),
        "TRACKS1": sorted(tracks1)
    }

    with open("folder_paths.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4) 


def start_time():
    start = datetime.now()
    start = start.strftime("%Y-%m-%d %H:%M:%S")

    with open("folder_paths.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data["START_TIME"] = start
    
    with open("folder_paths.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


window = tk.Tk()
window.title("File Uploader")
window.geometry("600x300")

tk.Button(window, text="Add Folder", command=add_folder).pack(pady=10)
tk.Button(window, text="Run", command=start_time).pack(pady=10)

status_label = tk.Label(window, text="")
status_label.pack(pady=5)

window.mainloop()