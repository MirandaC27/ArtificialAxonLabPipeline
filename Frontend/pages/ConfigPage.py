import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from zoneinfo import ZoneInfo
from copy import deepcopy

from state import (
    upload_data,
    settings_data,
    reset_history_state
)
from api_client import get_configs, reorder_configs


class ConfigPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")

        self.controller = controller

        self.configs = []
        self.config_labels = []

        self.selected_config = None
        self.selected_label = None

        self.drag_start_index = None
        self.drag_current_label = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_left_side()
        self.build_preview_side()

    def build_left_side(self):
        self.left_frame = tk.Frame(
            self,
            bg="white"
        )
        self.left_frame.grid(
            row=0,
            column=0,
            sticky="ns",
            padx=10,
            pady=10
        )

        tk.Button(
            self.left_frame,
            text="Cancel",
            command=lambda:
            self.controller.show_page("Home"),
            font=("Arial", 12),
            width=12
        ).pack(
            anchor="w",
            pady=5
        )

        self.list_canvas = tk.Canvas(
            self.left_frame,
            bg="white",
            highlightthickness=0,
            width=240
        )
        self.list_canvas.pack(
            side="left",
            fill="both",
            expand=True,
            pady=10
        )

        self.list_scrollbar = tk.Scrollbar(
            self.left_frame,
            orient="vertical",
            command=self.list_canvas.yview
        )
        self.list_scrollbar.pack(
            side="right",
            fill="y",
            pady=10
        )

        self.list_canvas.configure(
            yscrollcommand=self.list_scrollbar.set
        )

        self.list_frame = tk.Frame(
            self.list_canvas,
            bg="white"
        )

        self.list_window = self.list_canvas.create_window(
            (0, 0),
            window=self.list_frame,
            anchor="nw"
        )

        self.list_frame.bind(
            "<Configure>",
            self._update_list_scrollregion
        )

        self.list_canvas.bind(
            "<Configure>",
            self._resize_list_frame
        )

        tk.Button(
            self.left_frame,
            text="Autofill",
            command=self.autofill_selected_config,
            font=("Arial", 12),
            width=12
        ).pack(
            side="bottom",
            pady=5
        )

    def build_preview_side(self):
        self.right_frame = tk.Frame(
            self,
            bg="white"
        )
        self.right_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=20,
            pady=10
        )

        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)

        self.preview_title = tk.Label(
            self.right_frame,
            text="Select a config",
            font=("Arial", 28, "bold"),
            bg="white"
        )
        self.preview_title.grid(
            row=0,
            column=0,
            columnspan=2,
            pady=(20, 10)
        )

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
        self.preview_box.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(20, 0),
            pady=10
        )

        self.preview_scrollbar = tk.Scrollbar(
            self.right_frame,
            orient="vertical",
            command=self.preview_box.yview
        )
        self.preview_scrollbar.grid(
            row=1,
            column=1,
            sticky="ns",
            padx=(0, 20),
            pady=10
        )

        self.preview_box.configure(
            yscrollcommand=self.preview_scrollbar.set,
            state="disabled"
        )

    def _update_list_scrollregion(self, event=None):
        self.list_canvas.configure(
            scrollregion=self.list_canvas.bbox("all")
        )

    def _resize_list_frame(self, event):
        self.list_canvas.itemconfigure(
            self.list_window,
            width=event.width
        )

    def refresh(self):
        self.load_configs()

    def clear_preview(self):
        self.preview_title.config(
            text="Select a config"
        )

        self.preview_box.config(
            state="normal"
        )
        self.preview_box.delete(
            "1.0",
            tk.END
        )
        self.preview_box.config(
            state="disabled"
        )

    def load_configs(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        self.config_labels = []
        self.selected_config = None
        self.selected_label = None

        self.clear_preview()

        try:
            self.configs = get_configs()

        except Exception as e:
            tk.Label(
                self.list_frame,
                text=f"Error loading configs:\n{e}",
                bg="white",
                fg="red",
                justify="left"
            ).pack(
                fill="x",
                padx=5,
                pady=5
            )
            return

        if not self.configs:
            tk.Label(
                self.list_frame,
                text="No saved configs.",
                bg="white"
            ).pack(
                fill="x",
                padx=5,
                pady=5
            )
            return

        self.render_config_list()

    def render_config_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        self.config_labels = []

        for index, config in enumerate(self.configs):
            name = (
                config.get("config_name")
                or f"Config {config.get('id', 'N/A')}"
            )

            item = tk.Label(
                self.list_frame,
                text=f"→ {name}",
                anchor="w",
                padx=10,
                pady=8,
                bg="white",
                cursor="hand2",
                font=("Arial", 11)
            )
            item.pack(fill="x")

            self.config_labels.append(item)

            item.bind(
                "<Button-1>",
                lambda event,
                selected=config,
                selected_index=index:
                self.select_config(
                    event,
                    selected,
                    selected_index
                )
            )

            item.bind(
                "<B1-Motion>",
                self.drag_motion
            )

            item.bind(
                "<ButtonRelease-1>",
                self.drop_config
            )

            tk.Frame(
                self.list_frame,
                height=1,
                bg="#cccccc"
            ).pack(
                fill="x",
                padx=5,
                pady=2
            )

        self._update_list_scrollregion()

    def select_config(self, event, config, index):
        self.selected_config = config
        self.drag_start_index = index
        self.drag_current_label = event.widget

        if (
            self.selected_label
            and self.selected_label.winfo_exists()
        ):
            self.selected_label.config(
                bg="white"
            )

        self.selected_label = event.widget
        self.selected_label.config(
            bg="#e0e0e0"
        )

        self.show_preview(config)

    def drag_motion(self, event):
        if self.drag_current_label:
            self.drag_current_label.config(
                bg="#cce5ff"
            )

    def drop_config(self, event):
        if self.drag_start_index is None:
            return

        mouse_y = self.list_frame.winfo_pointery()
        drop_index = self.drag_start_index

        for index, label in enumerate(self.config_labels):
            top = label.winfo_rooty()
            bottom = top + label.winfo_height()

            if top <= mouse_y <= bottom:
                drop_index = index
                break

        if drop_index != self.drag_start_index:
            moved_config = self.configs.pop(
                self.drag_start_index
            )

            self.configs.insert(
                drop_index,
                moved_config
            )

            self.save_new_order()

        self.drag_start_index = None
        self.drag_current_label = None
        self.selected_label = None

        self.render_config_list()

    def save_new_order(self):
        try:
            config_ids = [
                config["id"]
                for config in self.configs
            ]

            reorder_configs(config_ids)

            for index, config in enumerate(self.configs):
                config["order_index"] = index

        except Exception as e:
            messagebox.showerror(
                "Reorder Error",
                str(e)
            )

            self.load_configs()

    def show_preview(self, config):
        self.preview_title.config(
            text=config.get(
                "config_name",
                "Unnamed"
            )
        )

        self.preview_box.config(
            state="normal"
        )
        self.preview_box.delete(
            "1.0",
            tk.END
        )
        self.preview_box.insert(
            "1.0",
            self.format_config_text(config)
        )
        self.preview_box.config(
            state="disabled"
        )

        self.preview_box.yview_moveto(0)

    def format_config_text(self, config):
        created_at = self.format_created_at(
            config.get("created_at")
        )

        settings = config.get("settings_data")

        if not isinstance(settings, dict):
            settings = {}

        return "\n".join([
            f"Config ID: {config.get('id', 'N/A')}",
            f"Name: {config.get('config_name', 'N/A')}",
            f"Created At: {created_at}",
            f"Order: {config.get('order_index', 'N/A')}",

            "",

            "UPLOAD SETTINGS",
            "---------------",
            f"Image Type: {config.get('image_type', 'N/A')}",
            f"Microscope: {config.get('microscope', 'N/A')}",
            f"Number of FOVs: {config.get('num_fovs', 'N/A')}",
            (
                "Disabled FOVs:"
                f"{self.format_list(config.get('disabled_fovs'))}"
            ),

            "",

            "EXPERIMENT SETTINGS",
            "-------------------",
            self.format_settings(settings),

            "",

            "CHANNELS",
            "--------",
            self.format_channels(config.get("channels")),

            "",

            "DIRECTORIES",
            "-----------",
            (
                "Folders:"
                f"{self.format_list(config.get('folders'))}"
            ),
            (
                "Raw Tracks:"
                f"{self.format_list(config.get('tracks'))}"
            ),
            (
                "Cleaned Tracks:"
                f"{self.format_list(config.get('tracks1'))}"
            ),
            (
                "Ordered Tracks:"
                f"{self.format_list(config.get('ordered_track'))}"
            ),
            (
                "Data Folders:"
                f"{self.format_list(config.get('data'))}"
            )
        ])

    def format_created_at(self, value):
        if not value:
            return "N/A"

        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            return (
                parsed
                .astimezone(
                    ZoneInfo("America/New_York")
                )
                .strftime("%Y-%m-%d %I:%M %p")
            )

        except Exception:
            return str(value)

    def format_list(self, values):
        if not values:
            return "\n  None"

        return (
            "\n  - "
            + "\n  - ".join(
                str(value)
                for value in values
            )
        )

    def format_channels(self, channels):
        if not channels:
            return "  None"

        lines = []

        for channel in channels:
            if not isinstance(channel, dict):
                lines.append(
                    f"  - {channel}"
                )
                continue

            code = channel.get(
                "code",
                "N/A"
            )
            label = channel.get(
                "label",
                "N/A"
            )

            status = (
                "active"
                if channel.get("active", True)
                else "disabled"
            )

            lines.append(
                f"  - {code}: {label} ({status})"
            )

        return "\n".join(lines)

    def format_settings(self, settings):
        if not settings:
            return "  None"

        return "\n".join([
            (
                "  - Experiment: "
                f"{settings.get('experiment', 'N/A')}"
            ),
            (
                "  - Frames: "
                f"{settings.get('frames', 'N/A')}"
            ),
            (
                "  - Distance: "
                f"{settings.get('distance', 'N/A')}"
            ),
            (
                "  - Run Ezra: "
                f"{settings.get('run_ezra', 'N/A')}"
            )
        ])

    def autofill_selected_config(self):
        if not self.selected_config:
            messagebox.showerror(
                "Selection Error",
                "Select a config first."
            )
            return

        for field in upload_data:
            if field in self.selected_config:
                upload_data[field] = deepcopy(
                    self.selected_config[field]
                )

        saved_settings = self.selected_config.get(
            "settings_data"
        )

        if not isinstance(saved_settings, dict):
            saved_settings = {}

        for field in settings_data:
            if field in saved_settings:
                settings_data[field] = deepcopy(
                    saved_settings[field]
                )

        reset_history_state()

        messagebox.showinfo(
            "Autofilled",
            "Config loaded into the upload and settings forms."
        )

        self.controller.show_page("Upload")