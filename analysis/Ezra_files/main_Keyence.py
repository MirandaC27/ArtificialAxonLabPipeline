from detectrims_Keyence import detectrims_Keyence
from analysis import analysis
from detectnuclei import detectnuclei
from detectmyelinarea_Keyence import detectmyelinarea_Keyence
import time
import os
import json
from pathlib import Path
import sys

SOURCE_ROOT = Path(__file__).resolve().parents[2]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.append(str(SOURCE_ROOT))

from controller.runtime_paths import data_dir, results_dir

start = time.time()

setnums = [1]
outerthresh = 19500
innerthresh = 19500

dynamic_mode = False  # IF THE NUMBER OF AXONS IS INCORRECT CHANGE THIS TO 'True' TO MAKE MAX DISTANCE BETWEEN PILLARS DYNAMIC
debug_mode = False # IF YOU WANT TO DEBUG, MAKE SURE ONLY ONE SET IS BEING RUN OTHERWISE EACH SET WILL OVERWRITE THE LAST
further_analysis_mode = False # MAKES OUTPUT THAT IS USED BY FOCUSED WRAPPING TO FIND 80% OVER 3 / NUCLEI ONLY COUNTING NUCLEI IN THE MYELIN OBJ
skip = [] # INDEX STARTS WITH 0. THIS IS FOR TESTING SKIPPING LAYER. LAYERS IN THE LIST WILL BE SKIPPED. THE ANALYSIS FUNCTION NEEDS TO BE MANUALLY CHANGED IF SKIPPED LAYERS CAUSE GAPS

for setnum in setnums:

    config_path = data_dir() / "upload_settings.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    ordered_tracks = config.get("OrderedTrack", [])
    if not ordered_tracks:
        raise FileNotFoundError("No OrderedTrack path found in upload_settings.json")

    path = ordered_tracks[0]
    run_results_dir = results_dir()
    debug_path = str(run_results_dir / f"debug{setnum}.csv")
    further_analysis_path = str(run_results_dir / f"further_analysis{setnum}.csv")
    out_path = str(run_results_dir / "2D-Wrapping-Analysis_EM-algo.csv")

    # Extract the directory part of the path
    out_dir = os.path.dirname(out_path)

    # Create the directory if it doesn't exist
    os.makedirs(out_dir, exist_ok=True)

    print("Loading Overlap")
    # Returns overlaps_dict: {well,fov}:[[inner[x][y][z][%],outer[x][y][z][%]]     myelin_dict: [(well,fov)] = [myelin,myelin50,myelin80]
    overlaps_dict, myelin_dict = detectrims_Keyence(path,debug_path,  # Paths
                                            outerthresh,innerthresh,  # Perams
                                            dynamic_mode,debug_mode,skip) # Modes

    print("Detecting Nuclei")
    # Detect nuclei {well,fov}:[nuclei]
    nuclei_dict = detectnuclei(path)

    print("Detecting Myelin Area")
    # Detect total {well,fov}:[area]
    areas_dict = detectmyelinarea_Keyence(path,innerthresh,
                                  debug_mode)

    print("Analyzing")
    # Analysis
    analysis(path,out_path,further_analysis_path,   # Paths
             overlaps_dict,nuclei_dict,areas_dict,myelin_dict,  # Dicts
             skip,further_analysis_mode) # Modes

end = time.time() - start
print(end)
