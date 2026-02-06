import tkinter as tk
from tkinter import filedialog
import json

JSON_PATH = "file_paths.json"

def upload_files():
    file_paths = filedialog.askopenfilenames(
        title="Select files"
    )

    if not file_paths:
        return

    data = {
        "files": list(file_paths)
    }

    # Save paths to JSON
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    status_label.config(text=f"{len(file_paths)} file paths saved")


window = tk.Tk()
window.title("File Uploader")
window.geometry("600x300")

tk.Button(window, text="Upload File Paths", command=upload_files).pack(pady=120)

status_label = tk.Label(window, text="")
status_label.pack(pady=5)

window.mainloop()