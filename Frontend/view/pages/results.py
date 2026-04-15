import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
import json

try:
    import pandas as pd
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd


class CSVPreviewPage(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg="black")
        self.controller = controller

        self.CSV_DIR = Path("./csv_files")
        self.CSV_DIR.mkdir(parents=True, exist_ok=True)

        self.ORDER_FILE = Path("./csv_order.json")

        self.selected_csv = None
        self.selected_label = None
        self.csv_order = []

        self.ITEM_HEIGHT = 45
        self.drag_data = {"widget": None, "start_y": 0, "start_index": -1, "csv": None}

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # left
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

        # Scrollable list
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

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )
        self.csv_list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Bottom controls (mirroring original: Load / Delete / Save + entry)
        tk.Button(
            self.left_frame, text="Load", command=self.load_csv
        ).pack(side="bottom", fill="x", pady=2)

        tk.Button(
            self.left_frame, text="Remove", command=self.remove_csv
        ).pack(side="bottom", fill="x", pady=2)

        tk.Button(
            self.left_frame, text="Browse…", command=self.browse_csv
        ).pack(side="bottom", fill="x", pady=2)

        self.rows_var = tk.StringVar(value="5")
        rows_frame = tk.Frame(self.left_frame, bg="black")
        rows_frame.pack(side="bottom", fill="x", pady=5)
        tk.Label(rows_frame, text="Rows to preview:", bg="black", font=("Arial", 9)).pack(side="left")
        tk.Entry(rows_frame, textvariable=self.rows_var, width=5).pack(side="left", padx=4)

        # ── Right Side ─────────────────────────────────────────────────────────
        self.right_frame = tk.Frame(self, bg="black")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)

        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.preview_title = tk.Label(
            self.right_frame,
            text="Select a CSV",
            font=("Arial", 22, "bold"),
            bg="black"
        )
        self.preview_title.grid(row=0, column=0, pady=(0, 5))

        # Scrollable table area (Text widget keeps parity with original)
        text_frame = tk.Frame(self.right_frame, bg="black")
        text_frame.grid(row=1, column=0, sticky="nsew", padx=20)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        self.preview_text = tk.Text(
            text_frame,
            wrap="none",
            bg="#000000",
            font=("Courier", 10)
        )
        h_scroll = tk.Scrollbar(text_frame, orient="horizontal", command=self.preview_text.xview)
        v_scroll = tk.Scrollbar(text_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set
        )

        self.preview_text.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        # Bottom buttons
        bottom_frame = tk.Frame(self.right_frame, bg="black")
        bottom_frame.grid(row=2, column=0, pady=10)

        tk.Button(
            bottom_frame,
            text="Refresh",
            width=12,
            command=self.refresh_preview
        ).pack(side="left", padx=5)

        tk.Button(
            bottom_frame,
            text="Export head",
            width=12,
            bg="black",
            fg="black",
            command=self.export_head
        ).pack(side="left", padx=5)

        self.get_all_csvs()

    

    def save_order(self):
        try:
            self.ORDER_FILE.write_text(json.dumps([p.name for p in self.csv_order]))
        except Exception:
            pass

    def load_order(self):
        all_csvs = {p.name: p for p in self.CSV_DIR.glob("*.csv")}
        ordered = []

        if self.ORDER_FILE.exists():
            try:
                saved = json.loads(self.ORDER_FILE.read_text())
                for name in saved:
                    if name in all_csvs:
                        ordered.append(all_csvs.pop(name))
            except Exception:
                pass

        ordered.extend(all_csvs.values())
        return ordered

    def get_all_csvs(self):
        self.csv_order = self.load_order()
        self.render_csv_list()

    #dragging to re order

    def render_csv_list(self):
        for widget in self.csv_list_frame.winfo_children():
            widget.destroy()

        self.selected_label = None

        for csv_path in self.csv_order:
            item = tk.Label(
                self.csv_list_frame,
                text=f"to {csv_path.stem}",
                anchor="w",
                padx=10,
                pady=8,
                bg="black",
                cursor="hand2"
            )
            item.pack(fill="x")

            item.bind("<ButtonPress-1>", lambda e, c=csv_path: self.on_drag_start(e, c))
            item.bind("<B1-Motion>", self.on_drag_motion)
            item.bind("<ButtonRelease-1>", self.on_drag_release)

            tk.Frame(self.csv_list_frame, height=1, bg="#ccc").pack(fill="x", padx=5, pady=2)

    def on_drag_start(self, event, csv_path):
        self.drag_data = {
            "widget": event.widget,
            "start_y": event.y_root,
            "start_index": self.get_label_index(event.widget),
            "csv": csv_path,
        }
        event.widget.config(bg="#b1b2b3")

    def on_drag_motion(self, event):
        pass

    def on_drag_release(self, event):
        if not self.drag_data["widget"]:
            return

        delta_y = event.y_root - self.drag_data["start_y"]
        steps = round(delta_y / self.ITEM_HEIGHT)
        start_idx = self.drag_data["start_index"]
        csv_path = self.drag_data["csv"]

        if steps == 0:
            # Single click to select and preview
            self.selected_csv = csv_path

            if self.selected_label and self.selected_label.winfo_exists():
                self.selected_label.config(bg="black")

            self.selected_label = self.drag_data["widget"]
            self.selected_label.config(bg="#e0e0e0")

            self._show_preview(csv_path)
        else:
            target = max(0, min(len(self.csv_order) - 1, start_idx + steps))
            item = self.csv_order.pop(start_idx)
            self.csv_order.insert(target, item)
            self.save_order()
            self.render_csv_list()

        self.drag_data["widget"] = None

    def get_label_index(self, widget):
        text = widget.cget("text").replace("→ ", "").strip()
        for i, path in enumerate(self.csv_order):
            if path.stem == text:
                return i
        return -1

    #preview stuff

    def _show_preview(self, csv_path):
        try:
            n = int(self.rows_var.get())
        except ValueError:
            n = 5

        try:
            # Auto-detect delimiter using Python's csv sniffer
            import csv
            with open(csv_path, newline="", encoding="utf-8-sig") as f:
                sample = f.read(4096)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                sep = dialect.delimiter
            except csv.Error:
                sep = ","

            df = pd.read_csv(csv_path, sep=sep)
            head = df.head(n)

            self.preview_title.config(text=csv_path.stem)
            self.preview_text.delete("1.0", tk.END)

            # Shape info line
            info = f"Shape: {df.shape[0]} rows × {df.shape[1]} columns    (delimiter: {repr(sep)})\n\n"
            self.preview_text.insert(tk.END, info)

            # Build a clean aligned table manually
            cols = [str(c) for c in head.columns]
            rows = [[str(v) for v in row] for row in head.itertuples(index=False)]

            # Column widths = max of header or any cell value
            widths = [len(c) for c in cols]
            for row in rows:
                for i, val in enumerate(row):
                    widths[i] = max(widths[i], len(val))

            def fmt_row(cells):
                return "  ".join(c.ljust(widths[i]) for i, c in enumerate(cells))

            separator = "  ".join("-" * w for w in widths)

            self.preview_text.insert(tk.END, fmt_row(cols) + "\n")
            self.preview_text.insert(tk.END, separator + "\n")
            for row in rows:
                self.preview_text.insert(tk.END, fmt_row(row) + "\n")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_preview(self):
        if self.selected_csv:
            self._show_preview(self.selected_csv)

    # actions

    def browse_csv(self):
        """Open file dialog, copy CSV into the managed folder, refresh list."""
        path = filedialog.askopenfilename(
            title="Select a CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        src = Path(path)
        dest = self.CSV_DIR / src.name

        if dest.exists():
            if not messagebox.askyesno("File exists", f"{src.name} already exists. Overwrite?"):
                return

        try:
            dest.write_bytes(src.read_bytes())
            self.get_all_csvs()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_csv(self):
        """Mark selected CSV as the 'active' one (prints path — extend as needed)."""
        if not self.selected_csv:
            return messagebox.showwarning("Warning", "Select a CSV first")
        messagebox.showinfo("Loaded", f"Active CSV set to:\n{self.selected_csv}")

    def remove_csv(self):
        if not self.selected_csv:
            return

        if messagebox.askyesno("Confirm", f"Remove {self.selected_csv.name} from list?\n(file will be deleted)"):
            self.selected_csv.unlink(missing_ok=True)
            self.selected_csv = None

            self.preview_title.config(text="Select a CSV")
            self.preview_text.delete("1.0", tk.END)

            self.get_all_csvs()

    def export_head(self):
        """Save the currently previewed head() rows to a new CSV."""
        if not self.selected_csv:
            return messagebox.showwarning("Warning", "Select a CSV first")

        try:
            n = int(self.rows_var.get())
        except ValueError:
            n = 5

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"{self.selected_csv.stem}_head{n}.csv"
        )
        if not save_path:
            return

        try:
            import csv
            with open(self.selected_csv, newline="", encoding="utf-8-sig") as f:
                sample = f.read(4096)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                sep = dialect.delimiter
            except csv.Error:
                sep = ","
            df = pd.read_csv(self.selected_csv, sep=sep)
            df.head(n).to_csv(save_path, index=False)
            messagebox.showinfo("Exported", f"Saved to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    root.title("CSV Preview")
    root.geometry("900x600")
    root.configure(bg="black")

    page = CSVPreviewPage(root)
    page.pack(fill="both", expand=True)

    root.mainloop()