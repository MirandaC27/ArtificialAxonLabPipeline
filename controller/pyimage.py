import imagej
import os

# Get the absolute path to the local Fiji folder
fiji_path = os.path.abspath("fiji-latest-win64-jdk/Fiji")

# Initialize PyImageJ with the local Fiji
ij = imagej.init(fiji_path, mode='gui')

print("Fiji initialized:", ij.getVersion())

# Optional: show the GUI
ij.ui().showUI()