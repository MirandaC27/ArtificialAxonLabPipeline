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
    print(image_var.get(), scope_var.get(), experiment_menu.get(), fov_var.get(), frame_var.get())
    go_to_output_screen()

def go_back():
    #image_data_type.delete(0, tk.END)
    #microscope_type.delete(0, tk.END)

    output_screen.pack_forget()      
    input_screen.pack(fill="both", expand=True)  


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


tk.Label(input_screen, text="Select Image Type").grid(row=1, column=0, pady=10)
for i, img_type in enumerate(IMAGE_TYPES):
    tk.Radiobutton(
        input_screen,
        text=img_type,
        variable=image_var,
        value=img_type
    ).grid(row=1, column=i, padx=10)

tk.Label(input_screen, text="Select Microscope").grid(row=2, column=0, pady=10)
for i, scope in enumerate(MICROSCOPES):
    tk.Radiobutton(
        input_screen,
        text=scope,
        variable=scope_var,
        value=scope
    ).grid(row=2, column=i, padx=10)

tk.Label(input_screen, text="Select experiment").grid(row=3, column=0, pady=10)
experiment_menu = ttk.Combobox(input_screen, values=EXPERIMENTS, textvariable = experiment_var)
experiment_menu.set("experiment not selected.")
experiment_menu.grid(row=3, column=1, pady=10)

fov_label= tk.Label(input_screen, text="fields of view")
fov_label.grid(row=4, column=0, padx=10, pady=10, sticky='E')

fields_of_view = tk.Entry(input_screen,textvariable=fov_var)
fields_of_view.grid(row=4, column=1, padx=10, pady=10, sticky='W')

frame_label= tk.Label(input_screen, text="number of frames")
frame_label.grid(row=5, column=0, padx=10, pady=10, sticky='E')

frames = tk.Entry(input_screen,textvariable=frame_var)
frames.grid(row=5, column=1, padx=10, pady=10, sticky='W')


submit_button = tk.Button(input_screen, text="Submit", command=outputting)
submit_button.grid(row=7, column=0, columnspan=2, pady=10)


# output screen
output_screen = tk.Frame(window)

output_label = tk.Label(output_screen, text="", font=("Arial", 16))

back_button = tk.Button(output_screen, text="Back", command=go_back)
back_button.grid(row=6, column=1, columnspan=2, pady=10)


input_screen.pack(fill="both", expand=True)


window.mainloop()
