import base64
import csv
import io
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from api_client import (
    delete_result_csv,
    get_result_csv,
    get_result_csvs,
    reorder_result_csvs,
    save_result_csv,
)


class ResultsPage(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg="white")
        self.controller = controller
        self.selected_csv = None
        self.selected_content = None
        self.selected_label = None
        self.csv_order = []
        self.item_height = 45
        self.drag_data = {"widget": None, "start_y": 0, "start_index": -1, "csv": None}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.left_frame = tk.Frame(self, bg="white")
        self.left_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        tk.Button(
            self.left_frame,
            text="Back",
            command=lambda: self.controller.show_page("TestSave"),
            font=("Arial", 12),
            width=12,
        ).pack(anchor="w", pady=5)

        list_container = tk.Frame(self.left_frame, bg="white")
        list_container.pack(fill="both", expand=True, pady=10)
        scrollbar = tk.Scrollbar(list_container, orient="vertical")
        self.canvas = tk.Canvas(
            list_container,
            yscrollcommand=scrollbar.set,
            width=220,
            bg="white",
            highlightthickness=0,
        )
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.canvas.yview)
        self.csv_list_frame = tk.Frame(self.canvas, bg="white")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.csv_list_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfig(self.canvas_window, width=event.width))
        self.csv_list_frame.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        tk.Button(self.left_frame, text="Load", command=self.load_csv).pack(side="bottom", fill="x", pady=2)
        tk.Button(self.left_frame, text="Remove", command=self.remove_csv).pack(side="bottom", fill="x", pady=2)
        tk.Button(self.left_frame, text="Browse...", command=self.browse_csv).pack(side="bottom", fill="x", pady=2)
        self.rows_var = tk.StringVar(value="5")
        rows_frame = tk.Frame(self.left_frame, bg="white")
        rows_frame.pack(side="bottom", fill="x", pady=5)
        tk.Label(rows_frame, text="Rows to preview:", bg="white", font=("Arial", 9)).pack(side="left")
        tk.Entry(rows_frame, textvariable=self.rows_var, width=5).pack(side="left", padx=4)

        self.right_frame = tk.Frame(self, bg="white")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.preview_title = tk.Label(self.right_frame, text="Select a CSV", font=("Arial", 22, "bold"), bg="white")
        self.preview_title.grid(row=0, column=0, pady=(0, 5))

        text_frame = tk.Frame(self.right_frame, bg="white")
        text_frame.grid(row=1, column=0, sticky="nsew", padx=20)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        self.preview_text = tk.Text(text_frame, wrap="none", bg="white", font=("Courier", 10))
        horizontal = tk.Scrollbar(text_frame, orient="horizontal", command=self.preview_text.xview)
        vertical = tk.Scrollbar(text_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set, state="disabled")
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")

        bottom = tk.Frame(self.right_frame, bg="white")
        bottom.grid(row=2, column=0, pady=10, sticky="ew")
        bottom.grid_columnconfigure((0, 1, 2), weight=1)
        tk.Button(bottom, text="Refresh", command=self.refresh_preview).grid(row=0, column=0, padx=5, sticky="ew")
        tk.Button(bottom, text="Export Head", command=self.export_head).grid(row=0, column=1, padx=5, sticky="ew")
        tk.Button(bottom, text="Next", command=lambda: self.controller.show_page("SessionEnd")).grid(row=0, column=2, padx=5, sticky="ew")

    def refresh(self):
        try:
            self.csv_order = get_result_csvs()
            selected_id = self.selected_csv.get("id") if self.selected_csv else None
            self.selected_csv = next((item for item in self.csv_order if item["id"] == selected_id), None)
            if self.selected_csv is None:
                self.selected_content = None
                self.clear_preview()
            self.render_csv_list()
        except Exception as exc:
            messagebox.showerror("Results API Error", str(exc))

    def render_csv_list(self):
        for widget in self.csv_list_frame.winfo_children():
            widget.destroy()
        self.selected_label = None
        if not self.csv_order:
            tk.Label(self.csv_list_frame, text="No CSV files stored.", bg="white", fg="gray40").pack(padx=10, pady=10)
            return
        for csv_record in self.csv_order:
            item = tk.Label(
                self.csv_list_frame,
                text=f"→ {Path(csv_record['filename']).stem}",
                anchor="w",
                padx=10,
                pady=8,
                bg="white",
                cursor="hand2",
            )
            item.pack(fill="x")
            item.bind("<ButtonPress-1>", lambda event, record=csv_record: self.on_drag_start(event, record))
            item.bind("<B1-Motion>", lambda _event: None)
            item.bind("<ButtonRelease-1>", self.on_drag_release)
            tk.Frame(self.csv_list_frame, height=1, bg="#ccc").pack(fill="x", padx=5, pady=2)

    def on_drag_start(self, event, csv_record):
        self.drag_data = {
            "widget": event.widget,
            "start_y": event.y_root,
            "start_index": self.csv_order.index(csv_record),
            "csv": csv_record,
        }
        event.widget.config(bg="#d9e8f5")

    def on_drag_release(self, event):
        widget = self.drag_data.get("widget")
        if widget is None:
            return
        steps = round((event.y_root - self.drag_data["start_y"]) / self.item_height)
        start = self.drag_data["start_index"]
        record = self.drag_data["csv"]
        if steps == 0:
            self.selected_csv = record
            if self.selected_label and self.selected_label.winfo_exists():
                self.selected_label.config(bg="white")
            self.selected_label = widget
            widget.config(bg="#e0e0e0")
            self.load_selected_content()
        else:
            target = max(0, min(len(self.csv_order) - 1, start + steps))
            self.csv_order.insert(target, self.csv_order.pop(start))
            try:
                reorder_result_csvs([item["id"] for item in self.csv_order])
                self.render_csv_list()
            except Exception as exc:
                messagebox.showerror("Results API Error", str(exc))
                self.refresh()
        self.drag_data["widget"] = None

    def preview_row_count(self):
        try:
            return max(1, int(self.rows_var.get()))
        except ValueError:
            return 5

    def load_selected_content(self):
        if not self.selected_csv:
            return
        try:
            record = get_result_csv(self.selected_csv["id"])
            self.selected_content = base64.b64decode(record["content_base64"])
            self.show_preview()
        except Exception as exc:
            messagebox.showerror("Results API Error", str(exc))

    def read_csv_bytes(self, content):
        text = content.decode("utf-8-sig")
        try:
            delimiter = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","
        return delimiter, list(csv.reader(io.StringIO(text), delimiter=delimiter))

    def show_preview(self):
        if self.selected_content is None or not self.selected_csv:
            return
        try:
            delimiter, rows = self.read_csv_bytes(self.selected_content)
            header = rows[0] if rows else []
            body = rows[1:self.preview_row_count() + 1]
            widths = [len(str(value)) for value in header]
            for row in body:
                while len(widths) < len(row):
                    widths.append(0)
                for index, value in enumerate(row):
                    widths[index] = max(widths[index], len(str(value)))

            def formatted(row):
                return "  ".join(str(value).ljust(widths[index]) for index, value in enumerate(row))

            lines = [f"Shape: {max(0, len(rows) - 1)} rows × {len(header)} columns  (delimiter: {delimiter!r})", ""]
            if header:
                lines.extend([formatted(header), "  ".join("-" * width for width in widths)])
                lines.extend(formatted(row) for row in body)
            self.preview_title.config(text=Path(self.selected_csv["filename"]).stem)
            self.set_preview("\n".join(lines))
        except Exception as exc:
            messagebox.showerror("CSV Error", str(exc))

    def set_preview(self, value):
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", value)
        self.preview_text.config(state="disabled")

    def clear_preview(self):
        self.preview_title.config(text="Select a CSV")
        self.set_preview("")

    def refresh_preview(self):
        if self.selected_csv:
            self.load_selected_content()

    def browse_csv(self):
        selected = filedialog.askopenfilename(title="Select a CSV file", filetypes=[("CSV files", "*.csv")])
        if not selected:
            return
        source = Path(selected)
        try:
            content_base64 = base64.b64encode(source.read_bytes()).decode("ascii")
            response = save_result_csv(source.name, content_base64)
            if response.status_code == 409:
                if not messagebox.askyesno("File Exists", f"{source.name} already exists. Overwrite it?"):
                    return
                response = save_result_csv(source.name, content_base64, overwrite=True)
            response.raise_for_status()
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Results API Error", str(exc))

    def load_csv(self):
        if not self.selected_csv:
            messagebox.showwarning("Selection Required", "Select a CSV first.")
            return
        self.load_selected_content()

    def remove_csv(self):
        if not self.selected_csv:
            messagebox.showwarning("Selection Required", "Select a CSV first.")
            return
        if not messagebox.askyesno("Confirm Removal", f"Delete {self.selected_csv['filename']} from PostgreSQL?"):
            return
        try:
            delete_result_csv(self.selected_csv["id"])
            self.selected_csv = None
            self.selected_content = None
            self.clear_preview()
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Results API Error", str(exc))

    def export_head(self):
        if not self.selected_csv:
            messagebox.showwarning("Selection Required", "Select a CSV first.")
            return
        if self.selected_content is None:
            try:
                record = get_result_csv(self.selected_csv["id"])
                self.selected_content = base64.b64decode(record["content_base64"])
            except Exception as exc:
                messagebox.showerror("Results API Error", str(exc))
                return
        destination = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"{Path(self.selected_csv['filename']).stem}_head{self.preview_row_count()}.csv",
        )
        if not destination:
            return
        try:
            delimiter, rows = self.read_csv_bytes(self.selected_content)
            with Path(destination).open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle, delimiter=delimiter)
                writer.writerows(rows[:self.preview_row_count() + 1])
            messagebox.showinfo("Exported", f"Saved to {destination}")
        except OSError as exc:
            messagebox.showerror("Export Error", str(exc))