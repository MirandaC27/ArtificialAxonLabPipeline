import imagej
import scyjava
from pathlib import Path


ij = imagej.init("sc.fiji:fiji", mode="headless")
print(f"ImageJ version: {ij.getVersion()}")

IJ               = scyjava.jimport("ij.IJ")
Prefs            = scyjava.jimport("ij.Prefs")
ResultsTable     = scyjava.jimport("ij.measure.ResultsTable")
ParticleAnalyzer = scyjava.jimport("ij.plugin.filter.ParticleAnalyzer")
Measurements     = scyjava.jimport("ij.measure.Measurements")
ImageCalculator  = scyjava.jimport("ij.plugin.ImageCalculator")
ImagePlus        = scyjava.jimport("ij.ImagePlus")
WindowManager    = scyjava.jimport("ij.WindowManager")

# Thresholds
MYELIN_THRESH = 8000
DEBRIS_THRESH = 15000
#nucleithresh = 70;	optional, can be auto-thresholded
# axonthresh=35000;

BASE_PATH  = Path(r"/Users/chloemiranda/capstone/CLEANED/ORDERED")
WELL_RANGE = range(2, 12)



def ensure_dirs(dirs):
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def find_file(directory, keyword):
    all_tifs = list(directory.glob("*.tif")) + list(directory.glob("*.TIF"))

    print(f"    [find_file] searching '{directory}' for keyword '{keyword}'")
    print(f"    [find_file] all .tif files found: {[f.name for f in all_tifs]}")

    matches = [f for f in all_tifs if keyword.lower() in f.name.lower()]

    if len(matches) == 0:
        raise FileNotFoundError(
            f"No .tif file containing '{keyword}' found in {directory}\n"
            f"  Files present: {[f.name for f in all_tifs]}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"Multiple .tif files containing '{keyword}' found in {directory}: {matches}"
        )
    print(f"    [find_file] matched: {matches[0].name}")
    return matches[0]


def load_channel(filepath, channel):
    """
    Opens a tif and extracts a single channel (1-based).
    """
    ChannelSplitter = scyjava.jimport("ij.plugin.ChannelSplitter")
    imp = IJ.openImage(str(filepath))
    if imp is None:
        raise FileNotFoundError(f"IJ.openImage returned None for: {filepath}")
    
    print(f"    [load_channel] {filepath.name}: {imp.getNChannels()} channels, extracting channel {channel}")
    
    if imp.getNChannels() > 1:
        channels = ChannelSplitter.split(imp)
        imp.close()
        return channels[channel - 1]
    return imp


def show_run_hide(imp, command, args=""):
    imp.show()
    if args:
        ij.py.run_macro(f'run("{command}", "{args}");')
    else:
        ij.py.run_macro(f'run("{command}");')
    return IJ.getImage()    # return the current image after processing


def threshold_and_mask(imp, low, high=65535):
    imp.show()
    imp.getProcessor().setThreshold(low, high, imp.getProcessor().NO_LUT_UPDATE)
    ij.py.run_macro('run("Convert to Mask");')
    return IJ.getImage()    # return current image, not the original imp


def auto_threshold_mask(imp):
    imp.show()
    ij.py.run_macro('run("Auto Threshold", "method=Default white");')
    ij.py.run_macro('run("Convert to Mask");')
    return IJ.getImage()    # return current image
def save_results(rt, out_path):
    rt.save(str(out_path))


def save_imp(imp, *paths):
    for p in paths:
        IJ.saveAsTiff(imp, str(p))


def analyze_particles(imp, size_min, size_max, circ_min, circ_max):
    rt = ResultsTable()
    options = ParticleAnalyzer.SHOW_NONE
    measurements = (
        Measurements.AREA
        | Measurements.MEAN
        | Measurements.MIN_MAX
        | Measurements.SHAPE_DESCRIPTORS
        | Measurements.INTEGRATED_DENSITY
        | Measurements.LIMIT
    )
    pa = ParticleAnalyzer(options, measurements, rt,
                          size_min, size_max, circ_min, circ_max)
    pa.analyze(imp)
    return rt



def pillar_mask(imp, dir_temp, dir_masks):
    save_imp(imp, dir_temp / "pillars.tif")
    imp = show_run_hide(imp, "Bandpass Filter...",
                        "filter_large=40 filter_small=3 suppress=None tolerance=5 process")
    imp = auto_threshold_mask(imp)
    save_imp(imp, dir_temp / "mask-pillars.tif", dir_masks / "mask-pillars.tif")
    return imp


def nuclei_mask(imp, dir_temp, dir_masks, dir_data):
    save_imp(imp, dir_temp / "nuclei.tif")
    imp = auto_threshold_mask(imp)
    imp = show_run_hide(imp, "Watershed", "stack")
    save_imp(imp, dir_masks / "mask-nuclei.tif")
    imp.close()


def myelin_raw_mask(imp, dir_temp, dir_masks):
    print(f"    [myelin_raw_mask] starting")
    save_imp(imp, dir_temp / "myelin.tif")
    imp = threshold_and_mask(imp, MYELIN_THRESH)
    myelin_raw_name = f"mask-myelin-raw-{MYELIN_THRESH}.tif"   
    save_imp(imp,
             dir_temp  / myelin_raw_name,
             dir_masks / myelin_raw_name)
    return imp


def debris_mask(imp, dir_temp, dir_data, dir_masks):
    save_imp(imp, dir_temp / "debris.tif")
    imp = threshold_and_mask(imp, DEBRIS_THRESH)
    debris_name = f"mask-debris-{DEBRIS_THRESH}.tif"   # make sure this is still here
    save_imp(imp,
             dir_temp  / debris_name,
             dir_masks / debris_name)
    
    return imp


def process_field(field_dir):
    print(f"  [process_field] starting {field_dir.name}")
    dir_oir   = field_dir / "OIR"
    dir_temp  = field_dir / "TEMP"
    dir_data  = field_dir / "DATA"
    dir_masks = field_dir / "MASKS"
    ensure_dirs([dir_temp, dir_data, dir_masks])

    path_nuclei  = find_file(dir_oir, "nuclei")
    path_myelin  = find_file(dir_oir, "myelin")
    path_debris  = find_file(dir_oir, "debris")
    path_pillars = find_file(dir_oir, "axon")


    imp_pillars = load_channel(path_pillars, channel=1)
    imp_pillars = pillar_mask(imp_pillars, dir_temp, dir_masks)

    imp_nuclei = load_channel(path_nuclei, channel=3)
    nuclei_mask(imp_nuclei, dir_temp, dir_masks, dir_data)

    imp_myelin = load_channel(path_myelin, channel=3)
    imp_myelin = myelin_raw_mask(imp_myelin, dir_temp, dir_masks)

    imp_debris = load_channel(path_debris, channel=2)
    imp_debris = debris_mask(imp_debris, dir_temp, dir_data, dir_masks)

    imp_myelin.show()
    imp_debris.show()
    ic = ImageCalculator()
    imp_myelin_clean = ic.run("Subtract create", imp_myelin, imp_debris)
    imp_myelin.hide()
    imp_debris.hide()

    myelin_clean_name = f"mask-myelin-{MYELIN_THRESH}.tif"
    save_imp(imp_myelin_clean, dir_masks / myelin_clean_name)

    IJ.run("Set Scale...", "distance=0 known=0 unit=pixel")
    IJ.run("Set Measurements...",
           "area mean min shape integrated limit redirect=None decimal=2")
    rt_myelin = analyze_particles(
        imp_myelin_clean,
        size_min=2, size_max=2000,
        circ_min=0.20, circ_max=1.00,
    )
    save_results(rt_myelin,
                 dir_data / f"Total-MBP-2D-{MYELIN_THRESH}-{DEBRIS_THRESH}.out")

    imp_myelin.close()
    imp_debris.close()

    imp_pillars_reload = IJ.openImage(str(dir_temp / "mask-pillars.tif"))
    show_run_hide(imp_pillars_reload, "Dilate",    "stack")
    show_run_hide(imp_pillars_reload, "Watershed", "stack")
    show_run_hide(imp_pillars_reload, "Outline",   "stack")

    save_imp(imp_pillars_reload,
             dir_temp  / "mask-pillars-rim.tif",
             dir_masks / "mask-pillars-rim.tif")


    imp_pillars_reload.show()
    imp_myelin_clean.show()
    ic2 = ImageCalculator()
    imp_overlap = ic2.run("Multiply create", imp_pillars_reload, imp_myelin_clean)
    imp_pillars_reload.hide()
    imp_myelin_clean.hide()

    overlap_name = f"mask-myelin-overlap-{MYELIN_THRESH}-{DEBRIS_THRESH}.tif"
    save_imp(imp_overlap,
             dir_masks / overlap_name,
             dir_temp  / overlap_name)

    for imp in (imp_pillars_reload, imp_myelin_clean, imp_overlap):
        imp.close()

    print(f" {field_dir.name}")



def main():
    for k in WELL_RANGE:
        well_name = f"B{k:02d}"
        well_path = BASE_PATH / well_name
        print(f"\nProcessing well: {well_name}  ({well_path})")

        try:
            field_dirs = sorted([p for p in well_path.iterdir() if p.is_dir()])
        except FileNotFoundError:
            print(f"Well directory not found, skipping: {well_path}")
            continue

        print(f"Found {len(field_dirs)} field(s)")
        for field_dir in field_dirs:
            try:
                process_field(field_dir)
            except Exception as exc:
                print(f"  ✗ {field_dir.name}: {exc}")


if __name__ == "__main__":
    main()
    ij.dispose()