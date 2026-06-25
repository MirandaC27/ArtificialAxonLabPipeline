import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
from zoneinfo import ZoneInfo

from api_client import get_recent_upload_step1, save_config


class HistoryPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        self.uploads = []
        self.selected_upload = None
        self.selected_label = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.left_frame = tk.Frame(self, bg="white")
        self.left_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)

        tk.Button(
            self.left_frame,
            text="Cancel",
            command=lambda: controller.show_page("Home"),
            font=("Arial", 12),
            width=12
        ).pack(anchor="w", pady=5)

        self.list_frame = tk.Frame(self.left_frame, bg="white")
        self.list_frame.pack(fill="both", expand=True, pady=10)

        tk.Button(
            self.left_frame,
            text="Save Config",
            command=self.save_current_config,
            font=("Arial", 12),
            width=12
        ).pack(side="bottom", pady=10)

        self.right_frame = tk.Frame(self, bg="white")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)

        self.preview_title = tk.Label(
            self.right_frame,
            text="Select a session",
            font=("Arial", 28, "bold"),
            bg="white"
        )
        self.preview_title.pack(pady=(20, 10))

        self.preview_box = tk.Text(
            self.right_frame,
            font=("Courier New", 12),
            bg="white",
            wrap="word",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#d9d9d9",
            padx=12,
            pady=12
        )
        self.preview_box.pack(fill="both", expand=True, padx=20, pady=10)
        self.preview_box.config(state="disabled")

    def refresh(self):
        self.load_uploads()

    def load_uploads(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        self.selected_upload = None
        self.selected_label = None
        self.preview_title.config(text="Select a session")
        self.preview_box.config(state="normal")
        self.preview_box.delete("1.0", tk.END)
        self.preview_box.config(state="disabled")

        try:
            self.uploads = get_recent_upload_step1()

        except Exception as e:
            tk.Label(
                self.list_frame,
                text=f"Error loading history:\n{e}",
                bg="white",
                fg="red"
            ).pack()
            return

        if not self.uploads:
            tk.Label(
                self.list_frame,
                text="No sessions found.",
                bg="white"
            ).pack()
            return

        for upload in self.uploads:
            item = tk.Label(
                self.list_frame,
                text=f"-> Session {upload['id']}",
                anchor="w",
                padx=10,
                pady=8,
                bg="white",
                cursor="hand2",
                font=("Arial", 11)
            )

            item.pack(fill="x")

            item.bind(
                "<Button-1>",
                lambda e, u=upload: self.select_upload(e, u)
            )

            tk.Frame(
                self.list_frame,
                height=1,
                bg="#ccc"
            ).pack(fill="x", padx=5, pady=2)

    def select_upload(self, event, upload):
        self.selected_upload = upload

        if self.selected_label and self.selected_label.winfo_exists():
            self.selected_label.config(bg="white")

        self.selected_label = event.widget
        self.selected_label.config(bg="#e0e0e0")

        self.show_upload_preview(upload)

    def show_upload_preview(self, upload):
        self.preview_title.config(
            text=f"Session {upload.get('id', 'N/A')}"
        )

        text = self.format_upload_text(upload)

        self.preview_box.config(state="normal")
        self.preview_box.delete("1.0", tk.END)
        self.preview_box.insert("1.0", text)
        self.preview_box.config(state="disabled")

    def format_upload_text(self, upload):
        created_at = upload.get("created_at", "N/A")

        if created_at != "N/A":
            try:
                created_at = (
                    datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    .astimezone(ZoneInfo("America/New_York"))
                    .strftime("%Y-%m-%d %I:%M %p")
                )
            except Exception:
                created_at = created_at[:16].replace("T", " ")

        return "\n".join([
            f"Session ID: {upload.get('id', 'N/A')}",
            f"Created At: {created_at}",
            "",
            f"Image Type: {upload.get('image_type', 'N/A')}",
            f"Microscope: {upload.get('microscope', 'N/A')}",
            f"Number of FOVs: {upload.get('num_fovs', 'N/A')}",
            f"Disabled FOVs: {self.format_list(upload.get('disabled_fovs'))}",
            "",
            "Channels:",
            self.format_channels(upload.get("channels")),
            "",
            f"Folders: {self.format_list(upload.get('folders'))}",
            f"Raw Tracks: {self.format_list(upload.get('tracks'))}",
            f"Cleaned Tracks: {self.format_list(upload.get('tracks1'))}",
            f"Ordered Tracks: {self.format_list(upload.get('ordered_track'))}",
            f"Data Folders: {self.format_list(upload.get('data'))}",
        ])

    def format_list(self, values):
        if not values:
            return "None"

        return "\n  - " + "\n  - ".join(str(value) for value in values)

    def format_channels(self, channels):
        if not channels:
            return "  None"

        lines = []

        for channel in channels:
            code = channel.get("code", "N/A")
            label = channel.get("label", "N/A")
            status = "active" if channel.get("active", True) else "disabled"
            lines.append(f"  - {code}: {label} ({status})")

        return "\n".join(lines)

    def upload_config_payload(self, upload):
        fields = [
            "folders",
            "tracks",
            "tracks1",
            "ordered_track",
            "data",
            "image_type",
            "microscope",
            "num_fovs",
            "disabled_fovs",
            "channels",
        ]

        return {field: upload.get(field) for field in fields}

    def save_current_config(self):
        if not self.selected_upload:
            messagebox.showerror("Selection Error", "Select a session first.")
            return

        config_name = simpledialog.askstring(
            "Save Config",
            "Enter config name:"
        )

        if not config_name:
            return

        try:
            save_config(
                config_name,
                self.upload_config_payload(self.selected_upload)
            )

            messagebox.showinfo("Saved", "Config saved successfully.")

        except Exception as e:
            messagebox.showerror("Save Error", str(e))
