# masking_front.py
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
import sys
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from analysis.masking import main as run_masking


THRESHOLD_CHANNELS = ["axon", "myelin", "nuclei", "debris", "GFAP"]

DEFAULT_THRESHOLDS = {
    "myelin": 8000,
    "debris": 15000,
}

CONFIG_PATH = PROJECT_ROOT / "data" / "upload_settings.json"

if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {}

DEFAULT_BASE_PATH = Path(data.get("OrderedTrack", [""])[0]) if data.get("OrderedTrack") else Path("")

DEFAULT_WELL_START = 2
DEFAULT_WELL_END = 11

DEFAULT_PARTICLE_SIZE_MIN = 2
DEFAULT_PARTICLE_SIZE_MAX = 2000

THRESH_MIN = 0
THRESH_MAX = 65535


class MaskingSettingsPage(tk.Frame):

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller

        self.threshold_vars = {}
        self.auto_vars = {}

        self.particle_size_min_var = tk.StringVar(value=str(DEFAULT_PARTICLE_SIZE_MIN))
        self.particle_size_max_var = tk.StringVar(value=str(DEFAULT_PARTICLE_SIZE_MAX))

        self.base_path_var = tk.StringVar(value=str(DEFAULT_BASE_PATH))
        self.well_start_var = tk.StringVar(value=str(DEFAULT_WELL_START))
        self.well_end_var = tk.StringVar(value=str(DEFAULT_WELL_END))

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        tk.Label(
            self,
            text="Masking Settings",
            font=("TkDefaultFont", 13, "bold"),
        ).grid(row=0, column=0, pady=(16, 4), padx=20, sticky="w")

        tk.Label(
            self,
            text="Set intensity thresholds for each channel mask.",
            justify="left",
            fg="gray40",
        ).grid(row=1, column=0, padx=20, sticky="w")

        self.status_label = tk.Label(self, text="", justify="left", fg="gray30")
        self.status_label.grid(row=2, column=0, pady=(0, 6), padx=20, sticky="w")

        self.channel_display_label = tk.Label(
            self,
            text="Channels: (not loaded)",
            justify="left",
            fg="gray30",
        )
        self.channel_display_label.grid(row=3, column=0, padx=20, sticky="e")
        self.load_channels_from_upload()

        path_frame = tk.LabelFrame(self, text="Input Directory & Well Range")
        path_frame.grid(row=4, column=0, padx=20, sticky="ew")
        path_frame.grid_columnconfigure(1, weight=1)

        tk.Label(path_frame, text="Base path", width=12, anchor="w").grid(
            row=0, column=0, padx=(10, 8), pady=8, sticky="w"
        )

        tk.Entry(path_frame, textvariable=self.base_path_var).grid(
            row=0, column=1, padx=(0, 6), pady=8, sticky="ew"
        )

        tk.Button(
            path_frame,
            text="Browse…",
            command=self._browse_base_path,
        ).grid(row=0, column=2, padx=(0, 10), pady=8)

        tk.Label(path_frame, text="Well start", width=12, anchor="w").grid(
            row=1, column=0, padx=(10, 8), pady=(0, 8), sticky="w"
        )

        tk.Entry(path_frame, textvariable=self.well_start_var, width=6).grid(
            row=1, column=1, padx=(0, 6), pady=(0, 8), sticky="w"
        )

        tk.Label(path_frame, text="Well end", width=12, anchor="w").grid(
            row=2, column=0, padx=(10, 8), pady=(0, 8), sticky="w"
        )

        tk.Entry(path_frame, textvariable=self.well_end_var, width=6).grid(
            row=2, column=1, padx=(0, 6), pady=(0, 8), sticky="w"
        )

        tk.Label(path_frame, text="(inclusive)", fg="gray40").grid(
            row=2, column=2, padx=(0, 10), pady=(0, 8), sticky="w"
        )

        thresh_frame = tk.LabelFrame(self, text="Channel Thresholds")
        thresh_frame.grid(row=5, column=0, padx=20, pady=6, sticky="ew")

        tk.Label(
            thresh_frame,
            text="Channel",
            font=("TkDefaultFont", 9, "bold"),
            width=10,
            anchor="w",
        ).grid(row=0, column=0, padx=(10, 20), pady=(6, 2), sticky="w")

        tk.Label(
            thresh_frame,
            text="Low Threshold (0 – 65535)",
            font=("TkDefaultFont", 9, "bold"),
        ).grid(row=0, column=1, pady=(6, 2), sticky="w")

        tk.Label(
            thresh_frame,
            text="Auto",
            font=("TkDefaultFont", 9, "bold"),
        ).grid(row=0, column=3, padx=(10, 10), pady=(6, 2), sticky="w")

        ttk.Separator(thresh_frame, orient="horizontal").grid(
            row=1, column=0, columnspan=5, sticky="ew", padx=8, pady=2
        )

        for idx, channel in enumerate(THRESHOLD_CHANNELS):
            row = idx + 2

            thresh_var = tk.StringVar(value=str(DEFAULT_THRESHOLDS.get(channel, "")))
            auto_var = tk.BooleanVar(value=False)

            self.threshold_vars[channel] = thresh_var
            self.auto_vars[channel] = auto_var

            tk.Label(
                thresh_frame,
                text=channel.capitalize(),
                width=10,
                anchor="w",
            ).grid(row=row, column=0, padx=(10, 20), pady=6, sticky="w")

            tk.Entry(
                thresh_frame,
                textvariable=thresh_var,
                width=10,
            ).grid(row=row, column=1, padx=(0, 10), pady=6, sticky="w")

            default_val = DEFAULT_THRESHOLDS.get(channel, "")

            tk.Button(
                thresh_frame,
                text="Reset",
                width=6,
                command=lambda c=channel, d=default_val: self._reset_channel(c, d),
            ).grid(row=row, column=2, padx=(0, 10), pady=6)

            tk.Checkbutton(
                thresh_frame,
                variable=auto_var,
            ).grid(row=row, column=3, padx=(10, 10), pady=6)

        particle_frame = tk.LabelFrame(
            self,
            text="Particle Analysis Size Filter (Myelin only)",
        )
        particle_frame.grid(row=6, column=0, padx=20, pady=6, sticky="ew")

        tk.Label(
            particle_frame,
            text="Size (px²)",
            font=("TkDefaultFont", 9, "bold"),
            width=10,
            anchor="w",
        ).grid(row=0, column=0, padx=(10, 20), pady=(6, 2), sticky="w")

        tk.Label(
            particle_frame,
            text="Value",
            font=("TkDefaultFont", 9, "bold"),
        ).grid(row=0, column=1, pady=(6, 2), sticky="w")

        ttk.Separator(particle_frame, orient="horizontal").grid(
            row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=2
        )

        tk.Label(particle_frame, text="Minimum", width=10, anchor="w").grid(
            row=2, column=0, padx=(10, 20), pady=6, sticky="w"
        )

        tk.Entry(
            particle_frame,
            textvariable=self.particle_size_min_var,
            width=10,
        ).grid(row=2, column=1, padx=(0, 10), pady=6, sticky="w")

        tk.Button(
            particle_frame,
            text="Reset",
            width=6,
            command=lambda: self._reset_particle_size("min"),
        ).grid(row=2, column=2, padx=(0, 10), pady=6)

        tk.Label(particle_frame, text="Maximum", width=10, anchor="w").grid(
            row=3, column=0, padx=(10, 20), pady=6, sticky="w"
        )

        tk.Entry(
            particle_frame,
            textvariable=self.particle_size_max_var,
            width=10,
        ).grid(row=3, column=1, padx=(0, 10), pady=6, sticky="w")

        tk.Button(
            particle_frame,
            text="Reset",
            width=6,
            command=lambda: self._reset_particle_size("max"),
        ).grid(row=3, column=2, padx=(0, 10), pady=6)

        action_frame = tk.Frame(self)
        action_frame.grid(row=7, column=0, pady=(8, 4), padx=20, sticky="w")

        tk.Button(
            action_frame,
            text="Reset All to Defaults",
            command=self._reset_all,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            action_frame,
            text="Apply Settings",
            command=self.save_settings_to_json,
        ).pack(side="left")

        tk.Button(
            self,
            text="Run Masking",
            command=self._run_masking,
            bg="black",
            fg="white",
            font=("TkDefaultFont", 10, "bold"),
            relief="flat",
            padx=12,
            pady=8,
        ).grid(row=8, column=0, pady=(10, 4), padx=20, sticky="ew")

        nav_frame = tk.Frame(self)
        nav_frame.grid(row=9, column=0, pady=12, padx=20, sticky="ew")
        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=1)

        tk.Button(
            nav_frame,
            text="Back",
            command=lambda: self.controller.show_page("Settings") if self.controller else None,
        ).grid(row=0, column=0, padx=5, sticky="ew")

        tk.Button(
            nav_frame,
            text="Next",
            command=self._on_next,
        ).grid(row=0, column=1, padx=5, sticky="ew")

        self.results_button = tk.Button(
            self,
            text="Go to Results",
            command=lambda: self.controller.show_page("Results") if self.controller else None,
            state="disabled",
            bg="#000000",
            fg="white",
            font=("TkDefaultFont", 10, "bold"),
            relief="flat",
            padx=12,
            pady=8,
        )

        self.results_button.grid(row=10, column=0, pady=(4, 10), padx=20, sticky="ew")

    def _run_masking(self):
        self.load_channels_from_upload()

        settings, errors = self._collect_settings()
        if errors:
            self.status_label.config(text=" | ".join(errors), fg="red")
            return

        if not self.save_settings_to_json():
            return

        self.status_label.config(text="Running masking...", fg="blue")
        self.update_idletasks()

        try:
            run_masking()
            self.status_label.config(text="Masking complete.", fg="green")
            self.results_button.config(state="normal")
        except Exception as e:
            self.status_label.config(text=f"Error: {e}", fg="red")

    def _browse_base_path(self):
        initial = str(self.base_path_var.get() or DEFAULT_BASE_PATH or Path.cwd())
        selected = filedialog.askdirectory(
            parent=self,
            initialdir=initial,
            title="Select Base Path",
        )
        if selected:
            self.base_path_var.set(selected)
            self.status_label.config(text=f"Base path set to: {selected}", fg="green")

    def _reset_channel(self, channel, default):
        self.auto_vars[channel].set(False)
        self.threshold_vars[channel].set(str(default))
        self.status_label.config(text=f"{channel.capitalize()} reset to {default}.")

    def _reset_particle_size(self, which):
        if which == "min":
            self.particle_size_min_var.set(str(DEFAULT_PARTICLE_SIZE_MIN))
            self.status_label.config(
                text=f"Minimum particle size reset to {DEFAULT_PARTICLE_SIZE_MIN}."
            )
        else:
            self.particle_size_max_var.set(str(DEFAULT_PARTICLE_SIZE_MAX))
            self.status_label.config(
                text=f"Maximum particle size reset to {DEFAULT_PARTICLE_SIZE_MAX}."
            )

    def _reset_all(self):
        self.base_path_var.set(str(DEFAULT_BASE_PATH))
        self.well_start_var.set(str(DEFAULT_WELL_START))
        self.well_end_var.set(str(DEFAULT_WELL_END))

        for channel in THRESHOLD_CHANNELS:
            self.auto_vars[channel].set(False)
            default = DEFAULT_THRESHOLDS.get(channel, "")
            self.threshold_vars[channel].set(str(default))

        self.particle_size_min_var.set(str(DEFAULT_PARTICLE_SIZE_MIN))
        self.particle_size_max_var.set(str(DEFAULT_PARTICLE_SIZE_MAX))
        self.status_label.config(text="All values reset to defaults.")

    def _collect_settings(self):
        base_path = self.get_base_path()
        well_range = self.get_well_range()
        thresholds = self.get_thresholds()
        particle = self.get_particle_size()

        errors = []
        if not base_path:
            errors.append("Base path is required.")
        if well_range is None:
            errors.append("Well start/end must be integers.")

        if errors:
            return None, errors

        return (
            {
                "base_path": base_path,
                "well_range": well_range,
                "thresholds": thresholds,
                "particle_size": particle,
            },
            None,
        )

    def set_base_path(self, path):
        self.base_path_var.set(str(path))

    def load_channels_from_upload(self):
        config_path = PROJECT_ROOT / "data" / "upload_settings.json"

        if not config_path.exists():
            self.channel_display_label.config(text="Channels: (no upload data)")
            return

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        channels = data.get("Channels", [])
        self.set_channels(channels)

        print("Loading channels from:", config_path)
        print("Channels found:", channels)

    def set_channels(self, channels):
        if not channels:
            self.channel_display_label.config(text="Channels: (none)")
            return

        formatted = []

        for ch in channels:
            label = ch.get("label", "").lower()
            code = ch.get("code", "CH?")
            active = ch.get("active", True)

            status = "" if active else " (disabled)"
            formatted.append(f"{code}: {label}{status}")

        display_text = "Channels:\n" + "\n".join(formatted)
        self.channel_display_label.config(text=display_text)

    def get_base_path(self):
        raw = self.base_path_var.get().strip()
        return Path(raw) if raw else None

    def get_well_range(self):
        try:
            start = int(self.well_start_var.get().strip())
            end = int(self.well_end_var.get().strip())
            return range(start, end + 1)
        except ValueError:
            return None

    def get_thresholds(self):
        result = {}

        for ch, var in self.threshold_vars.items():
            if self.auto_vars[ch].get():
                result[ch] = "auto"
            else:
                raw = var.get().strip()
                result[ch] = int(raw) if raw.lstrip("-").isdigit() else None

        return result

    def get_particle_size(self):
        result = {}

        for key, var in (
            ("min", self.particle_size_min_var),
            ("max", self.particle_size_max_var),
        ):
            raw = var.get().strip()
            result[key] = int(raw) if raw.lstrip("-").isdigit() else None

        return result

    def save_settings_to_json(self):
        settings, errors = self._collect_settings()
        if errors:
            self.status_label.config(text=" | ".join(errors), fg="red")
            return False

        serializable = {
            "base_path": str(settings["base_path"]),
            "well_start": settings["well_range"].start,
            "well_end": settings["well_range"].stop - 1,
            "thresholds": settings["thresholds"],
            "particle_size": settings["particle_size"],
        }

        save_path = PROJECT_ROOT / "data" / "masking_settings.json"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=4)

        self.status_label.config(text=f"Settings saved to {save_path.name}", fg="green")
        return True

    def refresh_base_path(self):
        config_path = PROJECT_ROOT / "data" / "upload_settings.json"

        if not config_path.exists():
            return

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ordered = data.get("OrderedTrack", [])

        if ordered:
            self.base_path_var.set(str(Path(ordered[0])))
            self.status_label.config(text=f"Loaded base path: {ordered[0]}")

    def _on_next(self):
        self.load_channels_from_upload()

        if self.controller:
            self.controller.show_page("SessionEnd")


def save_settings_file(settings, path):
    serializable = {
        "base_path": str(settings["base_path"]),
        "well_start": settings["well_range"].start,
        "well_end": settings["well_range"].stop - 1,
        "thresholds": settings["thresholds"],
        "particle_size": settings["particle_size"],
    }

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=4)


def collect_settings():
    result_holder = {}

    root = tk.Tk()
    root.title("Masking Settings")
    root.geometry("520x700")
    root.resizable(False, True)

    page = MaskingSettingsPage(root, controller=None)
    page.pack(fill="both", expand=True)

    def on_run():
        base_path = page.get_base_path()
        well_range = page.get_well_range()
        thresholds = page.get_thresholds()
        particle = page.get_particle_size()

        errors = []

        if not base_path:
            errors.append("Base path is required.")

        if well_range is None:
            errors.append("Well start/end must be integers.")

        if errors:
            page.status_label.config(text=" | ".join(errors), fg="red")
            return

        result_holder["base_path"] = base_path
        result_holder["well_range"] = well_range
        result_holder["thresholds"] = thresholds
        result_holder["particle_size"] = particle

        settings = result_holder.copy()
        save_path = PROJECT_ROOT / "data" / "masking_settings.json"
        save_settings_file(settings, save_path)

        root.destroy()

    btn_frame = tk.Frame(root)
    btn_frame.pack(fill="x", padx=20, pady=(0, 12))

    tk.Button(
        btn_frame,
        text="Run Masking",
        command=on_run,
        bg="#2d7d46",
        fg="white",
        font=("TkDefaultFont", 10, "bold"),
        relief="flat",
        padx=12,
        pady=6,
    ).pack(fill="x")

    root.mainloop()

    return result_holder if result_holder else None


if __name__ == "__main__":
    settings = collect_settings()

    if settings:
        print("Base path:    ", settings["base_path"])
        print("Well range:   ", settings["well_range"])
        print("Thresholds:   ", settings["thresholds"])
        print("Particle size:", settings["particle_size"])
    else:
        print("Cancelled.")