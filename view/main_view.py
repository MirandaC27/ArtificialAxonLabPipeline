#main_view.py
import tkinter as tk
from UploadPageStep1 import UploadPageStep1
from SettingFront import SettingsPage
from pipeline_front import ImageProcessingSettings
from HomePage import HomePage
from Config import ConfigPage
from SessionEnd import SessionEnd
from masking_front import MaskingSettingsPage
from history import HistoryPage
from results import ResultsPage


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pipeline")
        self.geometry("700x500")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.pages = {}

        for PageClass, name in [
            (HomePage, "Home"),
            (ConfigPage, "Config"),
            (UploadPageStep1, "Upload"),
            (SettingsPage, "Settings"),
            (ImageProcessingSettings, "Image Processing Stuff"),
            (SessionEnd, "SessionEnd"),
            (MaskingSettingsPage, "Masking Settings"),
            (HistoryPage, "History"),
            (ResultsPage, "Results")
        ]:
            page = PageClass(container, self)
            self.pages[name] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.show_page("Home")

    def get_page(self, name):
        return self.pages.get(name)
    
    def show_page(self, name):
        if name == "Masking Settings":
            self.geometry("520x700")
        else:
            self.geometry("700x500")

        page = self.pages[name]
        if hasattr(page, "refresh_sessions"):
            page.refresh_sessions()
        page.tkraise()

if __name__ == "__main__":
    app = App()
    app.mainloop()
