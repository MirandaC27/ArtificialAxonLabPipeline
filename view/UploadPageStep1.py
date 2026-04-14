from concurrent.futures import thread
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from pathlib import Path
import subprocess
import platform
import threading
import signal
import json
import sys
import os

sys.path.append(str(Path(__file__).resolve().parent.parent))
from controller.SessionDataUtil import SessionDataUtil

sd = SessionDataUtil()


CHANNELS = ['axon','myelin','nuclei','debris']
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
        self.fov_var = tk.StringVar()

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

        #channel label entry
        self.channel_label_var = tk.StringVar()

        self.channel_label_dropdown = ttk.Combobox(
            channel_frame,
            textvariable=self.channel_label_var,
            values=CHANNELS,
            state="readonly",
            width=9
        )
        self.channel_label_dropdown.grid(row=0, column=2)
        self.channel_label_dropdown.set(CHANNELS[0])  # default value

        tk.Label(channel_frame, text="# of FOVs:").grid(row=0, column=3, padx=(10, 0))
        tk.Entry(channel_frame, textvariable=self.fov_var, width=6).grid(row=0, column=4)

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.grid(row=5, column=0, pady=8, padx=20, sticky="ew")

        tk.Button(button_frame, text="Add Channel", command=self.add_channel).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Remove Channel", command=self.remove_channel).grid(row=0, column=1, padx=5)

        # Channel list
        self.channel_listbox = tk.Listbox(self, width=50, height=5)
        self.channel_listbox.grid(row=7, column=0, pady=10, padx=20, sticky="nw")

        self.grid_columnconfigure(0, weight=1)

        # next and Previous buttons 
        nav_frame = tk.Frame(self)
        nav_frame.grid(row=11, column=0, pady=5, padx=20, sticky="ew")
        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=1)

        tk.Button(
            nav_frame,
            text="Back",
            command=lambda: self.controller.show_page("Home")
        ).grid(row=0, column=0, padx=5, sticky="ew")

        tk.Button(
            nav_frame,
            text="Next",
            command=lambda: self.controller.show_page("Settings")
        ).grid(row=0, column=1, padx=5, sticky="ew")
        
    def update_channel_listbox(self):

        self.channel_listbox.delete(0, tk.END)

        for ch in self.channels:
            self.channel_listbox.insert(
                tk.END,
                f"Channel {ch['num']} — {ch['label']}"
            )


    def add_channel(self):

        num = self.channel_num_entry.get().strip()
        label = self.channel_label_var.get().strip()

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
        self.channel_label_dropdown.set(CHANNELS[0])

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
        self.channel_label_dropdown.set(CHANNELS[0])

        self.status_label.config(text="Channel removed.")


    def add_folder(self):

        folder = filedialog.askdirectory(title="Select a folder")

        if folder:
            self.selected_folders.append(folder)

            self.status_label.config(
                text="Selected folders:\n" + "\n".join(self.selected_folders)
            )

            # Push the CLEANED path to MaskingSettingsPage as soon as a
            # RAW folder is picked, so the masking page stays in sync.
            self._push_data_to_masking()
    
    def _get_cleaned_path(self):
        """
        Derives the CLEANED sibling directory from whichever selected folder
        contains '_RAW' in its name.  Returns a Path, or None if not found.
        """
        for folder in self.selected_folders:
            root = Path(folder)
            if "_RAW" in root.name.upper():
                return root.parent / "CLEANED"
        return None
     
    def _push_data_to_masking(self):
        if not hasattr(self.controller, "get_page"):
            return

        masking_page = self.controller.get_page("Masking Settings")
        if masking_page is None:
            return

        # Push path
        cleaned = self._get_cleaned_path()
        if cleaned is not None and hasattr(masking_page, "set_base_path"):
            masking_page.set_base_path(str(cleaned))

        # Push channels
        if hasattr(masking_page, "set_channels"):
            masking_page.set_channels(self.channels)

    def get_num_fovs(self):
        val = self.fov_var.get().strip()
        return int(val) if val.isdigit() else 0
    
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
            "NumFOVs": self.get_num_fovs(),
            "Channels": [
                {"code": f"CH{ch['num']}", "label": ch["label"]}
                for ch in self.channels
            ],
        }

        json_path = Path(__file__).resolve().parent.parent / "data" / "folder_paths.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

        self.save_txt(json_data)

        self._push_data_to_masking()

    
    def apply_config_data(self, parsed):
        """
        parsed = {
            "image_type": str,
            "microscope": str,
            "folders": list[str],
            "channels": list[dict{'num', 'label'}]
        }
        """

        if "image_type" in parsed and parsed["image_type"] in ("2D", "3D"):
            self.image_type_var.set(parsed["image_type"])

        if "microscope" in parsed and parsed["microscope"] in ("Keyence", "Olympus"):
            self.micro_type_var.set(parsed["microscope"])

        if "folders" in parsed and isinstance(parsed["folders"], list):
            self.selected_folders = parsed["folders"]
            self.status_label.config(
                text="Selected folders:\n" + "\n".join(self.selected_folders)
            )

        if "channels" in parsed and isinstance(parsed["channels"], list):
            self.channels = []
            for ch in parsed["channels"]:
                try:
                    num = int(ch.get("num"))
                    label = str(ch.get("label", ""))
                    if label:
                        self.channels.append({"num": num, "label": label})
                except Exception:
                    continue

            self.channels.sort(key=lambda x: x["num"])
            self.update_channel_listbox()

        # clear entry fields
        self.channel_num_entry.delete(0, tk.END)
        self.channel_label_dropdown.set(CHANNELS[0])

        self.status_label.config(text="Autofill applied.")

    def stop_script(self):
        self.stop_flag = True

        if self.process:
            try:
                if platform.system() == "Windows":
                    subprocess.call(["taskkill", "/F", "/T", "/PID", str(self.process.pid)])
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except Exception as e:
                print("Error stopping process:", e)
        
    def close_popup(self):
        if self.popup:
            self.progress.stop()
            self.popup.destroy()

    def show_loading_popup(self):
        self.popup = tk.Toplevel(self)
        self.popup.title("Running")
        self.popup.geometry("300x200")
        self.popup.transient(self)
        self.popup.grab_set()  

        self.progress = ttk.Progressbar(self.popup, mode="indeterminate")
        self.progress.pack(pady=20, padx=20, fill="x")
        self.progress.start(10)

        tk.Label(self.popup, text="Running script...").pack(pady=10)

        btn_frame = tk.Frame(self.popup)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Stop", command=self.stop_script).grid(row=0, column=1, padx=10)


    def run_step1(self):
        if platform.system() == "Windows":
            bash_path = r"C:\Program Files\Git\bin\bash.exe"
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            preexec_fn = None
        else:
            bash_path = "/bin/bash"
            creationflags = 0
            preexec_fn = os.setsid
    
        script_path = Path(__file__).resolve().parent.parent / "model" / "rename_organize_keyence.sh"
    
        self.process = subprocess.Popen(
            [bash_path, str(script_path)],
            creationflags=creationflags,
            preexec_fn=preexec_fn
        )
    
        while self.process.poll() is None:
            if self.stop_flag:
                break
            
    def run_process(self):
        print("Channels at run:", self.channels)
        print("Selected folders at run:", self.selected_folders)

        try:
            sd.save_folders(
                selected_folders=self.selected_folders,
                image_type=self.image_type_var.get(),
                microscope=self.micro_type_var.get(),
                num_fovs=self.get_num_fovs(),
                channels=self.channels,
            )

            sd.runtime(self.run_step1)

        finally:
            sd.save_end_time()
            self.after(0, self.close_popup)
    
    def button_run(self):
        self.stop_flag = False
        self.process = None

        self.show_loading_popup()

        thread = threading.Thread(target=self.run_process)
        thread.start()