import tkinter as tk
from tkinter import ttk, messagebox

from state import settings_data


EXPERIMENTS = [
    "DAPI",
    "GFP-myelin",
    "CY5-myelin",
    "GFP-debris",
    "CY5-debris"
]


class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        self.experiment_var = tk.StringVar()
        self.frame_var = tk.StringVar()
        self.dist_var = tk.StringVar()
        self.ezra_var = tk.BooleanVar(value=False)

        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        tk.Label(
            self,
            text="Settings",
            font=("Arial", 18, "bold")
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            pady=20
        )

        tk.Label(
            self,
            text="Experiment"
        ).grid(
            row=1,
            column=0,
            padx=10,
            pady=8,
            sticky="e"
        )

        self.exp_menu = ttk.Combobox(
            self,
            values=EXPERIMENTS,
            textvariable=self.experiment_var,
            state="readonly"
        )
        self.exp_menu.grid(
            row=1,
            column=1,
            padx=10,
            pady=8,
            sticky="w"
        )

        tk.Label(
            self,
            text="Number of frames"
        ).grid(
            row=2,
            column=0,
            padx=10,
            pady=8,
            sticky="e"
        )

        tk.Entry(
            self,
            textvariable=self.frame_var
        ).grid(
            row=2,
            column=1,
            padx=10,
            pady=8,
            sticky="w"
        )

        tk.Label(
            self,
            text="Distance between frames"
        ).grid(
            row=3,
            column=0,
            padx=10,
            pady=8,
            sticky="e"
        )

        tk.Entry(
            self,
            textvariable=self.dist_var
        ).grid(
            row=3,
            column=1,
            padx=10,
            pady=8,
            sticky="w"
        )

        tk.Checkbutton(
            self,
            text="Run Ezra's algorithm?",
            variable=self.ezra_var
        ).grid(
            row=4,
            column=1,
            padx=10,
            pady=8,
            sticky="w"
        )

        self.output_label = tk.Label(
            self,
            text="",
            justify="left",
            font=("Arial", 12)
        )
        self.output_label.grid(
            row=5,
            column=0,
            columnspan=2,
            pady=15
        )

        nav_frame = tk.Frame(self)
        nav_frame.grid(
            row=7,
            column=0,
            columnspan=2,
            pady=10,
            padx=20,
            sticky="ew"
        )

        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=1)

        tk.Button(
            nav_frame,
            text="Back",
            command=self._on_back
        ).grid(
            row=0,
            column=0,
            padx=5,
            sticky="ew"
        )

        tk.Button(
            nav_frame,
            text="Next",
            command=self._on_next
        ).grid(
            row=0,
            column=1,
            padx=5,
            sticky="ew"
        )

    def refresh(self):
        experiment = settings_data.get("experiment", "")

        self.experiment_var.set(
            experiment if experiment else "Select experiment"
        )

        frames = settings_data.get("frames", 0)

        self.frame_var.set(
            str(frames) if frames else ""
        )

        self.dist_var.set(
            settings_data.get("distance", "")
        )

        self.ezra_var.set(
            settings_data.get("run_ezra", False)
        )

    def save_current_state(self):
        experiment = self.experiment_var.get().strip()
        frames = self.frame_var.get().strip()
        distance = self.dist_var.get().strip()
        run_ezra = self.ezra_var.get()

        if not experiment or experiment == "Select experiment":
            raise ValueError("Please select an experiment.")

        if not frames.isdigit():
            raise ValueError("Frames must be a whole number.")

        if int(frames) <= 0:
            raise ValueError("Frames must be greater than zero.")

        if not distance:
            raise ValueError(
                "Please enter the distance between frames."
            )

        settings_data["experiment"] = experiment
        settings_data["frames"] = int(frames)
        settings_data["distance"] = distance
        settings_data["run_ezra"] = run_ezra

    def _on_back(self):
        try:
            experiment = self.experiment_var.get().strip()
            frames = self.frame_var.get().strip()
            distance = self.dist_var.get().strip()

            if experiment != "Select experiment":
                settings_data["experiment"] = experiment

            if frames.isdigit():
                settings_data["frames"] = int(frames)

            settings_data["distance"] = distance
            settings_data["run_ezra"] = self.ezra_var.get()

            self.controller.show_page("Upload")

        except Exception as e:
            messagebox.showerror("Settings Error", str(e))

    def _on_next(self):
        try:
            self.save_current_state()

            self.output_label.config(
                text=(
                    f"Experiment: "
                    f"{settings_data['experiment']}\n"
                    f"Frames: "
                    f"{settings_data['frames']}\n"
                    f"Distance: "
                    f"{settings_data['distance']}\n"
                    f"Run Ezra: "
                    f"{settings_data['run_ezra']}"
                )
            )

            self.controller.show_page("TestSave")

        except Exception as e:
            messagebox.showerror("Settings Error", str(e))
