import tkinter as tk
from tkinter import messagebox
from pathlib import Path

CONFIG_DIR = Path("../configs")

selected_config = None


def get_all_configs():
    config_listbox.delete(0, tk.END)

    configs = list(CONFIG_DIR.glob("*.json"))

    for config in configs:
        config_listbox.insert(tk.END, config.name)


def create_config():
    name = filename_entry.get().strip()

    if not name:
        messagebox.showerror("Error", "Enter a file name")
        return

    if not name.endswith(".json"):
        name += ".json"

    path = CONFIG_DIR / name

    if path.exists():
        messagebox.showerror("Error", "File already exists")
        return

    with open(path, "w") as f:
        f.write("{}")

    get_all_configs()
    filename_entry.delete(0, tk.END)


def save_config():
    global selected_config

    if not selected_config:
        messagebox.showwarning("Warning", "No config loaded")
        return

    content = "test config data"

    with open(selected_config, "w") as f:
        f.write(content)

    messagebox.showinfo("Saved", "Config updated")


def delete_config():
    selection = config_listbox.curselection()

    if not selection:
        messagebox.showwarning("Warning", "Select a config to delete")
        return

    filename = config_listbox.get(selection[0])
    path = CONFIG_DIR / filename

    confirm = messagebox.askyesno("Confirm Delete", f"Delete '{filename}'?")

    if not confirm:
        return

    try:
        if path.exists():
            path.unlink()

        get_all_configs()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete file:\n{e}")


root = tk.Tk()
root.title("Config Manager")
root.geometry("600x300")


config_listbox = tk.Listbox(root, width=20, height=10)
config_listbox.grid(row=0, column=0, padx=10, pady=5, rowspan=6)

button_frame = tk.Frame(root)
button_frame.grid(row=10, column=0, pady=5)

save_button = tk.Button(button_frame, text="Save", command=create_config)
save_button.pack(side="left", padx=5)

delete_button = tk.Button(button_frame, text="Delete", command=delete_config)
delete_button.pack(side="left", padx=5)

load_button = tk.Button(button_frame, text="Load")
load_button.pack(side="left", padx=5)


filename_label = tk.Label(root, text="New Config Name")
filename_label.grid(row=8, column=0)

filename_entry = tk.Entry(root, width=20)
filename_entry.grid(row=9, column=0, pady=5)

get_all_configs()

root.mainloop()