import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from zoneinfo import ZoneInfo

from state import upload_data
from api_client import get_configs, reorder_configs


class ConfigPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        self.configs = []
        self.selected_config = None
        self.selected_label = None
        self.drag_start_index = None
        self.drag_current_label = None

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
            text="Autofill",
            command=self.autofill_selected_config,
            font=("Arial", 12),
            width=12
        ).pack(side="bottom", pady=5)

        self.right_frame = tk.Frame(self, bg="white")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)

        self.preview_title = tk.Label(
            self.right_frame,
            text="Select a config",
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
        self.load_configs()

    def load_configs(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        self.selected_config = None
        self.selected_label = None
        self.preview_title.config(text="Select a config")
        self.preview_box.config(state="normal")
        self.preview_box.delete("1.0", tk.END)
        self.preview_box.config(state="disabled")

        try:
            self.configs = get_configs()
        except Exception as e:
            tk.Label(
                self.list_frame,
                text=f"Error loading configs:\n{e}",
                bg="white",
                fg="red"
            ).pack()
            return

        if not self.configs:
            tk.Label(
                self.list_frame,
                text="No saved configs.",
                bg="white"
            ).pack()
            return

        self.render_config_list()

    def render_config_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for index, config in enumerate(self.configs):
            item = tk.Label(
                self.list_frame,
                text=f"-> Session {config.get('id', 'N/A')}",
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
                lambda e, c=config, i=index: self.select_config(e, c, i)
            )
            item.bind("<B1-Motion>", self.drag_motion)
            item.bind("<ButtonRelease-1>", self.drop_config)

            tk.Frame(self.list_frame, height=1, bg="#ccc").pack(
                fill="x", padx=5, pady=2
            )

    def select_config(self, event, config, index):
        self.selected_config = config
        self.drag_start_index = index
        self.drag_current_label = event.widget

        if self.selected_label and self.selected_label.winfo_exists():
            self.selected_label.config(bg="white")

        self.selected_label = event.widget
        self.selected_label.config(bg="#e0e0e0")

        self.show_preview(config)

    def drag_motion(self, event):
        if self.drag_current_label:
            self.drag_current_label.config(bg="#cce5ff")

    def drop_config(self, event):
        if self.drag_start_index is None:
            return

        mouse_y = self.list_frame.winfo_pointery()

        labels = [
            widget for widget in self.list_frame.winfo_children()
            if isinstance(widget, tk.Label)
        ]

        drop_index = self.drag_start_index

        for index, label in enumerate(labels):
            top = label.winfo_rooty()
            bottom = top + label.winfo_height()

            if top <= mouse_y <= bottom:
                drop_index = index
                break

        if drop_index != self.drag_start_index:
            moved_config = self.configs.pop(self.drag_start_index)
            self.configs.insert(drop_index, moved_config)
            self.save_new_order()

        self.drag_start_index = None
        self.drag_current_label = None

        self.render_config_list()

    def save_new_order(self):
        try:
            config_ids = [config["id"] for config in self.configs]
            reorder_configs(config_ids)
        except Exception as e:
            messagebox.showerror("Reorder Error", str(e))

    def show_preview(self, config):
        self.preview_title.config(text=config.get("config_name", "Unnamed"))

        self.preview_box.config(state="normal")
        self.preview_box.delete("1.0", tk.END)
        self.preview_box.insert("1.0", self.format_config_text(config))
        self.preview_box.config(state="disabled")

    def format_config_text(self, config):
        created_at = config.get("created_at", "N/A")

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
            f"Session ID: {config.get('id', 'N/A')}",
            f"Name: {config.get('config_name', 'N/A')}",
            f"Created At: {created_at}",
            f"Order: {config.get('order_index', 'N/A')}",
            "",
            f"Image Type: {config.get('image_type', 'N/A')}",
            f"Microscope: {config.get('microscope', 'N/A')}",
            f"Number of FOVs: {config.get('num_fovs', 'N/A')}",
            f"Disabled FOVs: {self.format_list(config.get('disabled_fovs'))}",
            "",
            "Channels:",
            self.format_channels(config.get("channels")),
            "",
            f"Folders: {self.format_list(config.get('folders'))}",
            f"Raw Tracks: {self.format_list(config.get('tracks'))}",
            f"Cleaned Tracks: {self.format_list(config.get('tracks1'))}",
            f"Ordered Tracks: {self.format_list(config.get('ordered_track'))}",
            f"Data Folders: {self.format_list(config.get('data'))}",
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

    def autofill_selected_config(self):
        if not self.selected_config:
            messagebox.showerror("Selection Error", "Select a config first.")
            return

        for field in upload_data:
            upload_data[field] = self.selected_config.get(field, upload_data[field])

        messagebox.showinfo("Autofilled", "Config loaded into the upload form.")
        self.controller.show_page("Upload")
