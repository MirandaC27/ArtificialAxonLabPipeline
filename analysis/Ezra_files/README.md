THIS ALGORITHM REQUIRES MASKS FROM 'GetMasksNew.ijm'
CHECK THE PATHS TO THE SET AND OUTPUT

REQUIRED LIBRARY INSTALLAIONS:
pip install opencv-python
pip install numpy
pip install tifffile
pip install scipy
pip install pandas
conda install -n base -c conda-forge mamba
mamba install -c conda-forge opencv numpy tifffile pandas scipy


dynamic_mode = False  # IF THE NUMBER OF AXONS IS INCORRECT CHANGE THIS TO 'True' TO MAKE MAX DISTANCE BETWEEN PILLARS DYNAMIC
debug_mode = True # IF YOU WANT TO DEBUG, MAKE SURE ONLY ONE SET IS BEING RUN OTHERWISE EACH SET WILL OVERWRITE THE LAST
include_uncondensed = True # UNCONDENSED MYELINATION WILL BE REMOVED FROM RESULTS WHEN THIS IS FALSE
test_skip = [] # THIS IS FOR TESTING SKIPPING LAYER. LAYERS IN THE LIST WILL BE SKIPPED. THE ANALYSIS FUNCTION NEEDS TO BE MANUALLY CHANGED IF SKIPPED LAYERS CAUSE GAPS

To run this algorithm: 
1. A set number must be specified as 'setnum' in 'main.py.'
2. Enter 'cd reg_analyze' into the terminal to enter the regular analysis folder
3. Enter 'python main.py' into the terminal to run the algorithm (If computer uses python3 type 'python3 main.py')

What is in this algorithm:
1. detectrims.py -- overlaps_dict, myelin_dict = detectrims(path,widethresh,narrowthresh)
    a. Loops through each well and fov in the set and reads the myelin mask(s) and pillar mask
        b. Loops through each mask by z slice
            c. Creates inner and outer rims through dilating the pillar mask
            d. Finds closest inner center for each outer center (max-distance is hard set at the top)
            e. Create a mask for the rims and draw the contour
            f. Overlap rim masks with myelin masks
            g. Find percent overlap and add/create to pillar
            h. Add pixels to bins if thresholds are met (this is for counting myelin pixels in analysis.py)
        i. Store in dicts
2. detectnuclei.py -- nuclei_dict = detectnuclei(path)
    a. Read nuclei mask
    b. Find contours and count them
    c. Store in dict
3. detectmyelinarea.py -- areas_dict = detectmyelinarea(path,narrowthresh)
    a. Read myelin mask
    b. Z-project mask
    c. Count nonzero pixels
    d. Store in dict
4. analysis.py -- analysis(path,out_path,overlaps_dict,nuclei_dict,areas_dict,myelin_dict)
    a. Initialize output lists
    b. Append to lists from dicts
    c. Loop through pillars
    d. Make sorted lists with 50% and 80% thresholds
    e. If there is any wrapping, increment pillar count
    f. Find longest runs of 50% and 80% lists
    g. Bin the pillar depending on the length of the longest run
    h. Append results to output lists
    i. Make csv table of outputs