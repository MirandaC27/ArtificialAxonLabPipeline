import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from controller.AutoFillUtil import AutoFillUtil

class SessionEnd(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        self.autofill = AutoFillUtil()

        #Left Side: Welcome Text 
        self.left_frame = tk.Frame(self, bg="white")
        self.left_frame.place(relx=0.0, rely=0.0, relwidth=0.5, relheight=1.0)

        self.welcome_label = tk.Label(
            self.left_frame, 
            text="Session Ended", 
            font=("Arial", 35), 
            bg="white", 
            fg="#333333"
        )
        self.welcome_label.place(relx=0.5, rely=0.5, anchor="center")

        #Right Side: Question and Buttons
        self.right_frame = tk.Frame(self, bg="white")
        self.right_frame.place(relx=0.5, rely=0.0, relwidth=0.5, relheight=1.0)

        self.question_label = tk.Label(
            self.right_frame, 
            text="What would you like to do?", 
            font=("Arial", 18), 
            bg="white", 
            fg="#333333"
        )
        self.question_label.pack(pady=(80, 20))

        button_options = {
            "font": ("Arial", 12),
            "bg": "black",
            "fg": "white",
            "activebackground": "#333333",
            "activeforeground": "white",
            "width": 20,
            "height": 2,
            "bd": 0,
            "cursor": "hand2"
        }

        self.btn_new = tk.Button(self.right_frame, text="Create Graphs", command=lambda: controller.show_page("Home"), **button_options)
        self.btn_new.pack(pady=10)

        self.btn_old = tk.Button(self.right_frame, text="Rerun Configuration", command=self.rerun_configuration, **button_options)
        self.btn_old.pack(pady=10)

        self.btn_history = tk.Button(self.right_frame, text="Return to Home Page", command=lambda: controller.show_page("Home"), **button_options)
        self.btn_history.pack(pady=10)

        self.btn_quit = tk.Button(self.right_frame, text="quit", command=self.controller.quit, **button_options)
        self.btn_quit.pack(pady=10)

    def rerun_configuration(self):
        config_path = Path(__file__).resolve().parent.parent / "data" / "upload_settings.json"
        if not config_path.exists():
            messagebox.showerror("Error", "No saved configuration found to rerun")
            return

        self.autofill.set_selected_config(config_path)
        self.autofill.autofill_and_navigate(self.controller)
