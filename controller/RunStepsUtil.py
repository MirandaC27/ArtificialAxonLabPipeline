from pathlib import Path
from datetime import datetime
import subprocess
import json
import platform


def start_time(self):
    
    start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    json_path = Path(__file__).resolve().parent.parent / "data" / "folder_paths.json"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["START_TIME"] = start

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def run_step1(self):

    if platform.system() == "Windows":
        bash_path = r"C:\Program Files\Git\bin\bash.exe"
    else:
        bash_path = "/bin/bash"

    script_path = Path(__file__).resolve().parent.parent / "model" / "rename_organize_keyence.sh"

    subprocess.run([bash_path, str(script_path)], check=True)


def button_run(self):

    print("Channels at run:", self.channels)
    print("Selected folders at run:", self.selected_folders)

    self.save_folders()
    self.start_time()
    self.run_step1()