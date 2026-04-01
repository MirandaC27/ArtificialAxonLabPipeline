import json
import tkinter as tk
from tkinter import messagebox


class AutoFillUtil:
    def __init__(self):
        self.selected_config = None

    def set_selected_config(self, config_path):
        self.selected_config = config_path

    def _find_app_root(self, root):
        current = root
        while hasattr(current, "master") and current.master is not None:
            current = current.master
        return current

    def parse_config_data(self, data):
        image_type = data.get("ImageType", data.get("image_type", "3D"))
        microscope = data.get("Microscope", data.get("microscope", "Keyence"))

        folders = []
        if isinstance(data.get("selected_folders"), list):
            folders.extend(data["selected_folders"])
        if isinstance(data.get("Tracks"), list):
            folders.extend(data["Tracks"])
        if isinstance(data.get("Data"), list):
            folders.extend(data["Data"])
        if isinstance(data.get("Tracks1"), list):
            folders.extend(data["Tracks1"])

        folders = list(dict.fromkeys(folders))

        channels = []
        for ch in data.get("Channels", []):
            label = str(ch.get("label", ""))
            code = str(ch.get("code", "")).upper()
            num = None
            if code.startswith("CH"):
                try:
                    num = int(code[2:])
                except ValueError:
                    num = None
            elif isinstance(ch.get("num"), int):
                num = ch["num"]

            if num is not None and label:
                channels.append({"num": num, "label": label})

        channels = sorted(channels, key=lambda x: x["num"])

        return {
            "image_type": image_type,
            "microscope": microscope,
            "folders": folders,
            "channels": channels
        }

    def autofill_and_navigate(self, root):
        if not self.selected_config:
            messagebox.showwarning("Warning", "Select a config first")
            return

        try:
            data = json.loads(self.selected_config.read_text())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read config: {e}")
            return

        parsed = self.parse_config_data(data)

        app_root = self._find_app_root(root)


        # Navigate to Upload page
        app_root.show_page("Upload")

        upload_page = app_root.pages.get("Upload")
        if not upload_page:
            messagebox.showerror("Error", "Upload page not found")
            return

        try:
            upload_page.apply_config_data(parsed)
            messagebox.showinfo("Success", "Autofill complete!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply config: {e}")