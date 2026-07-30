import tkinter as tk
from tkinter import messagebox

from api_client import save_upload_step1
from state import history_state, masking_data, settings_data, upload_data


class TestSave(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        tk.Label(self, text="Test Save", font=("Arial", 18, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(20, 10)
        )

        tk.Label(
            self,
            text="Review the current upload and settings before saving history.",
        ).grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 12))

        self.summary_text = tk.Text(self, height=12, width=60, wrap="word")
        self.summary_text.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.summary_text.configure(state="disabled")

        nav_frame = tk.Frame(self)
        nav_frame.grid(row=3, column=0, columnspan=2, pady=20, padx=20, sticky="ew")
        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=1)

        self.back_button = tk.Button(nav_frame, text="Back", command=self._on_back)
        self.back_button.grid(row=0, column=0, padx=5, sticky="ew")

        self.next_button = tk.Button(
            nav_frame,
            text="Next (Save History)",
            command=self._on_next,
        )
        self.next_button.grid(row=0, column=1, padx=5, sticky="ew")

    def refresh(self):
        lines = [
            "Upload data:",
            f"  Microscope: {upload_data.get('microscope', '')}",
            f"  Image type: {upload_data.get('image_type', '')}",
            f"  Number of FOVs: {upload_data.get('num_fovs', 0)}",
            f"  Channels: {upload_data.get('channels', [])}",
            "",
            "Settings:",
            f"  Experiment: {settings_data.get('experiment', '')}",
            f"  Frames: {settings_data.get('frames', 0)}",
            f"  Distance: {settings_data.get('distance', '')}",
            f"  Run Ezra: {settings_data.get('run_ezra', False)}",
            "",
            "Masking:",
            f"  Base path: {masking_data.get('base_path', '')}",
            f"  Wells: {masking_data.get('well_start')} - {masking_data.get('well_end')}",
            f"  Thresholds: {masking_data.get('thresholds', {})}",
            f"  Auto thresholds: {masking_data.get('auto_thresholds', {})}",
            f"  Particle size: {masking_data.get('particle_size', {})}",
            "",
            "History state:",
            f"  Saved: {history_state.get('saved', False)}",
            f"  History ID: {history_state.get('history_id')}",
        ]

        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert("1.0", "\n".join(lines))
        self.summary_text.configure(state="disabled")

    def save_history_once(self):
        if history_state["saved"]:
            return history_state["history_id"]

        saved_record = save_upload_step1(dict(upload_data), dict(settings_data), dict(masking_data))
        history_state["saved"] = True
        history_state["history_id"] = saved_record.get("id")
        return history_state["history_id"]

    def _on_back(self):
        self.controller.show_page("Masking")

    def _on_next(self):
        self.next_button.configure(state="disabled")
        try:
            history_id = self.save_history_once()
            messagebox.showinfo("Complete", f"History saved successfully.\nHistory ID: {history_id}")
            self.controller.show_page("Results")
        except Exception as exc:
            messagebox.showerror("History Save Error", str(exc))
        finally:
            self.next_button.configure(state="normal")
