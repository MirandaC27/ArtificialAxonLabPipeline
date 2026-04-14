import tkinter as tk
from pathlib import Path


class HistoryPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        self.CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "history"
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        self.selected_config = None
        self.selected_label = None
        self.config_order = []

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        #   LEFT SIDE   #
        self.left_frame = tk.Frame(self, bg="white")
        self.left_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)

        tk.Button(
            self.left_frame,
            text="Cancel",
            command=lambda: controller.show_page("Home"),
            font=("Arial", 12),
            width=12
        ).pack(anchor="w", pady=5)

        self.list_container = tk.Frame(self.left_frame, bg="white")
        self.list_container.pack(fill="both", expand=True, pady=10)

        self.scrollbar = tk.Scrollbar(self.list_container, orient="vertical")
        self.canvas = tk.Canvas(
            self.list_container,
            yscrollcommand=self.scrollbar.set,
            width=220,
            bg="white",
            highlightthickness=0
        )

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.canvas.yview)

        self.config_list_frame = tk.Frame(self.canvas, bg="white")
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.config_list_frame, anchor="nw"
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        self.config_list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Right side of frame - preview
        self.right_frame = tk.Frame(self, bg="white")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)

        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.preview_title = tk.Label(
            self.right_frame,
            text="Select a session",
            font=("Arial", 28, "bold"),
            bg="white"
        )
        self.preview_title.grid(row=0, column=0, pady=(20, 10))

        self.preview_content_frame = tk.Frame(self.right_frame, bg="white")
        self.preview_content_frame.grid(row=1, column=0, sticky="nsew")

        self.preview_content_frame.grid_rowconfigure(0, weight=1)
        self.preview_content_frame.grid_columnconfigure(0, weight=1)

        # Load sessions
        self.get_all_configs()
        

    # Get folders + txt files
    def get_all_configs(self):
        self.config_order = [
            p for p in self.CONFIG_DIR.iterdir()
            if p.is_dir() or p.suffix.lower() == ".txt"
        ]

        self.config_order.sort(key=lambda x: (x.is_file(), x.name.lower()))

        self.render_config_list()

    # \List of sessions 
    def render_config_list(self):
        for widget in self.config_list_frame.winfo_children():
            widget.destroy()

        self.selected_label = None

        for entry in self.config_order:

            display_name = entry.name if entry.is_dir() else entry.stem

            item = tk.Label(
                self.config_list_frame,
                text=f"→ {display_name}",
                anchor="w",
                padx=10,
                pady=8,
                bg="white",
                cursor="hand2",
                font=("Arial", 11)
            )
            item.pack(fill="x")

            item.bind("<Button-1>", lambda e, p=entry: self.select_config(e, p))

            tk.Frame(self.config_list_frame, height=1, bg="#ccc").pack(
                fill="x", padx=5, pady=2
            )

    # Select item from list
    def select_config(self, event, entry_path):
        self.selected_config = entry_path

        if self.selected_label and self.selected_label.winfo_exists():
            self.selected_label.config(bg="white")

        self.selected_label = event.widget
        self.selected_label.config(bg="#e0e0e0")

        self.show_session_preview(entry_path)

    # Preview of selected item
    def show_session_preview(self, entry_path):
        for widget in self.preview_content_frame.winfo_children():
            widget.destroy()

        session_txt = entry_path / "sessionData.txt" if entry_path.is_dir() else entry_path

        text = self.read_session_txt(session_txt)

        title = entry_path.name if entry_path.is_dir() else entry_path.stem
        self.preview_title.config(text=title)

        if text is None:
            tk.Label(
                self.preview_content_frame,
                text="No session data found.",
                font=("Arial", 13),
                bg="white"
            ).grid(row=0, column=0, pady=10)
            return

        text_box = tk.Text(
            self.preview_content_frame,
            font=("Courier New", 12),
            bg="white",
            wrap="word",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#d9d9d9",
            padx=12,
            pady=12
        )
        text_box.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        text_box.insert("1.0", text)
        text_box.config(state="disabled")

    # Read text content    
    def read_session_txt(self, txt_path):
        if not txt_path.exists():
            return None

        try:
            return txt_path.read_text(encoding="utf-8").strip()
        except Exception:
            return None