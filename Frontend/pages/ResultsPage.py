import base64
import csv
import io
import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from api_client import (
    BASE_URL,
    delete_result_csv,
    get_analysis_job,
    get_result_csv,
    get_result_csvs,
    reorder_result_csvs,
    result_artifact_type,
    save_result_csv,
    start_analysis_job,
)
from state import masking_data, settings_data, upload_data


class ResultsPage(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg="white")
        self.controller = controller
        self.selected_csv = None
        self.selected_content = None
        self.selected_label = None
        self.preview_image = None
        self.csv_order = []
        self.experiment_groups = {}
        self.expanded_experiments = set()
        self.results_list_initialized = False
        self.item_height = 45
        self.drag_data = {"widget": None, "start_y": 0, "start_index": -1, "csv": None}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.left_frame = tk.Frame(self, bg="white")
        self.left_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        tk.Button(
            self.left_frame,
            text="Back",
            command=self.controller.return_from_results,
            font=("Arial", 12),
            width=12,
        ).pack(anchor="w", pady=5)

        list_container = tk.Frame(self.left_frame, bg="white")
        list_container.pack(fill="both", expand=True, pady=10)
        scrollbar = tk.Scrollbar(list_container, orient="vertical")
        self.canvas = tk.Canvas(
            list_container,
            yscrollcommand=scrollbar.set,
            width=240,
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
        self.rows_var = tk.StringVar(value="")
        rows_frame = tk.Frame(self.left_frame, bg="white")
        rows_frame.pack(side="bottom", fill="x", pady=5)
        tk.Label(rows_frame, text="Rows (blank = all):", bg="white", font=("Arial", 9)).pack(side="left")
        self.rows_entry = tk.Entry(rows_frame, textvariable=self.rows_var, width=5)
        self.rows_entry.pack(side="left", padx=4)
        self.rows_entry.bind("<Return>", lambda _event: self.refresh_preview())
        self.rows_entry.bind("<FocusOut>", lambda _event: self.refresh_preview())

        self.right_frame = tk.Frame(self, bg="white")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.preview_title = tk.Label(self.right_frame, text="Select an artifact", font=("Arial", 22, "bold"), bg="white")
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
        self.download_button = tk.Button(bottom, text="Download", command=self.export_head)
        self.download_button.grid(row=0, column=0, padx=5, sticky="ew")
        self.run_button = tk.Button(bottom, text="Run Analysis", command=self.run_analysis)
        self.run_button.grid(row=0, column=1, padx=5, sticky="ew")
        tk.Button(bottom, text="Next", command=lambda: self.controller.show_page("SessionEnd")).grid(row=0, column=2, padx=5, sticky="ew")
        self.analysis_status = tk.StringVar(value="Ready")
        tk.Label(
            bottom,
            textvariable=self.analysis_status,
            bg="white",
            anchor="w",
        ).grid(row=1, column=0, columnspan=3, padx=5, pady=(8, 2), sticky="ew")
        self.analysis_progress = ttk.Progressbar(bottom, mode="determinate", maximum=100)
        self.analysis_progress.grid(row=2, column=0, columnspan=3, padx=5, sticky="ew")

    def select_artifact_type(self, artifact_type):
        matches = [
            record for record in self.csv_order
            if result_artifact_type(record) == artifact_type
        ]
        if not matches:
            return False
        self.selected_csv = max(matches, key=lambda record: record.get("id", 0))
        self.expanded_experiments.add(
            self.selected_csv.get("experiment") or "Other"
        )
        self.render_csv_list()
        self.load_selected_content()
        return True

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
        self.experiment_groups = {}
        for record in self.csv_order:
            experiment = record.get("experiment") or "Other"
            self.experiment_groups.setdefault(experiment, []).append(record)
        experiments = sorted(
            self.experiment_groups,
            key=lambda value: (value == "Other", value),
        )
        if not self.csv_order:
            tk.Label(self.csv_list_frame, text="No analysis artifacts stored.", bg="white", fg="gray40").pack(padx=10, pady=10)
            return
        if not self.results_list_initialized:
            initial_experiment = (
                (self.selected_csv.get("experiment") or "Other")
                if self.selected_csv else experiments[0]
            )
            self.expanded_experiments.add(initial_experiment)
            self.results_list_initialized = True
        for experiment in experiments:
            expanded = experiment in self.expanded_experiments
            tk.Button(
                self.csv_list_frame,
                text=f"{'▼' if expanded else '▶'}  {experiment}",
                command=lambda value=experiment: self.toggle_experiment(value),
                anchor="w",
                relief="flat",
                bd=0,
                bg="#f0f0f0",
                activebackground="#e4e4e4",
                font=("Arial", 10, "bold"),
                padx=8,
                pady=7,
            ).pack(fill="x", padx=2, pady=(3, 0))
            if not expanded:
                continue
            for record in self.experiment_groups[experiment]:
                selected = (
                    self.selected_csv is not None
                    and record.get("id") == self.selected_csv.get("id")
                )
                tk.Button(
                    self.csv_list_frame,
                    text=self.artifact_label(record),
                    command=lambda value=record: self.select_result(value),
                    anchor="w",
                    justify="left",
                    relief="flat",
                    bd=0,
                    bg="#dce9f5" if selected else "white",
                    activebackground="#e8f1f8",
                    font=("Arial", 9),
                    padx=22,
                    pady=5,
                    wraplength=195,
                ).pack(fill="x", padx=2)
            tk.Frame(
                self.csv_list_frame, height=1, bg="#d0d0d0"
            ).pack(fill="x", padx=6)
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

    def toggle_experiment(self, experiment):
        if experiment in self.expanded_experiments:
            self.expanded_experiments.remove(experiment)
        else:
            self.expanded_experiments.add(experiment)
        self.render_csv_list()

    def select_result(self, record):
        self.selected_csv = record
        self.render_csv_list()
        self.load_selected_content()

    def artifact_label(self, record):
        labels = {
            "fov_summary": "FOV Summary (Final CSV)",
            "well_summary": "Well Summary",
            "wrapping_details": "Wrapping Analysis",
            "excel": "Excel Workbook",
            "uploaded": "Uploaded CSV",
            "csv": "CSV File",
        }
        artifact_type = result_artifact_type(record)
        label = labels.get(
            artifact_type,
            str(record.get("artifact_type") or "Analysis Output")
            .replace("_", " ").title(),
        )
        if artifact_type == "fov_summary":
            created_date = str(record.get("created_at") or "")[:10]
            if created_date:
                return f"{label} — {created_date}"
        return label

    def friendly_filename(self, record):
        experiment = record.get("experiment") or "Other"
        artifact_type = result_artifact_type(record)
        names = {
            "fov_summary": f"{experiment}_final_results.csv",
            "well_summary": f"{experiment}_well_summary.csv",
            "wrapping_details": f"{experiment}_wrapping_analysis.csv",
            "excel": f"{experiment}_summaries.xlsx",
        }
        return names.get(artifact_type, record.get("filename") or "analysis_output")

    def select_experiment(self):
        self.selected_csv = None
        self.selected_content = None
        self.populate_artifact_dropdown()
        if self.selected_csv:
            self.expanded_experiments.add(
                self.selected_csv.get("experiment") or "Other"
            )
            self.render_csv_list()
            self.load_selected_content()
        else:
            self.clear_preview()

    def populate_artifact_dropdown(self):
        records = self.experiment_groups.get(self.experiment_var.get(), [])
        self.artifact_options = {}
        for record in records:
            base = self.artifact_label(record)
            label = base
            suffix = 2
            while label in self.artifact_options:
                label = f"{base} ({suffix})"
                suffix += 1
            self.artifact_options[label] = record
        values = list(self.artifact_options)
        self.artifact_dropdown["values"] = values
        selected_id = self.selected_csv.get("id") if self.selected_csv else None
        selected_label = next(
            (
                label for label, record in self.artifact_options.items()
                if record.get("id") == selected_id
            ),
            values[-1] if values else "",
        )
        self.artifact_var.set(selected_label)
        self.selected_csv = (
            self.artifact_options.get(selected_label) if selected_label else None
        )

    def select_artifact(self):
        record = self.artifact_options.get(self.artifact_var.get())
        if not record:
            return
        self.selected_csv = record
        self.load_selected_content()

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
        value = self.rows_var.get().strip()
        if not value:
            return None
        try:
            count = int(value)
        except ValueError:
            return None
        return count if count > 0 else None

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
        mime_type = self.selected_csv.get("mime_type") or "text/csv"
        filename = self.selected_csv["filename"]
        self.preview_title.config(text=self.artifact_label(self.selected_csv))
        if mime_type.startswith("image/"):
            try:
                encoded = base64.b64encode(self.selected_content).decode("ascii")
                self.preview_image = tk.PhotoImage(data=encoded)
                self.preview_text.config(state="normal")
                self.preview_text.delete("1.0", tk.END)
                self.preview_text.image_create("1.0", image=self.preview_image)
                self.preview_text.config(state="disabled")
            except tk.TclError as exc:
                messagebox.showerror("Image Preview Error", str(exc))
            return
        if mime_type != "text/csv":
            self.preview_image = None
            display_filename = self.friendly_filename(self.selected_csv)
            self.set_preview(
                f"{display_filename}\n\nType: {mime_type}\n"
                f"Size: {len(self.selected_content):,} bytes\n\nUse Download to save and open this artifact."
            )
            return
        try:
            delimiter, rows = self.read_csv_bytes(self.selected_content)
            header = rows[0] if rows else []
            row_limit = self.preview_row_count()
            body = rows[1:] if row_limit is None else rows[1:row_limit + 1]
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
            self.preview_title.config(text=self.artifact_label(self.selected_csv))
            self.set_preview("\n".join(lines))
        except Exception as exc:
            messagebox.showerror("CSV Error", str(exc))

    def set_preview(self, value):
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", value)
        self.preview_text.config(state="disabled")

    def clear_preview(self):
        self.preview_image = None
        self.preview_title.config(text="Select an artifact")
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
        mime_type = self.selected_csv.get("mime_type") or "text/csv"
        if mime_type != "text/csv":
            suffix = Path(self.selected_csv["filename"]).suffix
            destination = filedialog.asksaveasfilename(
                defaultextension=suffix,
                initialfile=self.friendly_filename(self.selected_csv),
            )
            if not destination:
                return
            try:
                Path(destination).write_bytes(self.selected_content)
                messagebox.showinfo("Downloaded", f"Saved to {destination}")
            except OSError as exc:
                messagebox.showerror("Download Error", str(exc))
            return
        row_limit = self.preview_row_count()
        export_suffix = "all" if row_limit is None else f"head{row_limit}"
        destination = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=(
                f"{Path(self.friendly_filename(self.selected_csv)).stem}"
                f"_{export_suffix}.csv"
            ),
        )
        if not destination:
            return
        try:
            delimiter, rows = self.read_csv_bytes(self.selected_content)
            with Path(destination).open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle, delimiter=delimiter)
                writer.writerows(rows if row_limit is None else rows[:row_limit + 1])
            messagebox.showinfo("Exported", f"Saved to {destination}")
        except OSError as exc:
            messagebox.showerror("Export Error", str(exc))
    def run_analysis(self):
        try:
            job = start_analysis_job(
                dict(upload_data),
                dict(settings_data),
                dict(masking_data),
            )
            self.analysis_job_id = job["id"]
            self.run_button.config(state="disabled", text="Queued...")
            self.analysis_progress["value"] = job.get("progress", 0)
            self.analysis_status.set(job.get("progress_message") or "Queued for Docker analysis")
            self.after(1000, self.poll_analysis_job)
        except Exception as exc:
            self._analysis_failed(str(exc))

    def poll_analysis_job(self):
        try:
            job = get_analysis_job(self.analysis_job_id)
        except Exception as exc:
            self._analysis_failed(str(exc))
            return
        status = job.get("status")
        progress = int(job.get("progress") or 0)
        message = job.get("progress_message") or status.title()
        self.analysis_progress["value"] = progress
        self.analysis_status.set(f"{progress}% — {message}")
        if status in {"queued", "running"}:
            self.run_button.config(text=f"Running... {progress}%")
            self.after(2000, self.poll_analysis_job)
            return
        if status == "completed":
            self._analysis_complete({
                "record": {"id": job.get("result_id")},
                "row_count": job.get("row_count", 0),
                "artifact_count": len(job.get("artifact_ids") or []),
            })
            return
        self._analysis_failed(job.get("error") or "Docker analysis failed.")

    def _analysis_complete(self, summary):
        self.run_button.config(state="normal", text="Run Analysis")
        self.analysis_progress["value"] = 100
        self.analysis_status.set("100% — Analysis complete")
        self.refresh()
        record_id = (summary.get("record") or {}).get("id")
        self.selected_csv = next(
            (item for item in self.csv_order if item.get("id") == record_id),
            None,
        )
        if self.selected_csv:
            self.expanded_experiments.add(
                self.selected_csv.get("experiment") or "Other"
            )
            self.render_csv_list()
            self.load_selected_content()
        messagebox.showinfo(
            "Analysis Complete",
            f"Analysis artifacts saved to PostgreSQL: {summary.get('artifact_count', 0)}\n"
            f"FOV rows: {summary.get('row_count', 0)}",
        )

    def _analysis_failed(self, message):
        self.run_button.config(state="normal", text="Run Analysis")
        self.analysis_status.set("Analysis failed")
        messagebox.showerror("Analysis Error", message)
