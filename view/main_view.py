import tkinter as tk

from UploadPageStep1 import UploadPageStep1
from SettingFront import SettingsPage
from pipeline_front import ImageProcessingSettings


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
            (UploadPageStep1, "Upload"),
            (SettingsPage, "Settings"),
            (ImageProcessingSettings, "Image Processing Stuff")
        ]:

            page = PageClass(container, self)
            self.pages[name] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.show_page("Upload")


    def show_page(self, name):
        page = self.pages[name]
        page.tkraise()


if __name__ == "__main__":
    app = App()
    app.mainloop()