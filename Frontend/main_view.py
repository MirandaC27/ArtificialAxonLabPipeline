import tkinter as tk

from pages.HomePage import HomePage
from pages.UploadPage import UploadPage
#from pages.SettingsPage import SettingsPage
#from pages.MaskingPage import MaskingPage
#from pages.EndPage import EndPage

from pages.HistoryPage import HistoryPage
from pages.ConfigPage import ConfigPage


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Adder App")
        self.geometry("700x500")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.pages = {}

        for PageClass, name in [
            (HomePage, "Home"),
            (UploadPage, "Upload"),
            #(SettingsPage, "Settings"),
            #(MaskingPage, "Masking"),
            #(EndPage, "End"),

            (HistoryPage, "History"),
            (ConfigPage, "Config")

        ]:
            page = PageClass(container, self)
            self.pages[name] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.show_page("Home")

    def show_page(self, name):
        page = self.pages[name]

        if hasattr(page, "refresh"):
            page.refresh()

        page.tkraise()


if __name__ == "__main__":
    app = App()
    app.mainloop()