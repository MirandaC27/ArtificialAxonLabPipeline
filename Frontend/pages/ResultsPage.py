import tkinter as tk

from state import number_data
from state import name_data

try:
    from .api_client import add_numbers, combine_name
except ImportError:
    from api_client import add_numbers, combine_name


class ResultsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        content = tk.Frame(self, bg="white")
        content.pack(fill="both", expand=True)

        nav = tk.Frame(self, bg="white")
        nav.pack(side="bottom", pady=20)

        tk.Label(content, text="Results Page", font=("Arial", 24), bg="white").pack(pady=20)

        self.result_label = tk.Label(content, text="Choose a result", bg="white", font=("Arial", 14))
        self.result_label.pack(pady=20)

        tk.Button(content, text="Get Sum", command=self.get_sum).pack(pady=5)
        tk.Button(content, text="Get Full Name", command=self.get_full_name).pack(pady=5)

        tk.Button(nav, text="Previous", command=lambda: controller.show_page("LastName")).pack(side="left", padx=10)
        tk.Button(nav, text="Home", command=lambda: controller.show_page("Home")).pack(side="left", padx=10)

    def get_sum(self):
        try:
            a = int(number_data["a"])
            b = int(number_data["b"])

            result = add_numbers(a, b)
            self.result_label.config(text=f"Sum: {result['result']}")

        except Exception as e:
            self.result_label.config(text=f"Error: {e}")

    def get_full_name(self):
        try:
            result = combine_name(
                name_data["first_name"],
                name_data["last_name"]
            )

            full_name = result.get("full_name") or result.get("result")

            if full_name is None:
                raise KeyError(f"full_name missing. API returned: {result}")

            self.result_label.config(text=f"Full Name: {full_name}")

        except Exception as e:
            self.result_label.config(text=f"Error: {e}")