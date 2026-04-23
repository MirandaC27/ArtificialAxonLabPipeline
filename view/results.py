import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
import json
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd


class ResultsPage(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg="black")
        self.controller = controller

        # ─────────────────────────────────────────────
        # PROJECT ROOT → results folder
        # ─────────────────────────────────────────────
        SCRIPT_DIR = Path(__file__).resolve().parent
        self.PROJECT_ROOT = SCRIPT_DIR.parent
        self.RESULTS_DIR = self.PROJECT_ROOT / "results"
        self.RESULTS_DIR.mkdir(exist_ok=True)

        self.ORDER_FILE = self.PROJECT_ROOT / "csv_order.json"

        self.selected_csv = None
        self.csv_order = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ───────────────────────── LEFT PANEL ─────────────────────────
        self.left_frame = tk.Frame(self, bg="black")
        self.left_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)

        if controller:
            tk.Button(
                self.left_frame,
                text="Cancel",
                command=lambda: controller.show_page("Home"),
                font=("Arial", 12),
                width=12
            ).pack(anchor="w", pady=5)

        self.list_container = tk.Frame(self.left_frame, bg="black")
        self.list_container.pack(fill="both", expand=True, pady=10)

        self.scrollbar = tk.Scrollbar(self.list_container, orient="vertical")
        self.canvas = tk.Canvas(
            self.list_container,
            yscrollcommand=self.scrollbar.set,
            width=220,
            bg="black",
            highlightthickness=0
        )

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.canvas.yview)

        self.csv_list_frame = tk.Frame(self.canvas, bg="black")
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.csv_list_frame, anchor="nw"
        )

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.csv_list_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        tk.Button(self.left_frame, text="Load", command=self.load_csv).pack(side="bottom", fill="x", pady=2)
        tk.Button(self.left_frame, text="Remove", command=self.remove_csv).pack(side="bottom", fill="x", pady=2)
        tk.Button(self.left_frame, text="Refresh", command=self.get_all_csvs).pack(side="bottom", fill="x", pady=2)

        # rows control
        self.rows_var = tk.StringVar(value="5")
        rows_frame = tk.Frame(self.left_frame, bg="black")
        rows_frame.pack(side="bottom", fill="x", pady=5)

        tk.Label(rows_frame, text="Rows:", bg="black", fg="white").pack(side="left")
        tk.Entry(rows_frame, textvariable=self.rows_var, width=5).pack(side="left", padx=4)

        # ───────────────────────── RIGHT PANEL ─────────────────────────
        self.right_frame = tk.Frame(self, bg="black")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)

        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.preview_title = tk.Label(
            self.right_frame,
            text="Select a CSV",
            font=("Arial", 22, "bold"),
            bg="black",
            fg="white"
        )
        self.preview_title.grid(row=0, column=0, pady=(0, 5))

        self.preview_text = tk.Text(
            self.right_frame,
            wrap="none",
            bg="#000000",
            fg="white",
            font=("Courier", 10)
        )
        self.preview_text.grid(row=1, column=0, sticky="nsew", padx=20)

        # ───────────────────────── NEW BUTTON ─────────────────────────
        tk.Button(
            self.right_frame,
            text="Save Run Settings",
            command=self.save_run_settings,
            bg="black",
            fg="white"
        ).grid(row=2, column=0, pady=10)

        self.get_all_csvs()

    # ─────────────────────────────────────────────
    # FILE LOADING
    # ─────────────────────────────────────────────

    def get_all_csvs(self):
        self.csv_order = sorted(self.RESULTS_DIR.glob("*.csv"))
        self.render_csv_list()

    def render_csv_list(self):
        for w in self.csv_list_frame.winfo_children():
            w.destroy()

        for csv_path in self.csv_order:
            item = tk.Label(
                self.csv_list_frame,
                text=csv_path.name,
                anchor="w",
                padx=10,
                pady=8,
                bg="black",
                fg="white",
                cursor="hand2"
            )
            item.pack(fill="x")
            item.bind("<Button-1>", lambda e, p=csv_path: self._show_preview(p))

    # ─────────────────────────────────────────────
    # PREVIEW
    # ─────────────────────────────────────────────

    def _show_preview(self, csv_path):
        try:
            self.selected_csv = csv_path
            df = pd.read_csv(csv_path)

            self.preview_title.config(text=csv_path.name)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert(tk.END, str(df.head()))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ─────────────────────────────────────────────
    # SAVE RUN SETTINGS (NEW)
    # ─────────────────────────────────────────────

    def save_run_settings(self):
        if not self.selected_csv:
            return messagebox.showwarning("Warning", "Select a CSV first")

        settings_file = self.selected_csv.with_suffix(".settings.json")

        settings = {
            "csv_file": self.selected_csv.name,
            "timestamp": datetime.now().isoformat()
        }

        pipeline_settings = self._load_pipeline_settings()
        if pipeline_settings:
            settings.update(pipeline_settings)

        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)

            messagebox.showinfo("Saved", f"Settings saved:\n{settings_file.name}")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _load_pipeline_settings(self):
        try:
            settings_path = self.PROJECT_ROOT / "data" / "masking_settings.json"
            if settings_path.exists():
                with open(settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    # ─────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────

    def load_csv(self):
        if not self.selected_csv:
            return messagebox.showwarning("Warning", "Select a CSV first")
        messagebox.showinfo("Loaded", str(self.selected_csv))

    def remove_csv(self):
        if not self.selected_csv:
            return

        if messagebox.askyesno("Delete", "Remove file?"):
            self.selected_csv.unlink(missing_ok=True)
            self.selected_csv = None
            self.get_all_csvs()