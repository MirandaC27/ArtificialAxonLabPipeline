#masking.py
import imagej
import scyjava
import argparse
import json
import os

scyjava.config.set_java_constraints(fetch="auto")
if os.getenv("JGO_CACHE_DIR"):
    scyjava.config.set_cache_dir(os.environ["JGO_CACHE_DIR"])
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

#rom view.masking_front import collect_settings


FIJI_PATH = Path(os.getenv("FIJI_PATH", "/opt/fiji"))
ij = imagej.init(str(FIJI_PATH), mode="headless")
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
CHANNEL_FILE_ALIASES = {
    "axon": ("axon", "axons", "pillar", "pillars"),
    "myelin": ("myelin", "mbp"),
    "nuclei": ("nuclei", "nucleus", "dapi"),
    "debris": ("debris",),
    "gfap": ("gfap",),
}


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


def find_channel_file(directory, channel):
    for keyword in CHANNEL_FILE_ALIASES.get(channel, (channel,)):
        try:
            return find_file(directory, keyword)
        except FileNotFoundError:
            pass
    aliases = ", ".join(CHANNEL_FILE_ALIASES.get(channel, (channel,)))
    raise FileNotFoundError(
        f"No TIFF for channel '{channel}' was found in {directory}. "
        f"Accepted filename terms: {aliases}."
    )


def load_channel(filepath, channel):
    """Open a TIFF and return a non-empty channel, using ``channel`` as a hint."""
    ChannelSplitter = scyjava.jimport("ij.plugin.ChannelSplitter")
    imp = IJ.openImage(str(filepath))
    if imp is None:
        raise FileNotFoundError(f"IJ.openImage returned None for: {filepath}")

    channel_count = imp.getNChannels()
    print(f"    [load_channel] {filepath.name}: {channel_count} channels, preferred channel {channel}")
    if channel_count <= 1:
        return imp

    channels = list(ChannelSplitter.split(imp))
    imp.close()

    def signal_mean(candidate):
        try:
            return float(candidate.getProcessor().getStatistics().mean)
        except (AttributeError, TypeError, ValueError):
            return None

    preferred_index = channel - 1 if 1 <= channel <= len(channels) else 0
    means = [signal_mean(candidate) for candidate in channels]
    selected_index = preferred_index
    preferred_mean = means[preferred_index]
    measurable = [(mean, index) for index, mean in enumerate(means) if mean is not None]
    if preferred_mean is not None and preferred_mean <= 0 and measurable:
        selected_index = max(measurable)[1]

    selected = channels[selected_index]
    for index, candidate in enumerate(channels):
        if index != selected_index:
            candidate.close()
    print(f"    [load_channel] selected channel {selected_index + 1}; means={means}")
    return selected


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


def save_particle_results(imp, output_path, size_min, size_max):
    rt = analyze_particles(imp, size_min, size_max, 0.20, 1.00)
    save_results(rt, output_path)


def threshold_channel_mask(imp, channel_name, threshold, dir_temp, dir_masks):
    save_imp(imp, dir_temp / f"{channel_name}.tif")
    if threshold in (None, "auto"):
        imp = auto_threshold_mask(imp)
    else:
        imp = threshold_and_mask(imp, threshold)
    save_imp(
        imp,
        dir_temp / f"mask-{channel_name}-{threshold}.tif",
        dir_masks / f"mask-{channel_name}-{threshold}.tif",
    )
    return imp


def process_field(field_dir, settings):
    """Create masks and measurements only for channels enabled by the session."""
    thresholds = settings["thresholds"]
    particle_size = settings["particle_size"]
    skip_channels = settings.get("skip_channels", set())
    configured_channels = {
        str(label).strip().lower()
        for label in settings.get("active_channels", [])
        if str(label).strip()
    }
    if "active_channels" in settings:
        active_channels = configured_channels
    else:
        active_channels = MASKING_REQUIRED_CHANNELS - skip_channels
    if not active_channels:
        raise ValueError("At least one analysis channel must be active.")
    channel_numbers = settings.get("channel_numbers") or {}
    myelin_thresh = thresholds.get("myelin") or 8000
    debris_thresh = thresholds.get("debris") or 15000
    nuclei_thresh = thresholds.get("nuclei")
    gfap_thresh = thresholds.get("gfap", thresholds.get("GFAP"))
    size_min = particle_size.get("min") or 2
    size_max = particle_size.get("max") or 2000

    print(f"  [process_field] starting {field_dir.name}; channels={sorted(active_channels)}")
    dir_oir = field_dir / "OIR"
    dir_temp = field_dir / "TEMP"
    dir_data = field_dir / "DATA"
    dir_masks = field_dir / "MASKS"
    ensure_dirs([dir_temp, dir_data, dir_masks])

    def channel_number(label, fallback):
        try:
            return int(channel_numbers.get(label, fallback))
        except (TypeError, ValueError):
            return fallback

    if "nuclei" in active_channels:
        imp = load_channel(find_channel_file(dir_oir, "nuclei"), channel_number("nuclei", 3))
        nuclei_mask(imp, dir_temp, dir_masks, dir_data, nuclei_thresh)

    if "axon" in active_channels:
        imp = load_channel(find_channel_file(dir_oir, "axon"), channel_number("axon", 1))
        imp = pillar_mask(imp, dir_temp, dir_masks)
        save_particle_results(imp, dir_data / "Total-2D-axons.out", size_min, size_max)
        imp.close()

    imp_debris = None
    if "debris" in active_channels:
        imp_debris = load_channel(
            find_channel_file(dir_oir, "debris"), channel_number("debris", 2)
        )
        imp_debris = debris_mask(
            imp_debris, dir_temp, dir_data, dir_masks, debris_thresh
        )
        save_particle_results(
            imp_debris,
            dir_data / f"Total-2D-debris-{debris_thresh}.out",
            size_min,
            size_max,
        )

    imp_myelin_clean = None
    if "myelin" in active_channels:
        imp_myelin = load_channel(
            find_channel_file(dir_oir, "myelin"), channel_number("myelin", 3)
        )
        imp_myelin = myelin_raw_mask(
            imp_myelin, dir_temp, dir_masks, myelin_thresh
        )
        if imp_debris is not None:
            imp_myelin.show()
            imp_debris.show()
            imp_myelin_clean = ImageCalculator().run(
                "Subtract create", imp_myelin, imp_debris
            )
            imp_myelin.hide()
            imp_debris.hide()
            suffix = f"{myelin_thresh}-{debris_thresh}"
        else:
            imp_myelin_clean = imp_myelin.duplicate()
            suffix = str(myelin_thresh)
        save_imp(imp_myelin_clean, dir_masks / f"mask-myelin-{myelin_thresh}.tif")
        save_particle_results(
            imp_myelin_clean,
            dir_data / f"Total-MBP-2D-{suffix}.out",
            size_min,
            size_max,
        )
        imp_myelin.close()

    if "gfap" in active_channels:
        imp_gfap = load_channel(
            find_channel_file(dir_oir, "gfap"), channel_number("gfap", 1)
        )
        imp_gfap = threshold_channel_mask(
            imp_gfap, "GFAP", gfap_thresh, dir_temp, dir_masks
        )
        save_particle_results(
            imp_gfap,
            dir_data / f"Total-2D-GFAP-{gfap_thresh}.out",
            size_min,
            size_max,
        )
        imp_gfap.close()

    if imp_debris is not None:
        imp_debris.close()

    if "axon" in active_channels and imp_myelin_clean is not None:
        pillar_rim = IJ.openImage(str(dir_temp / "mask-pillars.tif"))
        show_run_hide(pillar_rim, "Dilate", "stack")
        show_run_hide(pillar_rim, "Watershed", "stack")
        show_run_hide(pillar_rim, "Outline", "stack")
        save_imp(
            pillar_rim,
            dir_temp / "mask-pillars-rim.tif",
            dir_masks / "mask-pillars-rim.tif",
        )
        pillar_rim.show()
        imp_myelin_clean.show()
        overlap = ImageCalculator().run(
            "Multiply create", pillar_rim, imp_myelin_clean
        )
        pillar_rim.hide()
        imp_myelin_clean.hide()
        overlap_name = f"mask-myelin-overlap-{myelin_thresh}-{debris_thresh}.tif"
        save_imp(overlap, dir_masks / overlap_name, dir_temp / overlap_name)
        pillar_rim.close()
        overlap.close()

    if imp_myelin_clean is not None:
        imp_myelin_clean.close()
    print(f" {field_dir.name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wells", help="Comma-separated well numbers assigned to this worker")
    args = parser.parse_args()
    # Collect settings from the UI 
    DATA_DIR = PROJECT_ROOT / "data"

    with open(DATA_DIR / "masking_settings.json", "r") as f:
        settings = json.load(f)

    base_path  = Path(settings["base_path"])
    well_range = settings["well_range"]
    if args.wells:
        well_range = [int(value) for value in args.wells.split(",") if value.strip()]
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

    failures = []
    #  Process wells
    for k in well_range:
        well_name = f"B{k:02d}"
        well_path = base_path / well_name
        print(f"\nProcessing well: {well_name}  ({well_path})")

        try:
            field_dirs = sorted([p for p in well_path.iterdir() if p.is_dir()])
        except FileNotFoundError:
            print(f"Well directory not found, skipping: {well_path}")
            print(f"AXONLAB_PROGRESS::{well_name}", flush=True)
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
                failures.append(f"{well_name}/{field_dir.name}: {exc}")
        print(f"AXONLAB_PROGRESS::{well_name}", flush=True)
    if failures:
        raise RuntimeError("Masking failed for " + "; ".join(failures))


if __name__ == "__main__":
    main()
    ij.dispose()
