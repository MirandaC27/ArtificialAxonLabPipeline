import tkinter as tk
from tkinter import messagebox

from api_client import save_session
from state import name_data
from state import number_data


class LastNamePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        content = tk.Frame(self, bg="white")
        content.pack(fill="both", expand=True)

        nav = tk.Frame(self, bg="white")
        nav.pack(side="bottom", pady=20)

        tk.Label(content, text="Last Name Page", font=("Arial", 24), bg="white").pack(pady=20)

        self.first_name_label = tk.Label(content, text="", bg="white")
        self.first_name_label.pack()

        tk.Label(content, text="Enter last name", bg="white").pack()
        self.last_name_entry = tk.Entry(content)
        self.last_name_entry.pack()

        tk.Button(nav, text="Previous", command=lambda: controller.show_page("FirstName")).pack(side="left", padx=10)
        tk.Button(nav, text="Next", command=self.next_page).pack(side="left", padx=10)

    def refresh(self):
        self.first_name_label.config(text=f"First Name: {name_data['first_name']}")

        self.last_name_entry.delete(0, tk.END)
        self.last_name_entry.insert(0, name_data["last_name"])

    def next_page(self):
        last_name = self.last_name_entry.get().strip()

        if not last_name:
            messagebox.showerror("Input Error", "Enter a last name")
            return

        name_data["last_name"] = last_name
        
        try:
            save_session(
                number_data["a"],
                number_data["b"],
                name_data["first_name"],
                name_data["last_name"]
            )

            self.controller.show_page("Results")

        except Exception as e:
            messagebox.showerror(
                "Save Error",
                f"Failed to save session:\n{e}"
            )
    
    def refresh(self):
        self.last_name_entry.delete(0, tk.END)
        self.last_name_entry.insert(0, name_data["last_name"])