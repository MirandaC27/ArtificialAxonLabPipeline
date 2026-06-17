import tkinter as tk
from tkinter import messagebox

from state import number_data


class AddPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        content = tk.Frame(self, bg="white")
        content.pack(fill="both", expand=True)

        nav = tk.Frame(self, bg="white")
        nav.pack(side="bottom", pady=20)

        tk.Label(content, text="Adder Page", font=("Arial", 24), bg="white").pack(pady=20)

        tk.Label(content, text="A", bg="white").pack()
        self.entry_a = tk.Entry(content)
        self.entry_a.pack()

        tk.Label(content, text="B", bg="white").pack()
        self.entry_b = tk.Entry(content)
        self.entry_b.pack()

        tk.Button(nav, text="Previous", command=lambda: controller.show_page("Home")).pack(side="left", padx=10)
        tk.Button(nav, text="Next", command=self.next_page).pack(side="left", padx=10)

    def refresh(self):
        self.entry_a.delete(0, tk.END)
        self.entry_a.insert(0, number_data["a"])

        self.entry_b.delete(0, tk.END)
        self.entry_b.insert(0, number_data["b"])

    def next_page(self):
        try:
            int(self.entry_a.get())
            int(self.entry_b.get())

            number_data["a"] = self.entry_a.get().strip()
            number_data["b"] = self.entry_b.get().strip()

            self.controller.show_page("FirstName")

        except ValueError:
            messagebox.showerror("Input Error", "Enter valid integers")

    def refresh(self):
        self.entry_a.delete(0, tk.END)
        self.entry_a.insert(0, str(number_data["a"]))

        self.entry_b.delete(0, tk.END)
        self.entry_b.insert(0, str(number_data["b"]))