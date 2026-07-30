import tkinter as tk

from state import reset_history_state


class SessionEnd(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        self.left_frame = tk.Frame(self, bg="white")
        self.left_frame.place(relx=0.0, rely=0.0, relwidth=0.5, relheight=1.0)

        tk.Label(
            self.left_frame,
            text="Session Ended",
            font=("Arial", 35),
            bg="white",
            fg="#333333",
        ).place(relx=0.5, rely=0.5, anchor="center")

        self.right_frame = tk.Frame(self, bg="white")
        self.right_frame.place(relx=0.5, rely=0.0, relwidth=0.5, relheight=1.0)

        tk.Label(
            self.right_frame,
            text="What would you like to do?",
            font=("Arial", 18),
            bg="white",
            fg="#333333",
        ).pack(pady=(80, 20))

        button_options = {
            "font": ("Arial", 12),
            "bg": "black",
            "fg": "white",
            "activebackground": "#333333",
            "activeforeground": "white",
            "width": 20,
            "height": 2,
            "bd": 0,
            "cursor": "hand2",
        }

        tk.Button(
            self.right_frame,
            text="Create Graphs",
            command=lambda: self.controller.show_page("Home"),
            **button_options,
        ).pack(pady=10)

        tk.Button(
            self.right_frame,
            text="Rerun Configuration",
            command=self.rerun_configuration,
            **button_options,
        ).pack(pady=10)
        tk.Button(
            self.right_frame,
            text="Return to Home Page",
            command=lambda: self.controller.show_page("Home"),
            **button_options,
        ).pack(pady=10)

        tk.Button(
            self.right_frame,
            text="Quit",
            command=self.controller.quit,
            **button_options,
        ).pack(pady=10)

    def rerun_configuration(self):
        reset_history_state()
        self.controller.show_page("Upload")