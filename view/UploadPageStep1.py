import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from datetime import datetime
import subprocess
import json
import platform


class UploadPageStep1(tk.Frame):

    def __init__(self, parent, controller=None):
        super().__init__(parent)

        self.controller = controller

        self.selected_folders = []
        self.channels = []

        self.build_ui()


    def build_ui(self):

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(7, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.image_type_var = tk.StringVar(value="3D")
        self.micro_type_var = tk.StringVar(value="Keyence")

        tk.Button(self, text="Add Folder", command=self.add_folder).grid(
            row=0, column=0, pady=8, sticky="ew", padx=20
        )

        tk.Button(self, text="Run", command=self.button_run).grid(
            row=8, column=0, pady=5, sticky="ew", padx=20
        )

        # Image Type
        image_frame = tk.LabelFrame(self, text="Image Type")
        image_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        tk.Radiobutton(image_frame, text="2D", variable=self.image_type_var, value="2D").grid(row=0, column=0)
        tk.Radiobutton(image_frame, text="3D", variable=self.image_type_var, value="3D").grid(row=0, column=1)

        # Microscope
        micro_frame = tk.LabelFrame(self, text="Microscope")
        micro_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        tk.Radiobutton(micro_frame, text="Keyence", variable=self.micro_type_var, value="Keyence").grid(row=0, column=0)
        tk.Radiobutton(micro_frame, text="Olympus", variable=self.micro_type_var, value="Olympus").grid(row=0, column=1)

        # Status
        self.status_label = tk.Label(self, text="", justify="left")
        self.status_label.grid(row=3, column=0, pady=5, padx=20, sticky="w")

        # Channel entry
        channel_frame = tk.Frame(self)
        channel_frame.grid(row=4, column=0, pady=5, padx=20, sticky="w")

        tk.Label(channel_frame, text="Channel #:").grid(row=0, column=0)
        self.channel_num_entry = tk.Entry(channel_frame, width=8)
        self.channel_num_entry.grid(row=0, column=1)

        tk.Label(channel_frame, text="Label:").grid(row=0, column=2)
        self.channel_label_entry = tk.Entry(channel_frame, width=20)
        self.channel_label_entry.grid(row=0, column=3)

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.grid(row=5, column=0, pady=8, padx=20, sticky="ew")

        tk.Button(button_frame, text="Add Channel", command=self.add_channel).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Remove Channel", command=self.remove_channel).grid(row=0, column=1, padx=5)

        # Channel list
        self.channel_listbox = tk.Listbox(self, width=50, height=10)
        self.channel_listbox.grid(row=7, column=0, pady=10, padx=20, sticky="nsew")

        tk.Button(  self,
                    text="Next",
                    command=lambda: self.controller.show_page("Settings")
                ).grid(row=9, column=0, pady=5, sticky="ew", padx=20)
        
        tk.Button(
                self,
                text="Go to Image Processing",
                command=lambda: self.controller.show_page("Image Processing Stuff")
            ).grid(row=10, column=0, pady=5, sticky="ew", padx=20)


    def update_channel_listbox(self):

        self.channel_listbox.delete(0, tk.END)

        for ch in self.channels:
            self.channel_listbox.insert(
                tk.END,
                f"Channel {ch['num']} — {ch['label']}"
            )


    def add_channel(self):

        num = self.channel_num_entry.get().strip()
        label = self.channel_label_entry.get().strip()

        if not num.isdigit():
            self.status_label.config(text="Channel number must be an integer.")
            return

        num = int(num)

        if label == "":
            self.status_label.config(text="Enter a channel label.")
            return

        for ch in self.channels:
            if ch["num"] == num:
                self.status_label.config(text=f"Channel {num} already exists.")
                return

        self.channels.append({"num": num, "label": label})
        self.channels.sort(key=lambda x: x["num"])

        self.update_channel_listbox()

        self.channel_num_entry.delete(0, tk.END)
        self.channel_label_entry.delete(0, tk.END)

        self.status_label.config(text="Channel added.")


    def remove_channel(self):

        num = self.channel_num_entry.get().strip()

        if not num.isdigit():
            self.status_label.config(text="Channel number must be an integer.")
            return

        num = int(num)

        new_list = [ch for ch in self.channels if ch["num"] != num]

        if len(new_list) == len(self.channels):
            self.status_label.config(text=f"Channel {num} not found.")
            return

        self.channels = new_list

        self.update_channel_listbox()

        self.channel_num_entry.delete(0, tk.END)
        self.channel_label_entry.delete(0, tk.END)

        self.status_label.config(text="Channel removed.")


    # -----------------------
    # FOLDER FUNCTIONS
    # -----------------------

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

        json_path = Path(__file__).resolve().parent / "folder_paths.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

        self.save_txt(json_data)


    def save_txt(self, data):

        with open("folder_paths.txt", "w", encoding="utf-8") as f:

            f.write("TRACKS\n")

            for p in data["Tracks"]:
                f.write(p + "\n")

            f.write("\nTRACKS1\n")

            for p in data["Tracks1"]:
                f.write(p + "\n")


    def start_time(self):

        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        json_path = Path(__file__).resolve().parent / "folder_paths.json"

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["START_TIME"] = start

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


    def run_step1(self):

        if platform.system() == "Windows":
            bash_path = r"C:\Program Files\Git\bin\bash.exe"
        else:
            bash_path = "/bin/bash"

        script_path = Path(__file__).resolve().parent.parent / "model" / "rename_organize_keyence.sh"

        subprocess.run([bash_path, str(script_path)], check=True)


    def button_run(self):

        print("Channels at run:", self.channels)
        print("Selected folders at run:", self.selected_folders)

        self.save_folders()
        self.start_time()
        self.run_step1()