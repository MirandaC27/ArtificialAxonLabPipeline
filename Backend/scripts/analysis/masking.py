#masking.py
import imagej
import scyjava
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

#rom view.masking_front import collect_settings


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

CONFIG_PATH = PROJECT_ROOT / "data" / "upload_settings.json"
MASKING_REQUIRED_CHANNELS = {"axon", "myelin", "nuclei", "debris"}


def ensure_dirs(dirs):
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def load_skip_config():
    if not CONFIG_PATH.exists():
        return {
            "skip_fovs": set(),
            "skip_channels": set(),
            "skip_fovs_per_well": {},
        }

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_skip_fovs = list(data.get("DisabledFOVs", [])) + list(data.get("SkipFOVs", []))
    skip_fovs = {
        int(fov)
        for fov in raw_skip_fovs
        if str(fov).strip().isdigit()
    }
    skip_channels = {
        str(label).strip().lower()
        for label in data.get("SkipChannels", [])
        if str(label).strip()
    }
    skip_channels.update(
        ch["label"].strip().lower()
        for ch in data.get("Channels", [])
        if ch.get("label") and not ch.get("active", True)
    )

    raw_per_well = data.get("SkipFOVsPerWell", {})
    skip_fovs_per_well = {}
    for well, fovs in raw_per_well.items():
        skip_fovs_per_well[well] = {
            int(fov) for fov in fovs if str(fov).strip().isdigit()
        }

    return {
        "skip_fovs": skip_fovs,
        "skip_channels": skip_channels,
        "skip_fovs_per_well": skip_fovs_per_well,
    }


def parse_fov_num(field_name):
    parts = field_name.split("_")
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return int(parts[1])


def should_skip_field(well_name, field_name, skip_config):
    fov_num = parse_fov_num(field_name)
    if fov_num is None:
        return False

    if fov_num in skip_config["skip_fovs"]:
        return True

    return fov_num in skip_config["skip_fovs_per_well"].get(well_name, set())


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
    return IJ.getImage()


def threshold_and_mask(imp, low, high=65535):
    imp.show()
    imp.getProcessor().setThreshold(low, high, imp.getProcessor().NO_LUT_UPDATE)
    ij.py.run_macro('run("Convert to Mask");')
    return IJ.getImage()


def auto_threshold_mask(imp):
    imp.show()
    ij.py.run_macro('run("Auto Threshold", "method=Default white");')
    ij.py.run_macro('run("Convert to Mask");')
    return IJ.getImage()


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


def nuclei_mask(imp, dir_temp, dir_masks, dir_data, thresh_nuclei):
    save_imp(imp, dir_temp / "nuclei.tif")
    if thresh_nuclei == "auto":
        imp = auto_threshold_mask(imp)
    elif thresh_nuclei is not None:
        imp = threshold_and_mask(imp, thresh_nuclei)
    else:
        imp = auto_threshold_mask(imp)
    imp = show_run_hide(imp, "Watershed", "stack")
    save_imp(imp, dir_masks / "mask-nuclei.tif")

    rt_nuclei = ResultsTable()
    options = ParticleAnalyzer.SHOW_NONE | ParticleAnalyzer.INCLUDE_HOLES
    measurements = Measurements.AREA
    pa = ParticleAnalyzer(options, measurements, rt_nuclei, 10, float("inf"), 0.0, 1.0)
    pa.analyze(imp)

    count_rt = ResultsTable()
    count_rt.incrementCounter()
    count_rt.addValue("Count", rt_nuclei.size())
    save_results(count_rt, dir_data / "nuclei.out")

    imp.close()


def myelin_raw_mask(imp, dir_temp, dir_masks, myelin_thresh):
    print(f"    [myelin_raw_mask] starting")
    save_imp(imp, dir_temp / "myelin.tif")
    if myelin_thresh == "auto":
        imp = auto_threshold_mask(imp)
    else:
        imp = threshold_and_mask(imp, myelin_thresh)
    myelin_raw_name = f"mask-myelin-raw-{myelin_thresh}.tif"
    save_imp(imp,
             dir_temp  / myelin_raw_name,
             dir_masks / myelin_raw_name)
    return imp


def debris_mask(imp, dir_temp, dir_data, dir_masks, debris_thresh):
    save_imp(imp, dir_temp / "debris.tif")
    if debris_thresh == "auto":
        imp = auto_threshold_mask(imp)
    else:
        imp = threshold_and_mask(imp, debris_thresh)
    debris_name = f"mask-debris-{debris_thresh}.tif"
    save_imp(imp,
             dir_temp  / debris_name,
             dir_masks / debris_name)
    return imp


def process_field(field_dir, settings):
    """
    Process a single field directory using the provided settings dict.

    settings keys expected:
        thresholds    – dict from get_thresholds()  e.g. {"myelin": 8000, "debris": 15000, ...}
        particle_size – dict from get_particle_size() e.g. {"min": 2, "max": 2000}
    """
    thresholds    = settings["thresholds"]
    particle_size = settings["particle_size"]
    skip_channels = settings.get("skip_channels", set())

    myelin_thresh = thresholds.get("myelin") or 8000
    debris_thresh = thresholds.get("debris") or 15000
    nuclei_thresh = thresholds.get("nuclei")          

    size_min = particle_size.get("min") or 2
    size_max = particle_size.get("max") or 2000

    missing_required = sorted(MASKING_REQUIRED_CHANNELS & skip_channels)
    if missing_required:
        print(f"  [process_field] skipping {field_dir.name}; excluded channels: {', '.join(missing_required)}")
        return

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
    nuclei_mask(imp_nuclei, dir_temp, dir_masks, dir_data, nuclei_thresh)

    imp_myelin = load_channel(path_myelin, channel=3)
    imp_myelin = myelin_raw_mask(imp_myelin, dir_temp, dir_masks, myelin_thresh)

    imp_debris = load_channel(path_debris, channel=2)
    imp_debris = debris_mask(imp_debris, dir_temp, dir_data, dir_masks, debris_thresh)

    imp_myelin.show()
    imp_debris.show()
    ic = ImageCalculator()
    imp_myelin_clean = ic.run("Subtract create", imp_myelin, imp_debris)
    imp_myelin.hide()
    imp_debris.hide()

    myelin_clean_name = f"mask-myelin-{myelin_thresh}.tif"
    save_imp(imp_myelin_clean, dir_masks / myelin_clean_name)

    IJ.run("Set Scale...", "distance=0 known=0 unit=pixel")
    IJ.run("Set Measurements...",
           "area mean min shape integrated limit redirect=None decimal=2")
    rt_myelin = analyze_particles(
        imp_myelin_clean,
        size_min=size_min, size_max=size_max,
        circ_min=0.20, circ_max=1.00,
    )
    save_results(rt_myelin,
                 dir_data / f"Total-MBP-2D-{myelin_thresh}-{debris_thresh}.out")

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

    overlap_name = f"mask-myelin-overlap-{myelin_thresh}-{debris_thresh}.tif"
    save_imp(imp_overlap,
             dir_masks / overlap_name,
             dir_temp  / overlap_name)

    for imp in (imp_pillars_reload, imp_myelin_clean, imp_overlap):
        imp.close()

    print(f" {field_dir.name}")


def main():
    # Collect settings from the UI 
    DATA_DIR = PROJECT_ROOT / "data"

    with open(DATA_DIR / "masking_settings.json", "r") as f:
        settings = json.load(f)

    base_path  = Path(settings["base_path"])
    well_range = settings["well_range"]
    skip_config = load_skip_config()
    settings["skip_channels"] = skip_config["skip_channels"]

    print(f"\nBase path:  {base_path}")
    print(f"Well range: {list(well_range)}")
    print(f"Thresholds: {settings['thresholds']}")
    print(f"Particles:  {settings['particle_size']}\n")
    if skip_config["skip_fovs"] or skip_config["skip_channels"] or skip_config["skip_fovs_per_well"]:
        print(f"Skip FOVs: {sorted(skip_config['skip_fovs'])}")
        print(f"Skip channels: {sorted(skip_config['skip_channels'])}")
        print(f"Per-well skipped FOVs: {skip_config['skip_fovs_per_well']}\n")

    #  Process wells 
    for k in well_range:
        well_name = f"B{k:02d}"
        well_path = base_path / well_name
        print(f"\nProcessing well: {well_name}  ({well_path})")

        try:
            field_dirs = sorted([p for p in well_path.iterdir() if p.is_dir()])
        except FileNotFoundError:
            print(f"Well directory not found, skipping: {well_path}")
            continue

        print(f"Found {len(field_dirs)} field(s)")
        for field_dir in field_dirs:
            if should_skip_field(well_name, field_dir.name, skip_config):
                print(f"  - {field_dir.name}: skipped by config")
                continue
            try:
                process_field(field_dir, settings)
            except Exception as exc:
                print(f"  X {field_dir.name}: {exc}")


if __name__ == "__main__":
    main()
    ij.dispose()
