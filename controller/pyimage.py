import imagej
from pathlib import Path

ij = imagej.init('sc.fiji:fiji', headless=False)  

data_folder = Path(r"C:\Users\jonat\OneDrive - Loyola University Maryland\Desktop\VS Code\AxonLabs\Sample Data\EXP009\2026-02-23_EXP009_ORDERED\B2\B02_0001\OIR")

tif_files = list(data_folder.glob("*.tif"))

for image in tif_files:
    print("Opening:", image.name)
    Imagedata = ij.io().open(str(image))  
    ij.ui().show(Imagedata)             

input("Press Enter to exit")
ij.dispose()  