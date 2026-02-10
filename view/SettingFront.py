import tkinter as tk
from tkinter import ttk


#some tkinter notes
#pady or padx: adding vertical or horizontal spacing
#.pack: boxes
#.pack_forget: makes things disappear without deleting them.
#screens must be labeled. Maybe consider labeling screens

#transitions are functions

MICROSCOPES = ['Keyence', 'Olympus']
IMAGE_TYPES = ['2D', '3D']
EXPERIMENTS = ['DAPI','GFP-mylein','CY5-myelin','GFP-debris','CY5-debris']

def create_state():
    state = {}

    # tkinter variables
    state["image_var"] = tk.StringVar()
    state["scope_var"] = tk.StringVar()
    state["experiment_var"] = tk.StringVar()
    state["fov_var"] = tk.StringVar()
    state["frame_var"] = tk.StringVar()
    state["ezra_var"] = tk.BooleanVar()

    # widget storage
    state["widgets_3d"] = {}

    return state


ui = {}

def collect_settings():
    return{
        "image": state["image"].get(),
        "scope": state["scope"].get(),
        "experiment": state["experiment"].get(),
        "fovs": state["fovs"].get(),

    }
    
def show_screen(state, name):
    for screen in("input", "output"):
        state[f"{screen}_frame"].grid_remove()

    state[f"{name}_frame"].grid(row=0, column=0, sticky="nsew")

def submit(state):
    data = state["image_var"].get()
    scope = state["scope_var"].get()
    exp = state["experiment_var"].get()
    fovs = state["fov_var"].get()
    frames = state["frame_var"].get()
    ezra = state["ezra_var"].get()

    print(data, scope, exp, fovs, frames, ezra)

    settings = (
        f"Data Type: {data}\n"
        f"Microscope: {scope}\n"
        f"Experiment: {exp}\n"
        f"FOVs: {fovs}\n"
        f"Frames: {frames}\n"
        f"Run Ezra: {ezra}"
    )

    state["output_label"].config(text=settings)
    show_screen(state, "output")

def show_3D_inputs(state):
    if state["image_var"].get() == "3D":
        for w in state["widgets_3d"].values():
            w.grid()
    else:
        for w in state["widgets_3d"].values():
            w.grid_remove()

def create_3d_widgets(state, parent):
    w = {}

    w["frame_label"] = tk.Label(parent, text="Number of frames")
    w["frame_entry"] = tk.Entry(parent, textvariable=state["frame_var"])

    w["dist_label"] = tk.Label(parent, text="Distance between frames")
    w["dist_entry"] = tk.Entry(parent)

    w["ezra_check"] = tk.Checkbutton(
        parent,
        text="Run Ezra's algorithm?",
        variable=state["ezra_var"]
    )

    # place
    w["frame_label"].grid(row=5, column=0, padx=10, pady=5, sticky="e")
    w["frame_entry"].grid(row=5, column=1, padx=10, pady=5, sticky="w")

    w["dist_label"].grid(row=6, column=0, padx=10, pady=5, sticky="e")
    w["dist_entry"].grid(row=6, column=1, padx=10, pady=5, sticky="w")

    w["ezra_check"].grid(row=7, column=1, padx=10, pady=5, sticky="w")

    # hide initially
    for widget in w.values():
        widget.grid_remove()

    state["widgets_3d"] = w

def build_input_screen(root, state):
    frame = tk.Frame(root)
    state["input_frame"] = frame

    tk.Label(frame, text="Select Image Type").grid(row=1, column=0, pady=10)

    for i, img in enumerate(IMAGE_TYPES):
        tk.Radiobutton(
            frame,
            text=img,
            variable=state["image_var"],
            value=img,
            command=lambda: show_3D_inputs(state)
        ).grid(row=1, column=i+1, padx=10)

    tk.Label(frame, text="Select Microscope").grid(row=2, column=0, pady=10)

    for i, scope in enumerate(MICROSCOPES):
        tk.Radiobutton(
            frame,
            text=scope,
            variable=state["scope_var"],
            value=scope
        ).grid(row=2, column=i+1, padx=10)

    tk.Label(frame, text="Experiment").grid(row=3, column=0, pady=10)

    exp_menu = ttk.Combobox(
        frame,
        values=EXPERIMENTS,
        textvariable=state["experiment_var"],
        state="readonly"
    )
    exp_menu.grid(row=3, column=1, pady=10)
    exp_menu.set("Select experiment")

    tk.Label(frame, text="Fields of view").grid(row=4, column=0, padx=10, pady=10, sticky="e")
    tk.Entry(frame, textvariable=state["fov_var"]).grid(row=4, column=1, padx=10, pady=10, sticky="w")

    create_3d_widgets(state, frame)

    tk.Button(
        frame,
        text="Submit",
        command=lambda: submit(state)
    ).grid(row=10, column=0, columnspan=2, pady=20)

def build_output_screen(root, state):
    frame = tk.Frame(root)
    state["output_frame"] = frame

    label = tk.Label(frame, text="", font=("Arial", 16))
    label.grid(row=0, column=0, padx=20, pady=20)
    state["output_label"] = label

    tk.Button(
        frame,
        text="Back",
        command=lambda: show_screen(state, "input")
    ).grid(row=1, column=0, pady=10)

def main():
    root = tk.Tk()
    root.title("Research Pipeline Settings")
    root.geometry("520x420")

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    state = create_state()

    build_input_screen(root, state)
    build_output_screen(root, state)

    show_screen(state, "input")

    root.mainloop()

main()



"""
def go_to_output_screen():
    data_type = image_var.get()
    microscope = scope_var.get()
    experiment = experiment_menu.get()
    fovs = fov_var.get()
    frames = frame_var.get()

    settings = f"Data Type: {data_type}\nMicroscope: {microscope}\nexperiment: {experiment}\nnumber of FOVs: {fovs}"
    

    output_label.config(text=settings)  
    input_screen.pack_forget() 

    output_screen.pack(fill="both", expand=True)

def show_radio_button_choice(choice):
    print(f"image type and microscope choice: {choice}")
    
def show_experiment_dropdown(r, c):
    label = Label(tk, text=" ")
    label.grid(row = r, column = c, pady = 10)


def outputting():
    print(image_var.get(), scope_var.get(), experiment_menu.get(), fov_var.get(), frame_var.get(), ezra_var.get())
    go_to_output_screen()

def go_back():
    #image_data_type.delete(0, tk.END)
    #microscope_type.delete(0, tk.END)

    output_screen.pack_forget()      
    input_screen.pack(fill="both", expand=True)

def inputs_3D():
    frame_label= tk.Label(input_screen, text="number of frames")
    frame_label.grid(row=5, column=0, padx=10, pady=10, sticky='E')

    frames = tk.Entry(input_screen,textvariable=frame_var)
    frames.grid(row=5, column=1, padx=10, pady=10, sticky='W')

    frame_label= tk.Label(input_screen, text="distance between frames")
    frame_label.grid(row=5, column=0, padx=10, pady=10, sticky='E')

    frames = tk.Entry(input_screen,textvariable=frame_var)
    frames.grid(row=5, column=1, padx=10, pady=10, sticky='W')

    ezra_algo = tk.Checkbutton(input_screen,text="Run Ezra's algorithm?", variable=ezra_var)
    ezra_algo.grid(row=5, column=1, padx=10, pady=10, sticky='W')

window = tk.Tk()
window.title("Settings")
window.geometry("500x300")


# input screen
input_screen = tk.Frame(window)

image_var = tk.StringVar()
scope_var = tk.StringVar()
experiment_var = tk.StringVar()
fov_var = tk.StringVar()
frame_var = tk.StringVar()
ezra_var = tk.BooleanVar()
"""
"""
tk.Label(input_screen, text="Select Image Type").grid(row=1, column=0, pady=10)
for i, img_type in enumerate(IMAGE_TYPES):
    tk.Radiobutton(
        input_screen,
        text=img_type,
        variable=image_var,
        value=img_type
    ).grid(row=1, column=i+1, padx=10)

tk.Label(input_screen, text="Select Microscope").grid(row=2, column=0, pady=10)
for i, scope in enumerate(MICROSCOPES):
    tk.Radiobutton(
        input_screen,
        text=scope,
        variable=scope_var,
        value=scope
    ).grid(row=2, column=i+1, padx=10)

tk.Label(input_screen, text="Select experiment").grid(row=3, column=0, pady=10)
experiment_menu = ttk.Combobox(input_screen, values=EXPERIMENTS, textvariable = experiment_var)
experiment_menu.set("experiment not selected.")
experiment_menu.grid(row=3, column=1, pady=10)

fov_label = tk.Label(input_screen, text="fields of view")
fov_label.grid(row=4, column=0, padx=10, pady=10, sticky='E')

fields_of_view = tk.Entry(input_screen,textvariable=fov_var)
fields_of_view.grid(row=4, column=1, padx=10, pady=10, sticky='W')

#ezra_label = tk.Label(input_screen, text="fields of view").grid(row=3, column=0, pady=10)



submit_button = tk.Button(input_screen, text="Submit", command=outputting)
submit_button.grid(row=7, column=0, columnspan=2, pady=10)


# output screen
output_screen = tk.Frame(window)

output_label = tk.Label(output_screen, text="", font=("Arial", 16))

back_button = tk.Button(output_screen, text="Back", command=go_back)
back_button.grid(row=6, column=1, columnspan=2, pady=10)


input_screen.pack(fill="both", expand=True)


window.mainloop()
"""
