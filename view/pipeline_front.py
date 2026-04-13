import tkinter as tk
from pathlib import Path
import json


class ImageProcessingSettings(tk.Frame):

    def __init__(self, parent, controller=None):
        super().__init__(parent)

        self.controller = controller

        self.build_ui()


    def build_ui(self):

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        input_frame = tk.LabelFrame(self, text="Image Processing Parameters")
        input_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        # Threshold
        tk.Label(input_frame, text="Threshold:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.threshold_entry = tk.Entry(input_frame, width=15)
        self.threshold_entry.grid(row=0, column=1, padx=5, pady=5)

        # Frame Distance
        tk.Label(input_frame, text="Frame Distance:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.frame_distance_entry = tk.Entry(input_frame, width=15)
        self.frame_distance_entry.grid(row=1, column=1, padx=5, pady=5)


        self.status_label = tk.Label(self, text="", justify="left")
        self.status_label.grid(row=1, column=0, pady=5, padx=20, sticky="w")


        button_frame = tk.Frame(self)
        button_frame.grid(row=2, column=0, pady=10, padx=20, sticky="ew")

        tk.Button(button_frame, text="Save Inputs", command=self.save_inputs).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Run", command=self.button_run).grid(row=0, column=1, padx=5)

        # next and back buttons 
        nav_frame = tk.Frame(self)
        nav_frame.grid(row=3, column=0, pady=5, padx=20, sticky="ew")
        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=1)

        tk.Button(
            nav_frame,
            text="Back",
            command=lambda: self.controller.show_page("Settings")
        ).grid(row=0, column=0, padx=5, sticky="ew")

        tk.Button(
            nav_frame,
            text="Next",
            command=lambda: self.controller.show_page("Masking Settings")
        ).grid(row=0, column=1, padx=5, sticky="ew")


    def validate_inputs(self):

        threshold = self.threshold_entry.get().strip()
        frame_distance = self.frame_distance_entry.get().strip()

        if threshold == "" or frame_distance == "":
            self.status_label.config(text="All fields are required.")
            return None

        try:
            threshold_val = float(threshold)
        except ValueError:
            self.status_label.config(text="Threshold must be a number.")
            return None

        try:
            frame_distance_val = int(frame_distance)
        except ValueError:
            self.status_label.config(text="Frame distance must be an integer.")
            return None

        return threshold_val, frame_distance_val


    def save_inputs(self):

        validated = self.validate_inputs()

        if not validated:
            return

        threshold_val, frame_distance_val = validated

        json_data = {
            "threshold": threshold_val,
            "frame_distance": frame_distance_val
        }

        json_path = Path(__file__).resolve().parent / "image_processing_inputs.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

        self.status_label.config(text="Inputs saved successfully.")

    def button_run(self):

        validated = self.validate_inputs()

        if not validated:
            return

        self.save_inputs()

        # Placeholder
        print("Running with inputs:")
        print(f"Threshold: {validated[0]}")
        print(f"Frame Distance: {validated[1]}")

        self.status_label.config(text="Processing started...")