import tkinter as tk
from tkinter import messagebox

try:
    from .api_client import add_numbers
except ImportError:
    from api_client import add_numbers

def calculate():
    try:
        a = int(entry_a.get())
        b = int(entry_b.get())

        result = add_numbers(a, b)
        result_label.config(text=f"Result: {result['result']}")

    except ValueError:
        messagebox.showerror("Input Error", "Enter valid integers")
    except Exception as e:
        result_label.config(text=f"Error: {e}")

def main():
    global entry_a, entry_b, result_label

    root = tk.Tk()
    root.title("Adder App")

    tk.Label(root, text="A").pack()
    entry_a = tk.Entry(root)
    entry_a.pack()

    tk.Label(root, text="B").pack()
    entry_b = tk.Entry(root)
    entry_b.pack()

    tk.Button(root, text="Add", command=calculate).pack()

    result_label = tk.Label(root, text="Result:")
    result_label.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
