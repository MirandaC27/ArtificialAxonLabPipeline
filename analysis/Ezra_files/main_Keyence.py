#main_keyence.py
from detectrims_Keyence import detectrims_Keyence
from analysis_Keyence import analysis
from detectnuclei import detectnuclei
from detectmyelinarea_Keyence import detectmyelinarea_Keyence
import time
import os

start = time.time()

setnums = [1]
outerthresh = 19500
innerthresh = 19500

dynamic_mode = False  # IF THE NUMBER OF AXONS IS INCORRECT CHANGE THIS TO 'True' TO MAKE MAX DISTANCE BETWEEN PILLARS DYNAMIC
debug_mode = False # IF YOU WANT TO DEBUG, MAKE SURE ONLY ONE SET IS BEING RUN OTHERWISE EACH SET WILL OVERWRITE THE LAST
further_analysis_mode = False # MAKES OUTPUT THAT IS USED BY FOCUSED WRAPPING TO FIND 80% OVER 3 / NUCLEI ONLY COUNTING NUCLEI IN THE MYELIN OBJ
skip = [] # INDEX STARTS WITH 0. THIS IS FOR TESTING SKIPPING LAYER. LAYERS IN THE LIST WILL BE SKIPPED. THE ANALYSIS FUNCTION NEEDS TO BE MANUALLY CHANGED IF SKIPPED LAYERS CAUSE GAPS

for setnum in setnums:

    path = f"/Users/chloemiranda/capstone/CLEANED/ORDERED"
    debug_path = f"E:/EXP009/2025-08-13_2xSecAb/debug{setnum}.csv"
    further_analysis_path = f"E:/EXP009/2025-08-13_2xSecAb/further_analysis{setnum}.csv"
    out_path = f"/Users/chloemiranda/capstone/CLEANED/ORDERED/2D-Wrapping-Analysis_EM-algo.csv"

    # Extract the directory part of the path
    out_dir = os.path.dirname(out_path)

    # Create the directory if it doesn't exist
    os.makedirs(out_dir, exist_ok=True)

    print("Loading Overlap")
    # Returns overlaps_dict: {well,fov}:[[inner[x][y][z][%],outer[x][y][z][%]]     myelin_dict: [(well,fov)] = [myelin,myelin50,myelin80]
    #overlaps_dict, myelin_dict = detectrims_Keyence(path,debug_path,  # Paths
    #                                        outerthresh,innerthresh,  # Perams
    #                                        dynamic_mode,debug_mode,skip) # Modes

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
             #overlaps_dict,nuclei_dict,areas_dict,myelin_dict,  # Dicts
             skip,further_analysis_mode) # Modes

end = time.time() - start
print(end)