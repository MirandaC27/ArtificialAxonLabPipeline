#main_view.py
import tkinter as tk
import sys
from pathlib import Path

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[3]
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

from ArtificialAxonLabPipeline.Frontend.view.pages.UploadPageStep1 import UploadPageStep1
from ArtificialAxonLabPipeline.Frontend.view.pages.SettingFront import SettingsPage
from ArtificialAxonLabPipeline.Frontend.view.pages.pipeline_front import ImageProcessingSettings
from ArtificialAxonLabPipeline.Frontend.view.pages.HomePage import HomePage
from ArtificialAxonLabPipeline.Frontend.view.pages.Config import ConfigPage
from ArtificialAxonLabPipeline.Frontend.view.pages.SessionEnd import SessionEnd
from ArtificialAxonLabPipeline.Frontend.view.pages.masking_front import MaskingSettingsPage
from ArtificialAxonLabPipeline.Frontend.view.pages.history import HistoryPage


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
            (HistoryPage, "History")
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
