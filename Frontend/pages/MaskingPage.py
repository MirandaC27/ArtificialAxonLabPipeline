import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from copy import deepcopy

from api_client import save_masking
from state import masking_data, upload_data


THRESHOLD_CHANNELS = ["axon", "myelin", "nuclei", "debris", "GFAP"]
DEFAULT_THRESHOLDS = {"axon": None, "myelin": 8000, "nuclei": None, "debris": 15000, "GFAP": None}


class MaskingPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.base_path_var = tk.StringVar()
        self.well_start_var = tk.StringVar()
        self.well_end_var = tk.StringVar()
        self.particle_min_var = tk.StringVar()
        self.particle_max_var = tk.StringVar()
        self.threshold_vars = {channel: tk.StringVar() for channel in THRESHOLD_CHANNELS}
        self.auto_vars = {channel: tk.BooleanVar() for channel in THRESHOLD_CHANNELS}
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        tk.Label(self, text="Masking Settings", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=(15, 4))
        self.channel_label = tk.Label(self, fg="gray30", justify="left")
        self.channel_label.grid(row=1, column=0, padx=20, sticky="w")

        path_frame = tk.LabelFrame(self, text="Input Directory and Well Range")
        path_frame.grid(row=2, column=0, padx=20, pady=6, sticky="ew")
        path_frame.grid_columnconfigure(1, weight=1)
        tk.Label(path_frame, text="Base path").grid(row=0, column=0, padx=8, pady=5, sticky="w")
        tk.Entry(path_frame, textvariable=self.base_path_var).grid(row=0, column=1, padx=8, pady=5, sticky="ew")
        tk.Button(path_frame, text="Browse...", command=self._browse).grid(row=0, column=2, padx=8, pady=5)
        tk.Label(path_frame, text="Well start").grid(row=1, column=0, padx=8, pady=5, sticky="w")
        tk.Entry(path_frame, textvariable=self.well_start_var, width=8).grid(row=1, column=1, padx=8, pady=5, sticky="w")
        tk.Label(path_frame, text="Well end").grid(row=2, column=0, padx=8, pady=5, sticky="w")
        tk.Entry(path_frame, textvariable=self.well_end_var, width=8).grid(row=2, column=1, padx=8, pady=5, sticky="w")

        threshold_frame = tk.LabelFrame(self, text="Channel Thresholds (0-65535)")
        threshold_frame.grid(row=3, column=0, padx=20, pady=6, sticky="ew")
        tk.Label(threshold_frame, text="Channel").grid(row=0, column=0, padx=8)
        tk.Label(threshold_frame, text="Threshold").grid(row=0, column=1, padx=8)
        tk.Label(threshold_frame, text="Auto").grid(row=0, column=2, padx=8)
        for row, channel in enumerate(THRESHOLD_CHANNELS, start=1):
            tk.Label(threshold_frame, text=channel).grid(row=row, column=0, padx=8, pady=3, sticky="w")
            tk.Entry(threshold_frame, textvariable=self.threshold_vars[channel], width=12).grid(row=row, column=1, padx=8, pady=3)
            tk.Checkbutton(threshold_frame, variable=self.auto_vars[channel]).grid(row=row, column=2, padx=8, pady=3)

        particle_frame = tk.LabelFrame(self, text="Myelin Particle Size (px²)")
        particle_frame.grid(row=4, column=0, padx=20, pady=6, sticky="ew")
        tk.Label(particle_frame, text="Minimum").grid(row=0, column=0, padx=8, pady=5)
        tk.Entry(particle_frame, textvariable=self.particle_min_var, width=10).grid(row=0, column=1, padx=8, pady=5)
        tk.Label(particle_frame, text="Maximum").grid(row=0, column=2, padx=8, pady=5)
        tk.Entry(particle_frame, textvariable=self.particle_max_var, width=10).grid(row=0, column=3, padx=8, pady=5)

        self.status_label = tk.Label(self, text="", fg="gray30")
        self.status_label.grid(row=5, column=0, padx=20, pady=4)
        nav = tk.Frame(self)
        nav.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        nav.grid_columnconfigure((0, 1), weight=1)
        tk.Button(nav, text="Back", command=lambda: self.controller.show_page("Settings")).grid(row=0, column=0, padx=5, sticky="ew")
        tk.Button(nav, text="Next", command=self._on_next).grid(row=0, column=1, padx=5, sticky="ew")

    def refresh(self):
        base_path = masking_data.get("base_path", "")
        if not base_path:
            ordered = upload_data.get("ordered_track") or []
            base_path = ordered[0] if ordered else ""
        self.base_path_var.set(base_path)
        self.well_start_var.set(str(masking_data.get("well_start", 2)))
        self.well_end_var.set(str(masking_data.get("well_end", 11)))
        thresholds = masking_data.get("thresholds", {})
        autos = masking_data.get("auto_thresholds", {})
        for channel in THRESHOLD_CHANNELS:
            value = thresholds.get(channel, DEFAULT_THRESHOLDS[channel])
            self.threshold_vars[channel].set("" if value is None else str(value))
            self.auto_vars[channel].set(bool(autos.get(channel, False)))
        particle = masking_data.get("particle_size", {})
        self.particle_min_var.set(str(particle.get("min", 2)))
        self.particle_max_var.set(str(particle.get("max", 2000)))
        channels = upload_data.get("channels") or []
        labels = [f"{item.get('code', 'CH?')}: {item.get('label', '')}" for item in channels if isinstance(item, dict)]
        self.channel_label.config(text="Channels: " + (", ".join(labels) if labels else "None"))

    def _browse(self):
        selected = filedialog.askdirectory(parent=self, title="Select masking base path")
        if selected:
            self.base_path_var.set(selected)

    def collect_state(self):
        base_path = self.base_path_var.get().strip()
        if not base_path:
            raise ValueError("Base path is required.")
        try:
            well_start = int(self.well_start_var.get())
            well_end = int(self.well_end_var.get())
            particle_min = int(self.particle_min_var.get())
            particle_max = int(self.particle_max_var.get())
        except ValueError as exc:
            raise ValueError("Wells and particle sizes must be whole numbers.") from exc
        if well_start > well_end:
            raise ValueError("Well start cannot be greater than well end.")
        if particle_min < 0 or particle_max < particle_min:
            raise ValueError("Particle size range is invalid.")
        thresholds = {}
        autos = {}
        for channel in THRESHOLD_CHANNELS:
            auto = self.auto_vars[channel].get()
            raw = self.threshold_vars[channel].get().strip()
            if auto:
                value = None
            elif raw == "":
                value = None
            else:
                try:
                    value = int(raw)
                except ValueError as exc:
                    raise ValueError(f"{channel} threshold must be a whole number.") from exc
                if not 0 <= value <= 65535:
                    raise ValueError(f"{channel} threshold must be between 0 and 65535.")
            thresholds[channel] = value
            autos[channel] = auto
        return {
            "base_path": base_path,
            "well_start": well_start,
            "well_end": well_end,
            "thresholds": thresholds,
            "auto_thresholds": autos,
            "particle_size": {"min": particle_min, "max": particle_max},
        }

    def _on_next(self):
        try:
            collected = self.collect_state()
            masking_data.clear()
            masking_data.update(deepcopy(collected))
            save_masking(dict(masking_data))
            self.status_label.config(text="Masking settings saved.", fg="green")
            self.controller.show_page("TestSave")
        except Exception as exc:
            messagebox.showerror("Masking Settings Error", str(exc))


MaskingSettingsPage = MaskingPage