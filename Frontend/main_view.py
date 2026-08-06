import tkinter as tk

from pages.HomePage import HomePage
from pages.UploadPage import UploadPage
from pages.SettingsPage import SettingsPage
from pages.MaskingPage import MaskingPage
#from pages.EndPage import EndPage

from pages.HistoryPage import HistoryPage
from pages.ConfigPage import ConfigPage

from pages.TestSave import TestSave
from pages.SessionEnd import SessionEnd
from pages.ResultsPage import ResultsPage

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Adder App")
        self.page_sizes = {
            "Home": (900, 600),
            "Upload": (900, 700),
            "Settings": (700, 430),
            "Masking": (780, 740),
            "TestSave": (780, 650),
            "Results": (1000, 700),
            "SessionEnd": (900, 600),
            "History": (1000, 700),
            "Config": (1150, 700),
        }
        self.minsize(650, 400)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.pages = {}
        self.current_page = None
        self.results_return_page = "Home"

        for PageClass, name in [
            (HomePage, "Home"),
            (UploadPage, "Upload"),
            (SettingsPage, "Settings"),
            (MaskingPage, "Masking"),
            (TestSave, "TestSave"),
            (ResultsPage, "Results"),
            (SessionEnd, "SessionEnd"),
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
        if name == "Results" and self.current_page != "Results":
            self.results_return_page = self.current_page or "Home"

        width, height = self.page_sizes.get(name, (900, 650))
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        page = self.pages[name]

        if hasattr(page, "refresh"):
            page.refresh()

        page.tkraise()
        self.current_page = name

    def return_from_results(self):
        return_page = self.results_return_page
        if return_page not in self.pages or return_page == "Results":
            return_page = "Home"
        self.show_page(return_page)


if __name__ == "__main__":
    app = App()
    app.mainloop()
