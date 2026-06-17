import tkinter as tk
from tkinter import messagebox

from state import name_data


class FirstNamePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        content = tk.Frame(self, bg="white")
        content.pack(fill="both", expand=True)

        nav = tk.Frame(self, bg="white")
        nav.pack(side="bottom", pady=20)

        tk.Label(content, text="First Name Page", font=("Arial", 24), bg="white").pack(pady=20)

        tk.Label(content, text="Enter first name", bg="white").pack()
        self.first_name_entry = tk.Entry(content)
        self.first_name_entry.pack()

        tk.Button(nav, text="Previous", command=lambda: controller.show_page("Add")).pack(side="left", padx=10)
        tk.Button(nav, text="Next", command=self.next_page).pack(side="left", padx=10)

    def refresh(self):
        self.first_name_entry.delete(0, tk.END)
        self.first_name_entry.insert(0, name_data["first_name"])

    def next_page(self):
        first_name = self.first_name_entry.get().strip()

        if not first_name:
            messagebox.showerror("Input Error", "Enter a first name")
            return

        name_data["first_name"] = first_name
        self.controller.show_page("LastName")
    
    def refresh(self):
        self.first_name_entry.delete(0, tk.END)
        self.first_name_entry.insert(0, name_data["first_name"])