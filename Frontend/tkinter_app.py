import tkinter as tk
from tkinter import messagebox, ttk

try:
    from .api_client import add_name, add_numbers
except ImportError:
    from api_client import add_name, add_numbers

def calculate():
    try:
        a = int(entry_a.get())
        b = int(entry_b.get())

        result = add_numbers(a, b)
        result_label.config(text=f"Result: {result.get('result')}")

    except ValueError:
        messagebox.showerror("Input Error", "Enter valid integers")
    except Exception as e:
        result_label.config(text=f"Error: {e}")

def submit_name():
    first_name = first_name_entry.get().strip()
    last_name = last_name_entry.get().strip()

    if not first_name or not last_name:
        messagebox.showerror("Input Error", "Enter both first and last name")
        return

    try:
        result = add_name(first_name, last_name)
        name_result_label.config(text=f"Result: {result.get('result')}")
    except Exception as e:
        name_result_label.config(text=f"Error: {e}")

def main():
    global entry_a, entry_b, first_name_entry, last_name_entry
    global result_label, name_result_label

    root = tk.Tk()
    root.title("Adder App")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    add_tab = ttk.Frame(notebook, padding=12)
    name_tab = ttk.Frame(notebook, padding=12)

    notebook.add(add_tab, text="add")
    notebook.add(name_tab, text="name")

    tk.Label(add_tab, text="A").pack()
    entry_a = tk.Entry(add_tab)
    entry_a.pack()

    tk.Label(add_tab, text="B").pack()
    entry_b = tk.Entry(add_tab)
    entry_b.pack()

    tk.Button(add_tab, text="Add", command=calculate).pack(pady=(8, 0))

    result_label = tk.Label(add_tab, text="Result:")
    result_label.pack(pady=(8, 0))

    tk.Label(name_tab, text="First Name").pack()
    first_name_entry = tk.Entry(name_tab)
    first_name_entry.pack()

    tk.Label(name_tab, text="Last Name").pack()
    last_name_entry = tk.Entry(name_tab)
    last_name_entry.pack()

    tk.Button(name_tab, text="Submit", command=submit_name).pack(pady=(8, 0))

    name_result_label = tk.Label(name_tab, text="Result:")
    name_result_label.pack(pady=(8, 0))

    root.mainloop()

if __name__ == "__main__":
    main()
