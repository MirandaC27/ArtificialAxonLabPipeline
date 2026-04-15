#SettingFront.py
import tkinter as tk
from tkinter import ttk

#I'm only adding this to show that I did complete U16 and U17
EXPERIMENTS = ['DAPI','GFP-mylein','CY5-myelin','GFP-debris','CY5-debris']



class SettingsPage(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.state = self.create_state()

        self.build_input_screen()
        self.build_output_screen()

        self.show_screen("input")


    def create_state(self):

        state = {}

        state["experiment_var"] = tk.StringVar()
        state["frame_var"] = tk.StringVar()
        state["ezra_var"] = tk.BooleanVar()

        state["widgets_3d"] = {}

        return state


    def show_screen(self, name):

        for screen in ("input", "output"):
            self.state[f"{screen}_frame"].grid_remove()

        self.state[f"{name}_frame"].grid(row=0, column=0, sticky="nsew")


    def submit(self):

        exp = self.state["experiment_var"].get()
        frames = self.state["frame_var"].get()
        ezra = self.state["ezra_var"].get()

        print(exp, frames, ezra)

        settings = (
            f"Experiment: {exp}\n"
            f"Frames: {frames}\n"
            f"Run Ezra: {ezra}"
        )

        self.state["output_label"].config(text=settings)
        self.show_screen("output")
        self.controller.show_page("Masking Settings")


    def create_3d_widgets(self, parent):

        w = {}

        w["frame_label"] = tk.Label(parent, text="Number of frames")
        w["frame_entry"] = tk.Entry(parent, textvariable=self.state["frame_var"])

        w["dist_label"] = tk.Label(parent, text="Distance between frames")
        w["dist_entry"] = tk.Entry(parent)

        w["ezra_check"] = tk.Checkbutton(
            parent,
            text="Run Ezra's algorithm?",
            variable=self.state["ezra_var"]
        )

        w["frame_label"].grid(row=3, column=0, padx=10, pady=5, sticky="e")
        w["frame_entry"].grid(row=3, column=1, padx=10, pady=5, sticky="w")

        w["dist_label"].grid(row=4, column=0, padx=10, pady=5, sticky="e")
        w["dist_entry"].grid(row=4, column=1, padx=10, pady=5, sticky="w")

        w["ezra_check"].grid(row=5, column=1, padx=10, pady=5, sticky="w")

        for widget in w.values():
            widget.grid_remove()

        self.state["widgets_3d"] = w


    def show_3D_inputs(self):

        for w in self.state["widgets_3d"].values():
            w.grid()


    def build_input_screen(self):

        frame = tk.Frame(self)
        self.state["input_frame"] = frame

        tk.Label(frame, text="Experiment").grid(row=0, column=0, pady=10)

        exp_menu = ttk.Combobox(
            frame,
            values=EXPERIMENTS,
            textvariable=self.state["experiment_var"],
            state="readonly"
        )
        exp_menu.grid(row=0, column=1, pady=10)
        exp_menu.set("Select experiment")
        
        self.create_3d_widgets(frame)

        # show 3D widgets by default
        self.show_3D_inputs()

        tk.Button(
            frame,
            text="Submit",
            command=self.submit
        ).grid(row=10, column=0, columnspan=2, pady=20)


    def build_output_screen(self):

        frame = tk.Frame(self)
        self.state["output_frame"] = frame

        label = tk.Label(frame, text="", font=("Arial", 16))
        label.grid(row=0, column=0, padx=20, pady=20)

        self.state["output_label"] = label

        nav_frame = tk.Frame(self)
        nav_frame.grid(row=10, column=0, pady=5, padx=20, sticky="ew")
        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=1)

        tk.Button(
            nav_frame,
            text="Back",
            command=lambda: self.controller.show_page("Upload")
        ).grid(row=0, column=0, padx=5, sticky="ew")

        tk.Button(
            nav_frame,
            text="Go to Image Processing",
            command=lambda: self.controller.show_page("Image Processing Stuff")
        ).grid(row=0, column=1, padx=5, sticky="ew")