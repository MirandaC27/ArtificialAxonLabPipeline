import tkinter as tk

#some tkinter notes
#pady or padx: adding vertical or horizontal spacing
#.pack: boxes
#.pack_forget: makes things disappear without deleting them.
#screens must be labeled. Maybe consider labeling screens

window = tk.Tk()
window.title("Settings")
window.geometry("300x150")


# input screen
input_screen = tk.Frame(window)

label = tk.Label(input_screen, text="Pipeline")
label.pack(pady=5)

entry = tk.Entry(input_screen)
entry.pack(pady=5)


def console_print():
    print(entry.get())

#transitions are functions
def go_to_output_screen():
    word = entry.get()          
    output_label.config(text=word)  
    input_screen.pack_forget()       
    output_screen.pack()

def outputting():
    console_print()
    go_to_output_screen()


button = tk.Button(input_screen, text="Submit", command=outputting)
button.pack(pady=10)

# output screen
output_screen = tk.Frame(window)

output_label = tk.Label(output_screen, text="", font=("Arial", 16))
output_label.pack(pady=20)

#transitions are functions
def go_back():
    entry.delete(0, tk.END)     
    output_screen.pack_forget()      
    input_screen.pack()              

back_button = tk.Button(output_screen, text="Back", command=go_back)
back_button.pack()


input_screen.pack()


window.mainloop()
