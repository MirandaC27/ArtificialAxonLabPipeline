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
        num_fovs = data.get("NumFOVs", data.get("num_fovs", 0))

        if not isinstance(num_fovs, int):
            try:
                num_fovs = int(str(num_fovs).strip())
            except (TypeError, ValueError):
                num_fovs = 0

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
        disabled_fovs = [
            str(fov).strip()
            for fov in data.get("DisabledFOVs", data.get("disabled_fovs", []))
            if str(fov).strip().isdigit()
        ]
        disabled_fovs = list(dict.fromkeys(disabled_fovs))

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
                channels.append(
                    {
                        "num": num,
                        "label": label,
                        "disabled": not ch.get("active", True),
                    }
                )

        channels = sorted(channels, key=lambda x: x["num"])

        return {
            "image_type": image_type,
            "microscope": microscope,
            "folders": folders,
            "channels": channels,
            "num_fovs": num_fovs,
            "disabled_fovs": disabled_fovs,
        }

    def load_selected_config(self):
        if not self.selected_config:
            raise ValueError("Select a config first")

        data = json.loads(self.selected_config.read_text())
        return self.parse_config_data(data)

    def autofill_and_navigate(self, root, autorun=False, show_success=True):
        if not self.selected_config:
            messagebox.showwarning("Warning", "Select a config first")
            return False

        try:
            parsed = self.load_selected_config()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read config: {e}")
            return False

        app_root = self._find_app_root(root)

        # Navigate to Upload page
        app_root.show_page("Upload")

        upload_page = app_root.pages.get("Upload")
        if not upload_page:
            messagebox.showerror("Error", "Upload page not found")
            return False

        try:
            upload_page.apply_upload_data(parsed)
            if autorun:
                upload_page.button_run()
            elif show_success:
                messagebox.showinfo("Success", "Autofill complete!")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply config: {e}")
            return False
