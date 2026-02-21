from datetime import datetime
from pathlib import Path

def CleanedFileName(datadir):
    EXP = Path(datadir).name
    date = datetime.now().strftime("%Y-%m-%d")
    cleaned_name = f"{date}_{EXP}_CLEANED"
    return cleaned_name

def OrderedFileName(datadir):
    EXP = Path(datadir).name
    date = datetime.now().strftime("%Y-%m-%d")
    cleaned_name = f"{date}_{EXP}_ORDERED"
    return cleaned_name
