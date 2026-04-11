import tkinter as tk
from tkinter import ttk
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))


THRESHOLD_CHANNELS = ['axon', 'myelin', 'nuclei', 'debris']

DEFAULT_THRESHOLDS = {
    "myelin": 8000,
    "debris": 15000,
}

# Defaults pulled from analyze_particles() in Masking.py
DEFAULT_PARTICLE_SIZE_MIN = 2
DEFAULT_PARTICLE_SIZE_MAX = 2000

THRESH_MIN = 0
THRESH_MAX = 65535


class MaskingSettingsPage(tk.Frame):

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller

        self.threshold_vars: dict[str, tk.StringVar] = {}
        self.particle_size_min_var = tk.StringVar(value=str(DEFAULT_PARTICLE_SIZE_MIN))
        self.particle_size_max_var = tk.StringVar(value=str(DEFAULT_PARTICLE_SIZE_MAX))

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

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
        ).grid(row=1, column=0, pady=(0, 10), padx=20, sticky="w")

        # Status label
        self.status_label = tk.Label(self, text="", justify="left", fg="gray30")
        self.status_label.grid(row=2, column=0, pady=(0, 6), padx=20, sticky="w")

        # ── Threshold section ──────────────────────────────────────────
        thresh_frame = tk.LabelFrame(self, text="Channel Thresholds")
        thresh_frame.grid(row=3, column=0, padx=20, pady=6, sticky="ew")

        tk.Label(thresh_frame, text="Channel", font=("TkDefaultFont", 9, "bold"), width=10, anchor="w").grid(
            row=0, column=0, padx=(10, 20), pady=(6, 2), sticky="w"
        )
        tk.Label(thresh_frame, text="Low Threshold (0 – 65535)", font=("TkDefaultFont", 9, "bold")).grid(
            row=0, column=1, pady=(6, 2), sticky="w"
        )

        ttk.Separator(thresh_frame, orient="horizontal").grid(
            row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=2
        )

        for idx, channel in enumerate(THRESHOLD_CHANNELS):
            row = idx + 2
            var = tk.StringVar(value=str(DEFAULT_THRESHOLDS.get(channel, "")))
            self.threshold_vars[channel] = var

            tk.Label(thresh_frame, text=channel.capitalize(), width=10, anchor="w").grid(
                row=row, column=0, padx=(10, 20), pady=6, sticky="w"
            )

            tk.Entry(thresh_frame, textvariable=var, width=10).grid(
                row=row, column=1, padx=(0, 10), pady=6, sticky="w"
            )

            default_val = DEFAULT_THRESHOLDS.get(channel, "")
            tk.Button(
                thresh_frame,
                text="Reset",
                width=6,
                command=lambda c=channel, d=default_val: self._reset_channel(c, d),
            ).grid(row=row, column=2, padx=(0, 10), pady=6)

        # ── Particle Size section ──────────────────────────────────────
        particle_frame = tk.LabelFrame(self, text="Particle Analysis Size Filter")
        particle_frame.grid(row=4, column=0, padx=20, pady=6, sticky="ew")

        tk.Label(particle_frame, text="Size (px²)", font=("TkDefaultFont", 9, "bold"), width=10, anchor="w").grid(
            row=0, column=0, padx=(10, 20), pady=(6, 2), sticky="w"
        )
        tk.Label(particle_frame, text="Value", font=("TkDefaultFont", 9, "bold")).grid(
            row=0, column=1, pady=(6, 2), sticky="w"
        )

        ttk.Separator(particle_frame, orient="horizontal").grid(
            row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=2
        )

        # Min row
        tk.Label(particle_frame, text="Minimum", width=10, anchor="w").grid(
            row=2, column=0, padx=(10, 20), pady=6, sticky="w"
        )
        tk.Entry(particle_frame, textvariable=self.particle_size_min_var, width=10).grid(
            row=2, column=1, padx=(0, 10), pady=6, sticky="w"
        )
        tk.Button(
            particle_frame,
            text="Reset",
            width=6,
            command=lambda: self._reset_particle_size("min"),
        ).grid(row=2, column=2, padx=(0, 10), pady=6)

        # Max row
        tk.Label(particle_frame, text="Maximum", width=10, anchor="w").grid(
            row=3, column=0, padx=(10, 20), pady=6, sticky="w"
        )
        tk.Entry(particle_frame, textvariable=self.particle_size_max_var, width=10).grid(
            row=3, column=1, padx=(0, 10), pady=6, sticky="w"
        )
        tk.Button(
            particle_frame,
            text="Reset",
            width=6,
            command=lambda: self._reset_particle_size("max"),
        ).grid(row=3, column=2, padx=(0, 10), pady=6)

        # ── Reset All ─────────────────────────────────────────────────
        tk.Button(
            self,
            text="Reset All to Defaults",
            command=self._reset_all,
        ).grid(row=5, column=0, pady=(8, 4), padx=20, sticky="w")

        # ── Nav buttons ───────────────────────────────────────────────
        nav_frame = tk.Frame(self)
        nav_frame.grid(row=10, column=0, pady=12, padx=20, sticky="ew")
        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=1)

        tk.Button(
            nav_frame,
            text="Back",
            command=lambda: self.controller.show_page("Upload") if self.controller else None,
        ).grid(row=0, column=0, padx=5, sticky="ew")

        tk.Button(
            nav_frame,
            text="Next",
            command=lambda: self.controller.show_page("Settings") if self.controller else None,
        ).grid(row=0, column=1, padx=5, sticky="ew")

    # ------------------------------------------------------------------
    # Interaction callbacks
    # ------------------------------------------------------------------

    def _reset_channel(self, channel: str, default):
        self.threshold_vars[channel].set(str(default))
        self.status_label.config(text=f"{channel.capitalize()} reset to {default}.")

    def _reset_particle_size(self, which: str):
        if which == "min":
            self.particle_size_min_var.set(str(DEFAULT_PARTICLE_SIZE_MIN))
            self.status_label.config(text=f"Minimum particle size reset to {DEFAULT_PARTICLE_SIZE_MIN}.")
        else:
            self.particle_size_max_var.set(str(DEFAULT_PARTICLE_SIZE_MAX))
            self.status_label.config(text=f"Maximum particle size reset to {DEFAULT_PARTICLE_SIZE_MAX}.")

    def _reset_all(self):
        for channel, default in DEFAULT_THRESHOLDS.items():
            if channel in self.threshold_vars:
                self.threshold_vars[channel].set(str(default))
        self.particle_size_min_var.set(str(DEFAULT_PARTICLE_SIZE_MIN))
        self.particle_size_max_var.set(str(DEFAULT_PARTICLE_SIZE_MAX))
        self.status_label.config(text="All values reset to defaults.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_base_path(self, path: str):
        self._base_path = Path(path)

    def set_channels(self, channels: list[dict]):
        labels = {ch["label"].lower() for ch in channels}
        active = [c for c in THRESHOLD_CHANNELS if c in labels]
        if active:
            self.status_label.config(text=f"Threshold channels detected: {', '.join(active)}")

    def get_thresholds(self) -> dict[str, int | None]:
        result = {}
        for ch, var in self.threshold_vars.items():
            raw = var.get().strip()
            result[ch] = int(raw) if raw.lstrip("-").isdigit() else None
        return result

    def get_particle_size(self) -> dict[str, int | None]:
        """
        Return min/max particle size values as ints, or None if blank/invalid.
        e.g. {"min": 2, "max": 2000}
        """
        result = {}
        for key, var in (("min", self.particle_size_min_var), ("max", self.particle_size_max_var)):
            raw = var.get().strip()
            result[key] = int(raw) if raw.lstrip("-").isdigit() else None
        return result


# ------------------------------------------------------------------
# Standalone smoke-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Masking Settings — Preview")
    root.geometry("500x480")

    page = MaskingSettingsPage(root, controller=None)
    page.pack(fill="both", expand=True)

    def print_values():
        print("Thresholds:   ", page.get_thresholds())
        print("Particle size:", page.get_particle_size())

    tk.Button(root, text="Print values (debug)", command=print_values).pack(pady=6)

    root.mainloop()