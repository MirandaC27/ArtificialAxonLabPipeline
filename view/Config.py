import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import json

CONFIG_DIR = Path("../data/configs")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

currentConfig = Path("../data/folder_paths.json")
ORDER_FILE = Path("../data/config_order.json")


def save_order():
    try:
        ORDER_FILE.write_text(json.dumps([p.name for p in config_order]))
    except Exception:
        pass


def load_order():
    all_configs = {p.name: p for p in CONFIG_DIR.glob("*.json")}
    ordered = []
    if ORDER_FILE.exists():
        try:
            saved = json.loads(ORDER_FILE.read_text())
            for name in saved:
                if name in all_configs:
                    ordered.append(all_configs.pop(name))
        except Exception:
            pass
    ordered.extend(all_configs.values())
    return ordered


selected_config = None
selected_label = None

config_order = []  

ITEM_HEIGHT = 45  


# Config List
def get_all_configs():
    global selected_label, config_order

    config_order = load_order()
    selected_label = None

    render_config_list()


def render_config_list():
    global selected_label

    # Clear existing widgets
    for widget in config_frame.winfo_children():
        widget.destroy()

    selected_label = None

    for config in config_order:
        item = tk.Label(config_frame, text=f"→ {config.stem}", font=("Arial", 14), anchor="w", padx=10, pady=8, cursor="hand2")
        item.pack(fill="x")
        item.bind("<ButtonPress-1>", lambda e, c=config: on_drag_start(e, c))
        item.bind("<B1-Motion>", on_drag_motion)
        item.bind("<ButtonRelease-1>", on_drag_release)

        divider = tk.Frame(config_frame, height=1, bg="#ccc")
        divider.pack(fill="x", padx=5, pady=2)

    # Update scroll region after render
    config_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

    # Shows scrollbar
    if len(config_order) > 5:
        scrollbar.pack(side="right", fill="y")
        canvas.configure(height=ITEM_HEIGHT * 5)
    else:
        scrollbar.pack_forget()
        canvas.configure(height=ITEM_HEIGHT * max(len(config_order), 1))


def on_config_click(event, config_path):
    global selected_config, selected_label

    selected_config = config_path

    if selected_label and selected_label.winfo_exists():
        selected_label.config(bg="SystemButtonFace")

    selected_label = event.widget
    selected_label.config(bg="#e0e0e0")

    try:
        content = config_path.read_text()
        preview_title.config(text=config_path.stem)
        preview_text.delete("1.0", tk.END)
        preview_text.insert(tk.END, content[:500])
    except Exception as e:
        messagebox.showerror("Error", str(e))



drag_data = {"widget": None, "start_y": 0, "start_index": -1, "config": None}


def on_drag_start(event, config_path):
    drag_data["widget"] = event.widget
    drag_data["start_y"] = event.y_root
    drag_data["start_index"] = get_label_index(event.widget)
    drag_data["config"] = config_path
    event.widget.config(bg="#b1b2b3")


def on_drag_motion(event):
    pass  


def on_drag_release(event):
    global selected_config, selected_label

    widget = drag_data["widget"]
    if widget is None or not widget.winfo_exists():
        return

    start_index = drag_data["start_index"]
    config_path = drag_data["config"]
    if start_index == -1:
        return

    delta_y = event.y_root - drag_data["start_y"]
    steps = round(delta_y / ITEM_HEIGHT)
    target_index = max(0, min(len(config_order) - 1, start_index + steps))

    if steps == 0:
        selected_config = config_path

        if selected_label and selected_label.winfo_exists():
            selected_label.config(bg="SystemButtonFace")

        selected_label = widget
        widget.config(bg="#e0e0e0")

        try:
            content = config_path.read_text()
            preview_title.config(text=config_path.stem)
            preview_text.delete("1.0", tk.END)
            preview_text.insert(tk.END, content[:500])
        except Exception as e:
            messagebox.showerror("Error", str(e))
    else:
        if start_index != target_index:
            item = config_order.pop(start_index)
            config_order.insert(target_index, item)
        save_order()
        render_config_list()

    drag_data["widget"] = None
    drag_data["start_y"] = 0
    drag_data["start_index"] = -1
    drag_data["config"] = None


def get_label_index(widget):
    """Find the index of a label widget in config_order by matching its text."""
    text = widget.cget("text").replace("→ ", "").strip()
    for i, path in enumerate(config_order):
        if path.stem == text:
            return i
    return -1



def load_config():
    if not selected_config:
        messagebox.showwarning("Warning", "Select a config")
        return
    try:
        content = selected_config.read_text()
        currentConfig.write_text(content)
        messagebox.showinfo("Success", f"Loaded {selected_config.name}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def delete_config():
    global selected_config

    if not selected_config:
        messagebox.showwarning("Warning", "Select a config")
        return

    confirm = messagebox.askyesno("Confirm", f"Delete {selected_config.name}?")
    if not confirm:
        return

    try:
        selected_config.unlink()
        selected_config = None
        get_all_configs()
        preview_title.config(text="Select a config")
        preview_text.delete("1.0", tk.END)
    except Exception as e:
        messagebox.showerror("Error", str(e))


def create_config():
    name = filename_entry.get().strip()

    if not name:
        messagebox.showerror("Error", "Enter a name")
        return

    if not name.endswith(".json"):
        name += ".json"

    path = CONFIG_DIR / name

    if path.exists():
        messagebox.showerror("Error", "File exists")
        return

    try:
        content = currentConfig.read_text()
        path.write_text(content)
        filename_entry.delete(0, tk.END)
        get_all_configs()
    except Exception as e:
        messagebox.showerror("Error", str(e))



root = tk.Tk()
root.title("Config Manager")
root.geometry("900x500")

# Left Side
left_frame = tk.Frame(root)
left_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)

cancel_button = tk.Button(left_frame, text="Cancel", command=root.destroy, font=("Arial", 12), padx=10, pady=5, width=12)
cancel_button.pack(anchor="w", pady=5)

# Bottom Buttons
tk.Button(left_frame, text="Load", command=load_config).pack(side="bottom", fill="x", pady=2)
tk.Button(left_frame, text="Delete", command=delete_config).pack(side="bottom", fill="x", pady=2)
tk.Button(left_frame, text="Save", command=create_config).pack(side="bottom", fill="x", pady=2)
filename_entry = tk.Entry(left_frame)
filename_entry.pack(side="bottom", fill="x", pady=5)


list_container = tk.Frame(left_frame)
list_container.pack(fill="both", expand=True, pady=10)

scrollbar = tk.Scrollbar(list_container, orient="vertical")

canvas = tk.Canvas(
    list_container,
    yscrollcommand=scrollbar.set,
    width=200,
    highlightthickness=0
)
canvas.pack(side="left", fill="both", expand=True)

scrollbar.config(command=canvas.yview)

# config_frame in canvas
config_frame = tk.Frame(canvas)
canvas_window = canvas.create_window((0, 0), window=config_frame, anchor="nw")

def on_canvas_configure(event):
    canvas.itemconfig(canvas_window, width=event.width)

canvas.bind("<Configure>", on_canvas_configure)



# Right Side
right_frame = tk.Frame(root)
right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)

root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

right_frame.grid_rowconfigure(1, weight=1)
right_frame.grid_columnconfigure(0, weight=1)

preview_title = tk.Label(right_frame, text="Select a config", font=("Arial", 28, "bold"))
preview_title.grid(row=0, column=0, sticky="n", pady=(0, 5))

preview_text = tk.Text(right_frame, wrap="word", font=("Arial", 12), state="normal")
preview_text.grid(row=1, column=0, sticky="nsew", padx=120)

bottom_frame = tk.Frame(right_frame)
bottom_frame.grid(row=2, column=0, pady=10)

tk.Button(bottom_frame, text="Autofill", width=15).pack(side="left", padx=10)
tk.Button(bottom_frame, text="Auto run", width=15, bg="black", fg="white").pack(side="left", padx=10)


get_all_configs()

root.mainloop()