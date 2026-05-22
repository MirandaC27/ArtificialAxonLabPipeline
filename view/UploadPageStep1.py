# UploadPageStep1.py
from concurrent.futures import thread as futures_thread
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from pathlib import Path
import subprocess
import platform
import threading
import signal
import json
import sys
import os
import shutil

sys.path.append(str(Path(__file__).resolve().parent.parent))
from controller.SessionDataUtil import SessionDataUtil
from controller.runtime_paths import resource_root

sd = SessionDataUtil()
CHANNELS = ['axon', 'myelin', 'nuclei', 'debris', 'GFAP']

class UploadPageStep1(tk.Frame):

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.selected_folders = []
        self.channels = []  # List of dicts: {'num': int, 'label': str, 'disabled': bool}
        self.disabled_fovs = []
        self.stop_flag = False
        self.process = None

        self.build_ui()
        
    def _on_next(self):
        # Save channels BEFORE switching pages
        self.save_folders()

        if self.controller:
            self.controller.show_page("Masking Settings")

    def apply_upload_data(self, config):
        self.selected_folders = []
        self.channels = []
        self.disabled_fovs = []
        self.image_type_var.set("3D")
        self.micro_type_var.set("Keyence")
        self.fov_var.set("")
        self.disable_mode_var.set(False)
        self.status_label.config(text="")
        self.channel_num_entry.delete(0, tk.END)
        self.channel_label_dropdown.set(CHANNELS[0])
        self.fov_disable_entry.delete(0, tk.END)
        self.channel_listbox.delete(0, tk.END)
        self.fov_disabled_listbox.delete(0, tk.END)
        self.toggle_disable_ui()

        self.image_type_var.set(config.get("image_type", "3D"))
        self.micro_type_var.set(config.get("microscope", "Keyence"))

        self.selected_folders = list(config.get("folders", []))
        if self.selected_folders:
            self.status_label.config(text=f"Selected: {len(self.selected_folders)} folders")

        self.fov_var.set(str(config.get("num_fovs", "")) if config.get("num_fovs", 0) else "")

        self.channels = [
            {
                "num": int(ch["num"]),
                "label": str(ch["label"]),
                "disabled": bool(ch.get("disabled", False)),
            }
            for ch in config.get("channels", [])
            if str(ch.get("num", "")).isdigit() and str(ch.get("label", "")).strip()
        ]
        self.channels.sort(key=lambda ch: ch["num"])
        self.update_channel_listbox()

        self.disabled_fovs = [
            str(fov).strip()
            for fov in config.get("disabled_fovs", [])
            if str(fov).strip().isdigit()
        ]
        for fov in self.disabled_fovs:
            self.fov_disabled_listbox.insert(tk.END, f"FOV {fov} Disabled")

        if any(ch.get("disabled") for ch in self.channels) or self.disabled_fovs:
            self.disable_mode_var.set(True)
            self.toggle_disable_ui()

    def build_ui(self):
        # Configure layout: Column 0 (Left), Column 1 (Right)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        
        # Row 12 acts as spacer to push buttons to the bottom
        self.grid_rowconfigure(12, weight=1)

        self.image_type_var = tk.StringVar(value="3D")
        self.micro_type_var = tk.StringVar(value="Keyence")
        self.fov_var = tk.StringVar()
        self.disable_mode_var = tk.BooleanVar(value=False)

        # Top section: Folder selection and settings
        tk.Button(self, text="Add Folder", command=self.add_folder).grid(
            row=0, column=0, columnspan=2, pady=8, sticky="ew", padx=20
        )

        image_frame = tk.LabelFrame(self, text="Image Type")
        image_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        tk.Radiobutton(image_frame, text="2D", variable=self.image_type_var, value="2D").pack(side="left", padx=20)
        tk.Radiobutton(image_frame, text="3D", variable=self.image_type_var, value="3D").pack(side="left", padx=20)

        micro_frame = tk.LabelFrame(self, text="Microscope")
        micro_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        tk.Radiobutton(micro_frame, text="Keyence", variable=self.micro_type_var, value="Keyence").pack(side="left", padx=20)
        tk.Radiobutton(micro_frame, text="Olympus", variable=self.micro_type_var, value="Olympus").pack(side="left", padx=20)

        self.status_label = tk.Label(self, text="", justify="left")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5, padx=20, sticky="w")

        # Left side channel controls
        left_side = tk.Frame(self)
        left_side.grid(row=4, column=0, rowspan=4, sticky="nw", padx=20)

        chan_input = tk.Frame(left_side)
        chan_input.pack(fill="x", anchor="w")
        
        tk.Label(chan_input, text="Channel #:").grid(row=0, column=0)
        self.channel_num_entry = tk.Entry(chan_input, width=6)
        self.channel_num_entry.grid(row=0, column=1, padx=2)

        self.channel_label_var = tk.StringVar()
        self.channel_label_dropdown = ttk.Combobox(chan_input, textvariable=self.channel_label_var, values=CHANNELS, state="readonly", width=8)
        self.channel_label_dropdown.grid(row=0, column=2, padx=2)
        self.channel_label_dropdown.set(CHANNELS[0])

        tk.Label(chan_input, text="# of FOVs:").grid(row=0, column=3, padx=(10, 2))
        tk.Entry(chan_input, textvariable=self.fov_var, width=6).grid(row=0, column=4)

        self.btn_frame = tk.Frame(left_side)
        self.btn_frame.pack(pady=10, fill="x")
        tk.Button(self.btn_frame, text="Add Channel", command=self.add_channel).grid(row=0, column=0, padx=2)
        tk.Button(self.btn_frame, text="Remove Channel", command=self.remove_channel).grid(row=0, column=1, padx=2)
        
        self.disable_ch_btn = tk.Button(self.btn_frame, text="Disable Channel", command=self.toggle_disable_channel)

        self.channel_listbox = tk.Listbox(left_side, width=55, height=4)
        self.channel_listbox.pack(pady=5)

        self.disable_check = tk.Checkbutton(left_side, text="Disable a channel or FOV", 
                                            variable=self.disable_mode_var, 
                                            command=self.toggle_disable_ui)
        self.disable_check.pack(anchor="w", pady=5)

        # Right side FOV disable controls
        self.fov_disable_frame = tk.LabelFrame(self, text="FOV Exclusion")
        self.fov_disable_frame.grid(row=4, column=1, rowspan=4, padx=20, sticky="nsew")
        
        tk.Label(self.fov_disable_frame, text="FOV # to Disable:").pack(pady=2)
        self.fov_disable_entry = tk.Entry(self.fov_disable_frame, width=15)
        self.fov_disable_entry.pack(pady=2)
        tk.Button(self.fov_disable_frame, text="Disable FOV", command=self.add_disabled_fov).pack(pady=2)
        
        tk.Label(self.fov_disable_frame, text="Disabled List:").pack(pady=(10, 0))
        self.fov_disabled_listbox = tk.Listbox(self.fov_disable_frame, width=25, height=4)
        self.fov_disabled_listbox.pack(pady=5, padx=10)
        
        self.fov_disable_frame.grid_remove()

        # Button navigation and run buttons
        tk.Button(self, text="Run", command=self.button_run).grid(row=13, column=0, columnspan=2, pady=10, sticky="ew", padx=20)

        nav_frame = tk.Frame(self)
        nav_frame.grid(row=14, column=0, columnspan=2, pady=(0, 10), padx=20, sticky="ew")
        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=1)

        tk.Button(nav_frame, text="Back", command=lambda: self.controller.show_page("Home")).grid(row=0, column=0, padx=5, sticky="ew")
        tk.Button(nav_frame, text="Next", command=self._on_next).grid(row=0, column=1, padx=5, sticky="ew")

    def toggle_disable_ui(self):
        if self.disable_mode_var.get():
            self.disable_ch_btn.grid(row=0, column=2, padx=2)
            self.fov_disable_frame.grid()
        else:
            self.disable_ch_btn.grid_remove()
            self.fov_disable_frame.grid_remove()

    def add_channel(self):
        num = self.channel_num_entry.get().strip()
        label = self.channel_label_var.get().strip()
        if num.isdigit() and label:
            self.channels.append({"num": int(num), "label": label, "disabled": False})
            self.channels.sort(key=lambda x: x["num"])
            self.update_channel_listbox()

    def toggle_disable_channel(self):
        selection = self.channel_listbox.curselection()
        if selection:
            idx = selection[0]
            self.channels[idx]["disabled"] = not self.channels[idx]["disabled"]
            self.update_channel_listbox()

    def update_channel_listbox(self):
        self.channel_listbox.delete(0, tk.END)
        for i, ch in enumerate(self.channels):
            status = " [DISABLED]" if ch["disabled"] else ""
            self.channel_listbox.insert(tk.END, f"Channel {ch['num']} — {ch['label']}{status}")
            if ch["disabled"]:
                self.channel_listbox.itemconfig(i, {'bg': '#e0e0e0', 'fg': '#a0a0a0'})
            else:
                self.channel_listbox.itemconfig(i, {'bg': 'white', 'fg': 'black'})

    def add_disabled_fov(self):
        val = self.fov_disable_entry.get().strip()
        if val.isdigit() and val not in self.disabled_fovs:
            self.disabled_fovs.append(val)
            self.fov_disabled_listbox.insert(tk.END, f"FOV {val} Disabled")
            self.fov_disable_entry.delete(0, tk.END)

    def remove_channel(self):
        num = self.channel_num_entry.get().strip()
        if num.isdigit():
            self.channels = [ch for ch in self.channels if ch["num"] != int(num)]
            self.update_channel_listbox()

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folders.append(folder)
            self.status_label.config(text=f"Selected: {len(self.selected_folders)} folders")

    def get_num_fovs(self):
        val = self.fov_var.get().strip()
        return int(val) if val.isdigit() else 0

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
        tk.Button(self.popup, text="Stop", command=self.stop_script).pack(pady=10)

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
        if hasattr(self, 'popup') and self.popup.winfo_exists():
            self.progress.stop()
            self.popup.destroy()

    def project_root(self):
        return resource_root()

    def find_bash(self):
        found = shutil.which("bash")
        if found:
            return found

        if platform.system() == "Windows":
            candidates = [
                r"C:\Program Files\Git\bin\bash.exe",
                r"C:\Program Files (x86)\Git\bin\bash.exe",
            ]
            for candidate in candidates:
                if Path(candidate).exists():
                    return candidate

        raise FileNotFoundError(
            "Could not find bash. Install Git for Windows, then try running the upload step again."
        )

    def run_step1(self):
        bash_path = self.find_bash()
        popen_kwargs = {
            "cwd": str(self.project_root()),
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
        }

        if platform.system() == "Windows":
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        elif hasattr(os, "setsid"):
            popen_kwargs["preexec_fn"] = os.setsid

        script_path = self.project_root() / "analysis" / "rename_organize_keyence.sh"

        if not script_path.exists():
            raise FileNotFoundError(f"Script not found at {script_path}")

        self.process = subprocess.Popen(
            [bash_path, str(script_path)],
            **popen_kwargs,
        )

        output, _ = self.process.communicate()

        if self.stop_flag:
            return

        if self.process.returncode != 0:
            tail = "\n".join((output or "").splitlines()[-20:])
            raise RuntimeError(
                f"Upload script failed with exit code {self.process.returncode}.\n\n{tail}"
            )

    def save_folders(self):
        sd.clear_session_files()

        tracks = set()
        data = set()

        for folder in self.selected_folders:
            root = Path(folder)
            if "_RAW" in root.name.upper():
                tracks.add(str(root))
            else:
                data.add(str(root))

        if tracks:
            raw_path = Path(list(tracks)[0])
            clean_path = raw_path.parent / "CLEANED"
        else:
            clean_path = "N/A"

        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        json_data = {
            "Tracks": sorted(tracks),
            "Tracks1": [str(clean_path)] if clean_path != "N/A" else [],
            "OrderedTrack": [str(clean_path.parent / "ORDERED")] if clean_path != "N/A" else [],
            "Data": sorted(data),
            "ImageType": self.image_type_var.get(),
            "Microscope": self.micro_type_var.get(),
            "NumFOVs": self.get_num_fovs(),
            "DisabledFOVs": self.disabled_fovs if self.disabled_fovs else [],
            "Channels": [
                {
                    "code": f"CH{ch['num']}",
                    "label": ch["label"],
                    "active": not ch.get("disabled", False)
                }
                for ch in self.channels
            ],
            "StartTime": start_time
        }

        history = sd.load_session_history()
        json_data["SessionId"] = sd.next_session_id(history["sessions"])

        json_dir = sd.data_dir()
        json_dir.mkdir(parents=True, exist_ok=True)
        json_path = json_dir / "upload_settings.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

    def run_process(self):
        try:
            if not self.selected_folders:
                self.after(0, lambda: (
                    self.status_label.config(text="Please select at least one folder before running."),
                    messagebox.showwarning("Missing Folder", "Please select at least one folder before running.")
                ))
                return

            self.save_folders()
            sd.runtime(self.run_step1)

        except Exception as exc:
            self.after(0, lambda exc=exc: (
                self.status_label.config(text="Upload script failed. See error details."),
                messagebox.showerror("Upload Script Failed", str(exc))
            ))

        finally:
            if self.selected_folders:
                sd.save_end_time()

            self.after(0, self.close_popup)

    def button_run(self):
        self.stop_flag = False
        self.process = None
        self.show_loading_popup()
        
        thread = threading.Thread(target=self.run_process)
        thread.start()
