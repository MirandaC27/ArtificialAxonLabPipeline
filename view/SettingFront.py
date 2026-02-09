import tkinter as tk

#some tkinter notes
#pady or padx: adding vertical or horizontal spacing
#.pack: boxes
#.pack_forget: makes things disappear without deleting them.
#screens must be labeled. Maybe consider labeling screens

#transitions are functions

MICROSCOPES = ['Keyence', 'Olympus']
IMAGE_TYPES = ['2D', '3D']

def go_to_output_screen():
    data_type = image_data_type.get()
    microscope = microscope_type.get()

    settings = f"Data Type: {data_type}\nMicroscope: {microscope}"  

    output_label.config(text=settings)  
    input_screen.pack_forget() 

    output_screen.pack(fill="both", expand=True)

def show_radio_button_choice(choice):
    print(f"Selected value: {choice}")

def outputting():
    print(image_data_type.get(), microscope_type.get())
    go_to_output_screen()

def go_back():
    image_data_type.delete(0, tk.END)
    microscope_type.delete(0, tk.END)

    output_screen.pack_forget()      
    input_screen.pack(fill="both", expand=True)  


window = tk.Tk()
window.title("Settings")
window.geometry("500x300")


# input screen
input_screen = tk.Frame(window)

image_var = tk.StringVar()
scope_var = tk.StringVar()
"""
image_data_label = tk.Label(input_screen, text="image data type: 2D or 3D?")
image_data_label.grid(row=0, column=0, padx=10, pady=10, sticky='E')

image_data_type = tk.Entry(input_screen)
image_data_type.grid(row=0, column=1, padx=10, pady=10, sticky='W')


microscope_label = tk.Label(input_screen, text="microscope:")
microscope_label.grid(row=1, column=0, padx=10, pady=10, sticky='E')

microscope_type = tk.Entry(input_screen)
microscope_type.grid(row=1, column=1, padx=10, pady=10, sticky='W')
"""

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

tk.Label(input_screen, text="Select Microscope").grid(row=2, column=0, pady=10)

submit_button = tk.Button(input_screen, text="Submit", command=outputting)
submit_button.grid(row=6, column=0, columnspan=2, pady=10)


# output screen
output_screen = tk.Frame(window)

output_label = tk.Label(output_screen, text="", font=("Arial", 16))

back_button = tk.Button(output_screen, text="Back", command=go_back)
back_button.grid(row=6, column=1, columnspan=2, pady=10)


input_screen.pack(fill="both", expand=True)


window.mainloop()
