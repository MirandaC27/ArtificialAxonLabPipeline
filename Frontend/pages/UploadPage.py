import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import subprocess
import platform
import threading
import signal
import os

from state import upload_data


CHANNELS = ["axon", "myelin", "nuclei", "debris", "GFAP"]


class UploadPage(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller

        self.selected_folders = []
        self.channels = []
        self.disabled_fovs = []

        self.stop_flag = False
        self.process = None

        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(12, weight=1)

        self.image_type_var = tk.StringVar(value="3D")
        self.micro_type_var = tk.StringVar(value="Keyence")
        self.fov_var = tk.StringVar()
        self.disable_mode_var = tk.BooleanVar(value=False)

        tk.Button(
            self,
            text="Add Folder",
            command=self.add_folder
        ).grid(row=0, column=0, columnspan=2, pady=8, sticky="ew", padx=20)

        image_frame = tk.LabelFrame(self, text="Image Type")
        image_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

        tk.Radiobutton(
            image_frame,
            text="2D",
            variable=self.image_type_var,
            value="2D"
        ).pack(side="left", padx=20)

        tk.Radiobutton(
            image_frame,
            text="3D",
            variable=self.image_type_var,
            value="3D"
        ).pack(side="left", padx=20)

        micro_frame = tk.LabelFrame(self, text="Microscope")
        micro_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

        tk.Radiobutton(
            micro_frame,
            text="Keyence",
            variable=self.micro_type_var,
            value="Keyence"
        ).pack(side="left", padx=20)

        tk.Radiobutton(
            micro_frame,
            text="Olympus",
            variable=self.micro_type_var,
            value="Olympus"
        ).pack(side="left", padx=20)

        self.status_label = tk.Label(self, text="", justify="left")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5, padx=20, sticky="w")

        left_side = tk.Frame(self)
        left_side.grid(row=4, column=0, rowspan=4, sticky="nw", padx=20)

        chan_input = tk.Frame(left_side)
        chan_input.pack(fill="x", anchor="w")

        tk.Label(chan_input, text="Channel #:").grid(row=0, column=0)

        self.channel_num_entry = tk.Entry(chan_input, width=6)
        self.channel_num_entry.grid(row=0, column=1, padx=2)

        self.channel_label_var = tk.StringVar()

        self.channel_label_dropdown = ttk.Combobox(
            chan_input,
            textvariable=self.channel_label_var,
            values=CHANNELS,
            state="readonly",
            width=8
        )
        self.channel_label_dropdown.grid(row=0, column=2, padx=2)
        self.channel_label_dropdown.set(CHANNELS[0])

        tk.Label(chan_input, text="# of FOVs:").grid(row=0, column=3, padx=(10, 2))

        tk.Entry(
            chan_input,
            textvariable=self.fov_var,
            width=6
        ).grid(row=0, column=4)

        self.btn_frame = tk.Frame(left_side)
        self.btn_frame.pack(pady=10, fill="x")

        tk.Button(
            self.btn_frame,
            text="Add Channel",
            command=self.add_channel
        ).grid(row=0, column=0, padx=2)

        tk.Button(
            self.btn_frame,
            text="Remove Channel",
            command=self.remove_channel
        ).grid(row=0, column=1, padx=2)

        self.disable_ch_btn = tk.Button(
            self.btn_frame,
            text="Disable Channel",
            command=self.toggle_disable_channel
        )

        self.channel_listbox = tk.Listbox(left_side, width=55, height=4)
        self.channel_listbox.pack(pady=5)

        self.disable_check = tk.Checkbutton(
            left_side,
            text="Disable a channel or FOV",
            variable=self.disable_mode_var,
            command=self.toggle_disable_ui
        )
        self.disable_check.pack(anchor="w", pady=5)

        self.fov_disable_frame = tk.LabelFrame(self, text="FOV Exclusion")
        self.fov_disable_frame.grid(row=4, column=1, rowspan=4, padx=20, sticky="nsew")

        tk.Label(
            self.fov_disable_frame,
            text="FOV # to Disable:"
        ).pack(pady=2)

        self.fov_disable_entry = tk.Entry(self.fov_disable_frame, width=15)
        self.fov_disable_entry.pack(pady=2)

        tk.Button(
            self.fov_disable_frame,
            text="Disable FOV",
            command=self.add_disabled_fov
        ).pack(pady=2)

        tk.Label(
            self.fov_disable_frame,
            text="Disabled List:"
        ).pack(pady=(10, 0))

        self.fov_disabled_listbox = tk.Listbox(self.fov_disable_frame, width=25, height=4)
        self.fov_disabled_listbox.pack(pady=5, padx=10)

        self.fov_disable_frame.grid_remove()

        tk.Button(
            self,
            text="Run",
            command=self.button_run
        ).grid(row=13, column=0, columnspan=2, pady=10, sticky="ew", padx=20)

        nav_frame = tk.Frame(self)
        nav_frame.grid(row=14, column=0, columnspan=2, pady=(0, 10), padx=20, sticky="ew")

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
            command=self._on_next
        ).grid(row=0, column=1, padx=5, sticky="ew")

    def refresh(self):
        self.channel_num_entry.delete(0, tk.END)
        self.fov_disable_entry.delete(0, tk.END)
        self.channel_label_var.set(CHANNELS[0])
        self.disable_mode_var.set(False)
        self.toggle_disable_ui()

        self.image_type_var.set(upload_data["image_type"])
        self.micro_type_var.set(upload_data["microscope"])
        self.fov_var.set(str(upload_data["num_fovs"]) if upload_data["num_fovs"] else "")

        self.selected_folders = list(upload_data["folders"])
        self.disabled_fovs = list(upload_data["disabled_fovs"])

        self.channels = []
        for ch in upload_data["channels"]:
            code = ch.get("code", "CH0").replace("CH", "")
            if code.isdigit():
                self.channels.append({
                    "num": int(code),
                    "label": ch.get("label", ""),
                    "disabled": not ch.get("active", True)
                })

        self.status_label.config(
            text=f"Selected: {len(self.selected_folders)} folders"
            if self.selected_folders else ""
        )

        self.update_channel_listbox()

        self.fov_disabled_listbox.delete(0, tk.END)
        for fov in self.disabled_fovs:
            self.fov_disabled_listbox.insert(tk.END, f"FOV {fov} Disabled")

    def _on_next(self):
        try:
            if not self.selected_folders:
                raise ValueError("Please select at least one folder.")

            self.save_current_state()

            if self.controller:
                self.controller.show_page("Settings")

        except Exception as e:
            messagebox.showerror("Upload Error", str(e))

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
            self.channels.append({
                "num": int(num),
                "label": label,
                "disabled": False
            })

            self.channels.sort(key=lambda x: x["num"])
            self.update_channel_listbox()
            self.channel_num_entry.delete(0, tk.END)

    def remove_channel(self):
        num = self.channel_num_entry.get().strip()

        if num.isdigit():
            self.channels = [
                ch for ch in self.channels
                if ch["num"] != int(num)
            ]

            self.update_channel_listbox()
            self.channel_num_entry.delete(0, tk.END)

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

            self.channel_listbox.insert(
                tk.END,
                f"Channel {ch['num']} — {ch['label']}{status}"
            )

            if ch["disabled"]:
                self.channel_listbox.itemconfig(
                    i,
                    {"bg": "#e0e0e0", "fg": "#a0a0a0"}
                )
            else:
                self.channel_listbox.itemconfig(
                    i,
                    {"bg": "white", "fg": "black"}
                )

    def add_disabled_fov(self):
        val = self.fov_disable_entry.get().strip()

        if val.isdigit() and val not in self.disabled_fovs:
            self.disabled_fovs.append(val)
            self.fov_disabled_listbox.insert(tk.END, f"FOV {val} Disabled")
            self.fov_disable_entry.delete(0, tk.END)

    def add_folder(self):
        folder = filedialog.askdirectory()

        if folder:
            self.selected_folders.append(folder)
            self.status_label.config(
                text=f"Selected: {len(self.selected_folders)} folders"
            )

    def get_num_fovs(self):
        val = self.fov_var.get().strip()
        return int(val) if val.isdigit() else 0

    def save_current_state(self):
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
            ordered_path = clean_path.parent / "ORDERED"

            tracks1 = [str(clean_path)]
            ordered_track = [str(ordered_path)]
        else:
            tracks1 = []
            ordered_track = []

        upload_data["folders"] = list(self.selected_folders)
        upload_data["tracks"] = sorted(tracks)
        upload_data["tracks1"] = tracks1
        upload_data["ordered_track"] = ordered_track
        upload_data["data"] = sorted(data)

        upload_data["image_type"] = self.image_type_var.get()
        upload_data["microscope"] = self.micro_type_var.get()
        upload_data["num_fovs"] = self.get_num_fovs()

        upload_data["disabled_fovs"] = list(self.disabled_fovs)

        upload_data["channels"] = [
            {
                "code": f"CH{ch['num']}",
                "label": ch["label"],
                "active": not ch.get("disabled", False)
            }
            for ch in self.channels
        ]

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

        tk.Button(
            self.popup,
            text="Stop",
            command=self.stop_script
        ).pack(pady=10)

    def stop_script(self):
        self.stop_flag = True

        if self.process:
            try:
                if platform.system() == "Windows":
                    subprocess.call([
                        "taskkill",
                        "/F",
                        "/T",
                        "/PID",
                        str(self.process.pid)
                    ])
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except Exception as e:
                print("Error stopping process:", e)

    def close_popup(self):
        if hasattr(self, "popup") and self.popup.winfo_exists():
            self.progress.stop()
            self.popup.destroy()

    def build_step1_args(self):
        active_channels = [
            channel for channel in upload_data["channels"]
            if channel.get("active", True)
        ]

        channel_codes = "|".join(
            channel.get("code", "") for channel in active_channels
        )
        channel_labels = "|".join(
            channel.get("label", "") for channel in active_channels
        )
        disabled_fovs = ",".join(str(fov) for fov in upload_data["disabled_fovs"])

        return [
            upload_data["tracks"][0] if upload_data["tracks"] else "",
            upload_data["tracks1"][0] if upload_data["tracks1"] else "",
            upload_data["ordered_track"][0] if upload_data["ordered_track"] else "",
            upload_data["data"][0] if upload_data["data"] else "",
            upload_data["image_type"],
            upload_data["microscope"],
            str(upload_data["num_fovs"]),
            disabled_fovs,
            channel_codes,
            channel_labels,
        ]

    def run_step1(self):
        if platform.system() == "Windows":
            bash_path = r"C:\Program Files\Git\bin\bash.exe"
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            preexec_fn = None
        else:
            bash_path = "/bin/bash"
            creationflags = 0
            preexec_fn = os.setsid

        script_path = (
            Path(__file__).resolve().parents[2]
            / "backend"
            / "scripts"
            / "rename_organize_keyence.sh"
        )

        if not script_path.exists():
            print(f"Error: Script not found at {script_path}")
            return

        self.process = subprocess.Popen(
            [bash_path, str(script_path), *self.build_step1_args()],
            creationflags=creationflags,
            preexec_fn=preexec_fn
        )

        while self.process.poll() is None:
            if self.stop_flag:
                break
            
    def run_process(self):
       try:
           if not self.selected_folders:
               raise ValueError("Please select at least one folder.")

           self.save_current_state()
           self.run_step1()

       except Exception as e:
           error_message = str(e)

           self.after(
               0,
               lambda message=error_message:
               self.status_label.config(text=f"Error: {message}")
           )

       finally:
           self.after(0, self.close_popup)

    def button_run(self):
        self.stop_flag = False
        self.process = None

        self.show_loading_popup()

        thread = threading.Thread(target=self.run_process)
        thread.start()