import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from datetime import datetime
import subprocess
import json
import platform

selected_folders = []

# global storage for channels
channels = []   # list of dicts: {"num": int, "label": str}

#global image var


def update_channel_listbox():
    channel_listbox.delete(0, tk.END)
    for ch in channels:
        channel_listbox.insert(tk.END, f"Channel {ch['num']} — {ch['label']}")

def add_channel():
    num = channel_num_entry.get().strip()
    label = channel_label_entry.get().strip()

    if not num.isdigit():
        status_label.config(text="Channel number must be an integer.")
        return

    num = int(num)

    global channels

    if label == "":
        status_label.config(text="Enter a channel label.")
        return

    for ch in channels:
        if ch["num"] == num:
            status_label.config(text=f"Channel {num} already exists.")
            return

    channels.append({"num": num, "label": label})
    channels.sort(key=lambda x: x["num"])

    update_channel_listbox()

    channel_num_entry.delete(0, tk.END)
    channel_label_entry.delete(0, tk.END)
    status_label.config(text="Channel added.")


def remove_channel():
    num = channel_num_entry.get().strip()

    if not num.isdigit():
        status_label.config(text="Channel number must be an integer.")
        return

    num = int(num)

    global channels

    new_list = [ch for ch in channels if ch["num"] != num]

    if len(new_list) == len(channels):
        status_label.config(text=f"Channel {num} not found.")
        return

    channels = new_list

    update_channel_listbox()

    channel_num_entry.delete(0, tk.END)
    channel_label_entry.delete(0, tk.END)
    status_label.config(text="Channel removed.")

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
        if folder_name.endswith("PLATE01"):
            tracks.add(str(root))
        elif folder_name.endswith("CLEANED"):
            tracks1.add(str(root))
        else:
            data.add(str(root))

    data = {
        "Tracks": sorted(tracks),
        "Tracks1": sorted(tracks1),
        "Data": sorted(data),
        "ImageType": image_type_var.get(),
        "Channels": [
            {
                "code": f"CH{ch['num']}",
                "label": ch["label"]
            }
            for ch in channels
        ]
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


def run_step1():
    if platform.system() == "Windows":
        bash_path = r"C:\Program Files\Git\bin\bash.exe"
    else:
        bash_path = "/bin/bash"

    script_path = Path(__file__).resolve().parent.parent / "model" / "step1_rename-keyence.sh"

    subprocess.run([bash_path, str(script_path)], check=True)

def button_run():
    start_time()
    run_step1()


# window
window = tk.Tk()
window.title("File Uploader")
window.geometry("600x350")

window.grid_rowconfigure(0, weight=0)
window.grid_rowconfigure(7, weight=1)
window.grid_columnconfigure(0, weight=1)

image_type_var = tk.StringVar(master=window, value="3D")

# buttons
tk.Button(window, text="Add Folder", command=add_folder).grid(
    row=0, column=0, pady=8, sticky="ew", padx=20
)

tk.Button(window, text="Run", command=button_run).grid(
    row=7, column=0, pady=5, sticky="ew", padx=20
)

# Image Type Selector
image_frame = tk.LabelFrame(window, text="Image Type")
image_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

tk.Radiobutton(image_frame, text="2D", variable=image_type_var, value="2D").grid(row=2, column=0, padx=10)
tk.Radiobutton(image_frame, text="3D", variable=image_type_var, value="3D").grid(row=2, column=1, padx=10)

# status
status_label = tk.Label(window, text="", justify="left")
status_label.grid(row=3, column=0, pady=5, padx=20, sticky="w")

# channel entry
channel_frame = tk.Frame(window)
channel_frame.grid(row=4, column=0, pady=5, padx=20, sticky="w")

tk.Label(channel_frame, text="Channel #:").grid(row=0, column=0, padx=5)
channel_num_entry = tk.Entry(channel_frame, width=8)
channel_num_entry.grid(row=0, column=1, padx=5)

tk.Label(channel_frame, text="Label:").grid(row=0, column=2, padx=5)
channel_label_entry = tk.Entry(channel_frame, width=20)
channel_label_entry.grid(row=0, column=3, padx=5)

# NEW: add/remove buttons instead of radio buttons
button_frame = tk.Frame(window)
button_frame.grid(row=5, column=0, pady=8, padx=20, sticky="ew")

tk.Button(button_frame, text="Add Channel", command=add_channel).grid(
    row=0, column=0, padx=5, sticky="ew"
)

tk.Button(button_frame, text="Remove Channel", command=remove_channel).grid(
    row=0, column=1, padx=5, sticky="ew"
)

button_frame.grid_columnconfigure(0, weight=1)
button_frame.grid_columnconfigure(1, weight=1)

# channel list
channel_listbox = tk.Listbox(window, width=50, height=10)
channel_listbox.grid(row=7, column=0, pady=10, padx=20, sticky="nsew")

window.mainloop()