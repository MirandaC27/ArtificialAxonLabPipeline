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
    global DIR1, DIR2, DIR3
    DIR1 = set()
    DIR2 = set()
    DIR3 = set()

    for folder in selected_folders:
        root = Path(folder)

        folder_name = root.name.upper()
        if folder_name.endswith("CLEANED"):
            DIR2.add(str(root))
        elif folder_name.endswith("ORDERED"):
            DIR3.add(str(root))
        else:
            DIR1.add(str(root))

    data = {
        "Cleaned": sorted(DIR2),
        "Ordered": sorted(DIR3),
        "Data": sorted(DIR1)
    }

    with open("folder_paths.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4) 
    
def run_step2():
    if platform.system() == "Windows":
        bash_path = r"C:\Program Files\Git\bin\bash.exe"
    else:
        bash_path = "/bin/bash"

    script_path = Path(__file__).resolve().parent.parent / "model" / "step2_organize-keyence-singlechan-lowe.sh"

    subprocess.run([bash_path, str(script_path)], check=True)

def button_run():
    run_step2()

window = tk.Tk()
window.title("File Uploader")
window.geometry("600x300")

tk.Button(window, text="Add Folder", command=add_folder).pack(pady=10)
tk.Button(window, text="Run", command=button_run).pack(pady=10)

status_label = tk.Label(window, text="")
status_label.pack(pady=5)

window.mainloop()