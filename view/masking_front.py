#masking_front.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json


class MaskingSettingsPage(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.state = self._create_state()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_input_screen()
        self._build_output_screen()
        self.show_screen("input")


        self._seed_from_json()


    def set_base_path(self, path: str):
        """
        Receives the CLEANED directory path from UploadPageStep1 and
        writes it into the base_path
        """
        self.state["base_path_var"].set(path)
    
    def set_channels(self, channels):
        """
        Receives channel list from UploadPageStep1 and maps them into
        masking channel inputs automatically.
        
        Expected format:
        [{"num": 1, "label": "axon"}, ...]
        """

        mapping = {
            "axon": "ch_pillars_var",
            "nuclei": "ch_nuclei_var",
            "myelin": "ch_myelin_var",
            "debris": "ch_debris_var",
        }

        for ch in channels:
            label = ch["label"]
            num = ch["num"]

            if label in mapping:
                self.state[mapping[label]].set(str(num))


    def _seed_from_json(self):
        json_path = Path(__file__).resolve().parent.parent / "data" / "folder_paths.json"
        if not json_path.exists():
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Base path
            tracks1 = data.get("Tracks1", [])
            if tracks1:
                self.state["base_path_var"].set(tracks1[0])

            # Channels
            channels = data.get("Channels", [])
            parsed_channels = []

            for ch in channels:
                code = ch.get("code", "")
                label = ch.get("label", "")
                if code.startswith("CH"):
                    num = int(code.replace("CH", ""))
                    parsed_channels.append({"num": num, "label": label})

            if parsed_channels:
                self.set_channels(parsed_channels)

        except (json.JSONDecodeError, OSError):
            pass


    def _create_state(self):
        s = {}

        #Threshold inputs
        s["myelin_thresh_var"] = tk.StringVar(value="8000")
        s["debris_thresh_var"] = tk.StringVar(value="15000")

        # Path / range inputs 
        s["base_path_var"]    = tk.StringVar(value="")
        s["well_start_var"]   = tk.StringVar(value="2")
        s["well_end_var"]     = tk.StringVar(value="12")

        
        s["ch_pillars_var"]   = tk.StringVar(value="")
        s["ch_nuclei_var"]    = tk.StringVar(value="")
        s["ch_myelin_var"]    = tk.StringVar(value="")
        s["ch_debris_var"]    = tk.StringVar(value="")

        # Particle analysis inputs
        s["size_min_var"]     = tk.StringVar(value="")
        s["size_max_var"]     = tk.StringVar(value="")
        s["circ_min_var"]     = tk.StringVar(value="")
        s["circ_max_var"]     = tk.StringVar(value="")

        #Screen frames (filled in build methods)
        s["input_frame"]  = None
        s["output_frame"] = None
        s["output_label"] = None

        return s

    def show_screen(self, name):
        for screen in ("input", "output"):
            if self.state[f"{screen}_frame"]:
                self.state[f"{screen}_frame"].grid_remove()
        self.state[f"{name}_frame"].grid(row=0, column=0, sticky="nsew")



    def _validate_int(self, value, label):
        try:
            v = int(value)
            if v < 0:
                raise ValueError
            return v
        except ValueError:
            raise ValueError(f"'{label}' must be a non-negative integer (got: '{value}').")

    def _validate_float(self, value, label):
        try:
            v = float(value)
            if not (0.0 <= v <= 1.0):
                raise ValueError
            return v
        except ValueError:
            raise ValueError(f"'{label}' must be a float between 0 and 1 (got: '{value}').")

    def _validate_channel(self, value, label):
        try:
            v = int(value)
            if v < 1:
                raise ValueError
            return v
        except ValueError:
            raise ValueError(f"'{label}' must be a positive integer ≥ 1 (got: '{value}').")


    def submit(self):
        try:
            myelin_thresh = self._validate_int(self.state["myelin_thresh_var"].get(),  "Myelin Threshold")
            debris_thresh = self._validate_int(self.state["debris_thresh_var"].get(),  "Debris Threshold")
            well_start    = self._validate_int(self.state["well_start_var"].get(),     "Well Range Start")
            well_end      = self._validate_int(self.state["well_end_var"].get(),       "Well Range End")
            size_min      = self._validate_int(self.state["size_min_var"].get(),       "Particle Size Min")
            size_max      = self._validate_int(self.state["size_max_var"].get(),       "Particle Size Max")

            circ_min = self._validate_float(self.state["circ_min_var"].get(), "Circularity Min")
            circ_max = self._validate_float(self.state["circ_max_var"].get(), "Circularity Max")

            ch_pillars = self._validate_channel(self.state["ch_pillars_var"].get(), "Pillars Channel")
            ch_nuclei  = self._validate_channel(self.state["ch_nuclei_var"].get(),  "Nuclei Channel")
            ch_myelin  = self._validate_channel(self.state["ch_myelin_var"].get(),  "Myelin Channel")
            ch_debris  = self._validate_channel(self.state["ch_debris_var"].get(),  "Debris Channel")

            base_path_str = self.state["base_path_var"].get().strip()
            if not base_path_str:
                raise ValueError(
                    "Base Path is empty.\n"
                    "Please select a RAW folder on the Upload page first, "
                    "or enter the CLEANED path manually."
                )
            base_path = Path(base_path_str)

            if well_start >= well_end:
                raise ValueError("Well Range Start must be less than Well Range End.")
            if size_min >= size_max:
                raise ValueError("Particle Size Min must be less than Max.")
            if circ_min >= circ_max:
                raise ValueError("Circularity Min must be less than Max.")

        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        self.result_config = {
            "MYELIN_THRESH": myelin_thresh,
            "DEBRIS_THRESH": debris_thresh,
            "BASE_PATH":     base_path,
            "WELL_RANGE":    range(well_start, well_end),
            "channels": {
                "pillars": ch_pillars,
                "nuclei":  ch_nuclei,
                "myelin":  ch_myelin,
                "debris":  ch_debris,
            },
            "particles": {
                "size_min": size_min,
                "size_max": size_max,
                "circ_min": circ_min,
                "circ_max": circ_max,
            },
        }

        summary = (
            f"Myelin Threshold:   {myelin_thresh}\n"
            f"Debris Threshold:   {debris_thresh}\n"
            f"\n"
            f"Base Path:          {base_path}\n"
            f"Well Range:         B{well_start:02d} → B{well_end - 1:02d}\n"
            f"\n"
            f"Channels  — Pillars: {ch_pillars}  |  Nuclei: {ch_nuclei}  "
            f"|  Myelin: {ch_myelin}  |  Debris: {ch_debris}\n"
            f"\n"
            f"Particles — Size: {size_min}–{size_max}  |  Circularity: {circ_min:.2f}–{circ_max:.2f}"
        )

        self.state["output_label"].config(text=summary)
        self.show_screen("output")


    def _build_input_screen(self):
        frame = tk.Frame(self, padx=20)
        self.state["input_frame"] = frame
        frame.grid(row=0, column=0, sticky="nsew", pady=(0, 20))

        row = 0

        #tried some formatting things, we'll see if things are good.
        def section(text, r):
            tk.Label(frame, text=text, font=("TkDefaultFont", 10, "bold"),
                    fg="#333333").grid(row=r, column=0, columnspan=3,
                                    sticky="w", pady=(14, 2))
            ttk.Separator(frame, orient="horizontal").grid(
                row=r + 1, column=0, columnspan=3, sticky="ew")
            return r + 2

        def lbl(text, r, c=0):
            tk.Label(frame, text=text).grid(row=r, column=c, sticky="e",
                                            padx=(0, 6), pady=4)

        def entry(var, r, c=1, width=18):
            tk.Entry(frame, textvariable=var, width=width).grid(
                row=r, column=c, sticky="w", pady=4)

        row = section("Thresholds", row)

        lbl("Myelin Threshold", row)
        entry(self.state["myelin_thresh_var"], row)
        tk.Label(frame, text="(0 – 65535)", fg="grey").grid(
            row=row, column=2, sticky="w", padx=4)
        row += 1

        lbl("Debris Threshold", row)
        entry(self.state["debris_thresh_var"], row)
        tk.Label(frame, text="(0 – 65535)", fg="grey").grid(
            row=row, column=2, sticky="w", padx=4)
        row += 1

        row = section("File Path & Well Range", row)

        lbl("Base Path", row)
        path_entry = tk.Entry(frame, textvariable=self.state["base_path_var"], width=36)
        path_entry.grid(row=row, column=1, sticky="w", pady=4)
        tk.Label(frame, text="set by Upload page", fg="grey").grid(
            row=row, column=2, sticky="w", padx=4)
        tk.Button(frame, text="Browse…",
                command=self._browse_path).grid(row=row + 1, column=2,
                                                sticky="w", padx=4)
        row += 1

        lbl("Well Range Start", row)
        entry(self.state["well_start_var"], row, width=6)
        row += 1

        lbl("Well Range End", row)
        entry(self.state["well_end_var"], row, width=6)
        tk.Label(frame, text="(exclusive)", fg="grey").grid(
            row=row, column=2, sticky="w", padx=4)
        row += 1

        row = section("Channel Assignments (1-based)", row)

        for label, key in [
            ("Pillars (axon file)",  "ch_pillars_var"),
            ("Nuclei",               "ch_nuclei_var"),
            ("Myelin (MBP file)",    "ch_myelin_var"),
            ("Debris",               "ch_debris_var"),
        ]:
            lbl(label, row)
            entry(self.state[key], row, width=4)
            row += 1

        
        row = section("Particle Analysis", row)

        lbl("Size Min (px²)", row)
        entry(self.state["size_min_var"], row, width=8)
        row += 1

        lbl("Size Max (px²)", row)
        entry(self.state["size_max_var"], row, width=8)
        row += 1

        lbl("Circularity Min", row)
        entry(self.state["circ_min_var"], row, width=8)
        tk.Label(frame, text="(0.0 – 1.0)", fg="grey").grid(
            row=row, column=2, sticky="w", padx=4)
        row += 1

        lbl("Circularity Max", row)
        entry(self.state["circ_max_var"], row, width=8)
        tk.Label(frame, text="(0.0 – 1.0)", fg="grey").grid(
            row=row, column=2, sticky="w", padx=4)
        row += 1

        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=(18, 0), sticky="ew")

        tk.Button(btn_frame, text="Submit", width=14,
                command=self.submit).pack(side="left", padx=4)

        if hasattr(self.controller, "show_page"):
            tk.Button(
                btn_frame, text="Go to Image Processing",
                command=lambda: self.controller.show_page("Image Processing Stuff")
            ).pack(side="right", padx=4)


    def _browse_path(self):
        path = filedialog.askdirectory(title="Select Base Path")
        if path:
            self.state["base_path_var"].set(path)


    def _build_output_screen(self):
        frame = tk.Frame(self, padx=20)
        self.state["output_frame"] = frame
        frame.grid(row=0, column=0, sticky="nsew", pady=(0, 20))

        tk.Label(frame, text="Pipeline Configuration",
                font=("TkDefaultFont", 12, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 10))

        label = tk.Label(frame, text="", font=("Courier", 10),
                        justify="left", anchor="w",
                        relief="sunken", padx=10, pady=10, bg="#f5f5f5")
        label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=6)
        self.state["output_label"] = label

        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=12, sticky="ew")

        tk.Button(btn_frame, text="← Back", width=10,
                command=lambda: self.show_screen("input")).pack(side="left", padx=4)

        tk.Button(btn_frame, text="Run Pipeline", width=14,
                command=self._run_pipeline).pack(side="left", padx=4)

        if hasattr(self, "controller") and hasattr(self.controller, "show_page"):
            tk.Button(
                btn_frame, text="Go to Image Processing",
                command=lambda: self.controller.show_page("Image Processing Stuff")
            ).pack(side="right", padx=4)



    def _run_pipeline(self):
        """
        Hook: apply self.result_config to masking.py's PipelineConfig,
        then call main().  Integrate as needed in main.py.
        """
        try:
            from masking import PipelineConfig, main
            cfg = self.result_config
            import masking
            masking.config = PipelineConfig(
                MYELIN_THRESH=cfg["MYELIN_THRESH"],
                DEBRIS_THRESH=cfg["DEBRIS_THRESH"],
                BASE_PATH=cfg["BASE_PATH"],
                WELL_RANGE=cfg["WELL_RANGE"],
            )
            messagebox.showinfo("Starting", "Pipeline started — check terminal for progress.")
            main()
        except Exception as e:
            messagebox.showerror("Pipeline Error", str(e))


    def get_config(self):
        """Returns the validated config dict, or None if not yet submitted."""
        return getattr(self, "result_config", None)


if __name__ == "__main__":

    class _StubController:
        def show_page(self, name):
            print(f"[stub] navigate to: {name}")

    root = tk.Tk()
    root.title("Masking Pipeline Settings")
    root.geometry("900x900")
    root.resizable(False, False)

    page = MaskingSettingsPage(root, _StubController())
    page.grid(row=0, column=0, sticky="nsew")

    root.mainloop()