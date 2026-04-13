import tkinter as tk
from UploadPageStep1 import UploadPageStep1
from pipeline_front import ImageProcessingSettings
from HomePage import HomePage
from Config import ConfigPage
from SessionEnd import SessionEnd
from masking_front import MaskingSettingsPage


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
            (ConfigPage, "Config"),
            (HomePage, "Home"),
            (UploadPageStep1, "Upload"),
            (ImageProcessingSettings, "Image Processing Stuff"),
            (MaskingSettingsPage, "Masking Settings"),
            (SessionEnd, "SessionEnd")
        ]:
            page = PageClass(container, self)
            self.pages[name] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.show_page("Home")

    def get_page(self, name):
        return self.pages.get(name)
    
    def show_page(self, name):
        if name == "Masking Settings":
            self.geometry("700x600")
        else:
            self.geometry("700x500")

        page = self.pages[name]
        page.tkraise()

if __name__ == "__main__":
    app = App()
    app.mainloop()