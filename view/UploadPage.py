import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from datetime import datetime
import subprocess
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
    global tracks, tracks1, data
    tracks = set()
    tracks1 = set()
    data = set()

    for folder in selected_folders:
        root = Path(folder)

        folder_name = root.name.upper()
        if folder_name.endswith("RAW"):
            tracks.add(str(root))
        elif folder_name.endswith("CLEANED"):
            tracks1.add(str(root))
        else:
            data.add(str(root))

    data = {
        "Tracks": sorted(tracks),
        "Tracks1": sorted(tracks1),
        "Data": sorted(data)
    }

    with open("folder_paths.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4) 
    
    save_txt(data)

def save_txt(data):
    with open("folder_paths.txt", "w", encoding="utf-8") as f:
        f.write("TRACKS\n")
        for p in data["Tracks"]:
            f.write(p + "\n")

        f.write("\nTRACKS1\n")
        for p in data["Tracks1"]:
            f.write(p + "\n")


def start_time():
    start = datetime.now()
    start = start.strftime("%Y-%m-%d %H:%M:%S")

    with open("folder_paths.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data["START_TIME"] = start
    
    with open("folder_paths.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def run_test():
    bash_path = r"C:\Program Files\Git\bin\bash.exe"
    subprocess.run([bash_path, "../model/step2_organize-keyence-singlechan-lowe.sh"], check=True)

def button_run():
    start_time()
    run_test()

window = tk.Tk()
window.title("File Uploader")
window.geometry("600x300")

tk.Button(window, text="Add Folder", command=add_folder).pack(pady=10)
tk.Button(window, text="Run", command=button_run).pack(pady=10)

status_label = tk.Label(window, text="")
status_label.pack(pady=5)

window.mainloop()