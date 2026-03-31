import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import json
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from controller.AutoFillUtil import AutoFillUtil


class ConfigPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        self.af = AutoFillUtil()

        self.CONFIG_DIR = Path("../data/configs")
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        self.currentConfig = Path("../data/folder_paths.json")
        self.ORDER_FILE = Path("../data/config_order.json")

        self.selected_config = None
        self.selected_label = None
        self.config_order = []

        self.ITEM_HEIGHT = 45
        self.drag_data = {"widget": None, "start_y": 0, "start_index": -1, "config": None}

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left Side
        self.left_frame = tk.Frame(self, bg="white")
        self.left_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)

        tk.Button(
            self.left_frame,
            text="Cancel",
            command=lambda: controller.show_page("Home"),
            font=("Arial", 12),
            width=12
        ).pack(anchor="w", pady=5)

        self.list_container = tk.Frame(self.left_frame, bg="white")
        self.list_container.pack(fill="both", expand=True, pady=10)

        self.scrollbar = tk.Scrollbar(self.list_container, orient="vertical")
        self.canvas = tk.Canvas(
            self.list_container,
            yscrollcommand=self.scrollbar.set,
            width=220,
            bg="white",
            highlightthickness=0
        )

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.canvas.yview)

        self.config_list_frame = tk.Frame(self.canvas, bg="white")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.config_list_frame, anchor="nw")

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.config_list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Bottom controls
        tk.Button(self.left_frame, text="Load", command=self.load_config).pack(side="bottom", fill="x", pady=2)
        tk.Button(self.left_frame, text="Delete", command=self.delete_config).pack(side="bottom", fill="x", pady=2)
        tk.Button(self.left_frame, text="Save", command=self.create_config).pack(side="bottom", fill="x", pady=2)

        self.filename_entry = tk.Entry(self.left_frame)
        self.filename_entry.pack(side="bottom", fill="x", pady=5)

        # Right Side
        self.right_frame = tk.Frame(self, bg="white")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)

        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.preview_title = tk.Label(
            self.right_frame,
            text="Select a config",
            font=("Arial", 22, "bold"),
            bg="white"
        )
        self.preview_title.grid(row=0, column=0, pady=(0, 5))

        self.preview_text = tk.Text(self.right_frame, wrap="word", bg="#f5f5f5")
        self.preview_text.grid(row=1, column=0, sticky="nsew", padx=20)

        bottom_frame = tk.Frame(self.right_frame, bg="white")
        bottom_frame.grid(row=2, column=0, pady=10)

        tk.Button(
            bottom_frame,
            text="Autofill",
            width=12,
            command=lambda: self.af.autofill_and_navigate(self.controller)
        ).pack(side="left", padx=5)

        tk.Button(
            bottom_frame,
            text="Auto run",
            width=12,
            bg="black",
            fg="white"
        ).pack(side="left", padx=5)

        self.get_all_configs()

   
    def save_order(self):
        try:
            self.ORDER_FILE.write_text(json.dumps([p.name for p in self.config_order]))
        except:
            pass

    def load_order(self):
        all_configs = {p.name: p for p in self.CONFIG_DIR.glob("*.json")}
        ordered = []

        if self.ORDER_FILE.exists():
            try:
                saved = json.loads(self.ORDER_FILE.read_text())
                for name in saved:
                    if name in all_configs:
                        ordered.append(all_configs.pop(name))
            except:
                pass

        ordered.extend(all_configs.values())
        return ordered

    def get_all_configs(self):
        self.config_order = self.load_order()
        self.render_config_list()


    def render_config_list(self):
        for widget in self.config_list_frame.winfo_children():
            widget.destroy()

        self.selected_label = None

        for config in self.config_order:
            item = tk.Label(
                self.config_list_frame,
                text=f"→ {config.stem}",
                anchor="w",
                padx=10,
                pady=8,
                bg="white",
                cursor="hand2"
            )
            item.pack(fill="x")

            item.bind("<ButtonPress-1>", lambda e, c=config: self.on_drag_start(e, c))
            item.bind("<B1-Motion>", self.on_drag_motion)
            item.bind("<ButtonRelease-1>", self.on_drag_release)

            tk.Frame(self.config_list_frame, height=1, bg="#ccc").pack(fill="x", padx=5, pady=2)


    def on_drag_start(self, event, config_path):
        self.drag_data = {
            "widget": event.widget,
            "start_y": event.y_root,
            "start_index": self.get_label_index(event.widget),
            "config": config_path
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
        config_path = self.drag_data["config"]

        if steps == 0:
            self.selected_config = config_path
            self.af.set_selected_config(config_path)

            if self.selected_label and self.selected_label.winfo_exists():
                self.selected_label.config(bg="white")

            self.selected_label = self.drag_data["widget"]
            self.selected_label.config(bg="#e0e0e0")

            try:
                content = config_path.read_text()
                self.preview_title.config(text=config_path.stem)
                self.preview_text.delete("1.0", tk.END)
                self.preview_text.insert(tk.END, content[:500])
            except Exception as e:
                messagebox.showerror("Error", str(e))

        else:
            target = max(0, min(len(self.config_order) - 1, start_idx + steps))
            item = self.config_order.pop(start_idx)
            self.config_order.insert(target, item)

            self.save_order()
            self.render_config_list()

        self.drag_data["widget"] = None

    def get_label_index(self, widget):
        text = widget.cget("text").replace("→ ", "").strip()
        for i, path in enumerate(self.config_order):
            if path.stem == text:
                return i
        return -1

    def load_config(self):
        if not self.selected_config:
            return messagebox.showwarning("Warning", "Select a config")

        try:
            self.currentConfig.write_text(self.selected_config.read_text())
            messagebox.showinfo("Success", f"Loaded {self.selected_config.name}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_config(self):
        if not self.selected_config:
            return

        if messagebox.askyesno("Confirm", f"Delete {self.selected_config.name}?"):
            self.selected_config.unlink()
            self.selected_config = None

            self.preview_title.config(text="Select a config")
            self.preview_text.delete("1.0", tk.END)

            self.get_all_configs()

    def create_config(self):
        name = self.filename_entry.get().strip()

        if not name:
            return

        if not name.endswith(".json"):
            name += ".json"

        path = self.CONFIG_DIR / name

        if path.exists():
            return messagebox.showerror("Error", "File already exists")

        try:
            path.write_text(self.currentConfig.read_text())
            self.filename_entry.delete(0, tk.END)
            self.get_all_configs()
        except Exception as e:
            messagebox.showerror("Error", str(e))
