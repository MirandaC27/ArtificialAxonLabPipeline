import imagej
import scyjava
import numpy as np
from pathlib import Path


ij = imagej.init("sc.fiji:fiji", mode="headless")
print(f"ImageJ version: {ij.getVersion()}")

# This was physically painful to figure out.
IJ       = scyjava.jimport("ij.IJ")
Prefs    = scyjava.jimport("ij.Prefs")
ResultsTable = scyjava.jimport("ij.measure.ResultsTable")
ParticleAnalyzer = scyjava.jimport("ij.plugin.filter.ParticleAnalyzer")
Measurements     = scyjava.jimport("ij.measure.Measurements")
ImageCalculator  = scyjava.jimport("ij.plugin.ImageCalculator")
ImagePlus        = scyjava.jimport("ij.ImagePlus")
WindowManager    = scyjava.jimport("ij.WindowManager")

#Thresholds
MYELIN_THRESH  = 8000
DEBRIS_THRESH  = 15000
#AXON_THRESH
#NUCLEI_THRESH


BASE_PATH = Path(r"*/CLEANED/ORDERED")
WELL_RANGE = range(2, 12)   


def ensure_dirs(dirs):
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

#bio format, loading channels
def load_channel(filepath, channel):
    #this is an array of functions for the bio formats importer
    #again, this was horrible to figure out
    #curse the PyImageJ documentation for giving NOTHING.
    options = (
        f"open=[{filepath}] "
        "color_mode=Default rois_import=[ROI manager] "
        "specify_range split_channels view=Hyperstack stack_order=XYCZT "
        f"series_1 c_begin_1={channel} c_end_1={channel} c_step_1=1"
    )
    IJ.run("Bio-Formats Importer", options)
    return IJ.getImage()

#use threshold to create a mask
def threshold_and_mask(imp, low, high):
    imp.getProcessor().setThreshold(low, high, imp.getProcessor().NO_LUT_UPDATE)
    IJ.run(imp, "Convert to Mask",
           "method=Default background=Default black")
    return imp

#auto thresholding for later.
def auto_threshold_mask(imp):
    IJ.run(imp, "Auto Threshold", "method=Default white")
    IJ.run(imp, "Convert to Mask",
           "method=Default background=Default black")
    return imp

def save_results(rt,out_path):
    rt.save(str(out_path))

def save_imp(imp, paths) -> None:
    for p in paths:
        IJ.saveAsTiff(imp, str(p))

#BAD ATTEMPTS AT MASK FUNCTIONS.
def pillar_mask(imp, dir_temp, dir_masks):
    save_imp(imp, dir_temp / "pillars.tif")

    IJ.run(imp, "Bandpass Filter",
                "filter_large=40 filter_small=3 suppress=None tolerance=5 process")
    auto_threshold_mask(imp)

    mask_pillars_path = dir_temp / "mask-pillars.tif"
    save_imp(imp, mask_pillars_path, dir_masks / "mask-pillars.tif")
    imp.close()
    return imp

def nuclei_mask(imp, dir_temp, dir_masks, dir_data):
    save_imp(imp, dir_temp / "nuclei.tif")

    auto_threshold_mask(imp)
    IJ.run(imp, "Watershed", "stack")

    mask_nuclei_path = dir_temp / "mask-nuclei.tif"
    save_imp(imp, mask_nuclei_path, dir_masks / "mask-nuclei.tif")

    # Count nuclei
    IJ.run("Set Scale:", "distance=0 known=0 unit=pixel")
    IJ.run("Set Measurements:", "redirect=None decimal=2")
    rt_nuclei = analyze_particles(
        imp,
        size_min=4, size_max=float("inf"),
        circ_min=0.20, circ_max=1.00,
        extra_flags=ParticleAnalyzer.SUMMARIZE,
    )
    save_results(rt_nuclei, dir_data / "nuclei.out")
    imp.close()
    return imp

def mylein_raw_mask(imp, dir_temp, dir_masks):
    save_imp(imp, dir_temp / "myelin.tif")

    threshold_and_mask(imp, MYELIN_THRESH)

    myelin_raw_name = f"mask-myelin-raw-{MYELIN_THRESH}.tif"
    save_imp(imp,
             dir_temp  / myelin_raw_name,
             dir_masks / myelin_raw_name)
    imp.close()
    return imp

def debris_mask(imp, dir_temp, dir_data, dir_masks):
    save_imp(imp, dir_temp / "debris.tif")

    threshold_and_mask(imp, DEBRIS_THRESH)

    debris_name = f"mask-debris-{DEBRIS_THRESH}.tif"
    save_imp(imp,
             dir_temp  / debris_name,
             dir_masks / debris_name)

    IJ.run("Set Scale:", "distance=0 known=0 unit=pixel")
    IJ.run("Set Measurements:",
           "area mean min shape integrated limit redirect=None decimal=2")
    rt_debris = analyze_particles(
        imp,
        size_min=2, size_max=2000,
        circ_min=0.20, circ_max=1.00,
        extra_flags=ParticleAnalyzer.SUMMARIZE,
    )
    save_results(rt_debris,
                 dir_data / f"Total-debris-{DEBRIS_THRESH}.out")
    imp.close()
    return imp

