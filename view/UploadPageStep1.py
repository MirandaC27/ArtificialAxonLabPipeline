import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
import threading
import json
import sys
import os

sys.path.append(str(Path(__file__).resolve().parent.parent))
from controller.SessionDataUtil import SessionDataUtil

sd = SessionDataUtil()

CHANNELS = ['axon','myelin','nuclei','debris']
EXPERIMENTS = ['DAPI','GFP-mylein','CY5-myelin','GFP-debris','CY5-debris']


class UploadPageStep1(tk.Frame):

    def __init__(self, parent, controller=None):
        super().__init__(parent)

        self.controller = controller
        self.selected_folders = []
        self.channels = []

        self.build_ui()

    def build_ui(self):

        # Layout: left + right
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        

        # Vars
        self.image_type_var = tk.StringVar(value="3D")
        self.micro_type_var = tk.StringVar(value="Keyence")

        self.experiment_var = tk.StringVar()
        self.fov_var = tk.StringVar()
        self.frame_var = tk.StringVar()
        self.distance_var = tk.StringVar()
        self.ezra_var = tk.BooleanVar()

        # Left side of frame 
        left_frame = tk.Frame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tk.Button(left_frame, text="Add Folder", command=self.add_folder).pack(fill="x", pady=5)

        # Image Type
        image_frame = tk.LabelFrame(left_frame, text="Image Type")
        image_frame.pack(fill="x", pady=5)

        tk.Radiobutton(image_frame, text="2D", variable=self.image_type_var, value="2D").pack(side="left")
        tk.Radiobutton(image_frame, text="3D", variable=self.image_type_var, value="3D").pack(side="left")

        # Microscope
        micro_frame = tk.LabelFrame(left_frame, text="Microscope")
        micro_frame.pack(fill="x", pady=5)

        tk.Radiobutton(micro_frame, text="Keyence", variable=self.micro_type_var, value="Keyence").pack(side="left")
        tk.Radiobutton(micro_frame, text="Olympus", variable=self.micro_type_var, value="Olympus").pack(side="left")

        self.status_label = tk.Label(left_frame, text="", justify="left")
        self.status_label.pack(anchor="w", pady=5)

        # Channel settings 
        channel_frame = tk.Frame(left_frame)
        channel_frame.pack(fill="x", pady=5)

        tk.Label(channel_frame, text="Channel #:").grid(row=0, column=0)
        self.channel_num_entry = tk.Entry(channel_frame, width=6)
        self.channel_num_entry.grid(row=0, column=1)

        self.channel_label_var = tk.StringVar()
        self.channel_label_dropdown = ttk.Combobox(
            channel_frame,
            textvariable=self.channel_label_var,
            values=CHANNELS,
            state="readonly",
            width=12
        )
        self.channel_label_dropdown.grid(row=0, column=2, padx=5)
        self.channel_label_dropdown.set(CHANNELS[0])

        tk.Label(channel_frame, text="# of FOVs:").grid(row=0, column=3, padx=(10, 5))
        tk.Entry(channel_frame, textvariable=self.fov_var, width=6).grid(row=0, column=4)

        # Buttons
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Add Channel", command=self.add_channel).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Remove Channel", command=self.remove_channel).pack(side="left", padx=5)

        # Listbox
        self.channel_listbox = tk.Listbox(left_frame, height=5)
        self.channel_listbox.pack(fill="x", pady=5)

        # Right side Experiment Settings
        right_frame = tk.LabelFrame(self, text="Experiment Settings")
        right_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=(20, 10))

        # Experiment
        tk.Label(right_frame, text="Experiment").grid(row=0, column=0, sticky="e", pady=5)
        exp_menu = ttk.Combobox(
            right_frame,
            values=EXPERIMENTS,
            textvariable=self.experiment_var,
            state="readonly"
        )
        exp_menu.grid(row=0, column=1)
        exp_menu.set("Select experiment")

        # Frames
        tk.Label(right_frame, text="Frames").grid(row=1, column=0, sticky="e")
        tk.Entry(right_frame, textvariable=self.frame_var).grid(row=1, column=1)

        # Distance
        tk.Label(right_frame, text="Distance").grid(row=2, column=0, sticky="e")
        tk.Entry(right_frame, textvariable=self.distance_var).grid(row=2, column=1)

        # Ezra
        tk.Checkbutton(
            right_frame,
            text="Run Ezra Algorithm",
            variable=self.ezra_var
        ).grid(row=3, column=1, sticky="w")

        # Bottom nav buttons 

        nav_frame = tk.Frame(self)
        nav_frame.grid(row=1, column=0, columnspan=2, sticky="sew", padx=20, pady=10)
        
        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=1)
        
        tk.Button(
            nav_frame,
            text="Run",
            command=self.button_run
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        
        tk.Button(
            nav_frame,
            text="Back",
            command=lambda: self.controller.show_page("Home") if self.controller else None
        ).grid(row=1, column=0, sticky="ew", padx=5)
        
        tk.Button(
            nav_frame,
            text="Next",
            command=lambda: self.controller.show_page("Image Processing Stuff") if self.controller else None
        ).grid(row=1, column=1, sticky="ew", padx=5)

    # Logic for managing channels and folders

    def update_channel_listbox(self):
        self.channel_listbox.delete(0, tk.END)
        for ch in self.channels:
            self.channel_listbox.insert(tk.END, f"Channel {ch['num']} — {ch['label']}")

    def add_channel(self):
        num = self.channel_num_entry.get().strip()
        label = self.channel_label_var.get()

        if not num.isdigit():
            return

        num = int(num)

        if any(ch["num"] == num for ch in self.channels):
            return

        self.channels.append({"num": num, "label": label})
        self.channels.sort(key=lambda x: x["num"])

        self.update_channel_listbox()

    def remove_channel(self):
        num = self.channel_num_entry.get().strip()

        if not num.isdigit():
            return

        num = int(num)
        self.channels = [ch for ch in self.channels if ch["num"] != num]

        self.update_channel_listbox()

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folders.append(folder)
            self.status_label.config(text="\n".join(self.selected_folders))

    # Save JSON data

    def save_all_to_json(self):

        json_data = {
            "Folders": self.selected_folders,
            "ImageType": self.image_type_var.get(),
            "Microscope": self.micro_type_var.get(),
            "NumFOVs": self.fov_var.get(),
            "Experiment": self.experiment_var.get(),
            "Frames": self.frame_var.get(),
            "Distance": self.distance_var.get(),
            "RunEzra": self.ezra_var.get(),
            "Channels": self.channels
        }

        path = Path("data/settings.json")
        path.parent.mkdir(exist_ok=True)

        with open(path, "w") as f:
            json.dump(json_data, f, indent=4)

        print("Saved JSON:", json_data)

    # Run Button Logic

    def button_run(self):
        self.save_all_to_json()

        thread = threading.Thread(target=self.run_process)
        thread.start()

    def run_process(self):
        try:
            sd.save_folders(
                selected_folders=self.selected_folders,
                image_type=self.image_type_var.get(),
                microscope=self.micro_type_var.get(),
                channels=self.channels,
            )
        finally:
            sd.save_end_time()