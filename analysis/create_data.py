import imagej
import scyjava
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

CONFIG_PATH = PROJECT_ROOT / "data" / "upload_settings.json"

SEGMENT_LOW  = 128
SEGMENT_HIGH = 255


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

def ensure_dirs(dirs):
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def load_channels_from_config():
    """Matches frontend + masking source of truth."""
    if not CONFIG_PATH.exists():
        return []

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("Channels", [])


def get_required_channels():
    """Channels required for create_data stage."""
    return {"axon", "myelin", "debris"}


def load_skip_config():
    """Identical to masking.py — reads from upload_settings.json."""
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


def get_field_dirs(well_path):
    return sorted([p for p in well_path.iterdir() if p.is_dir()])


def open_image(path):
    IJ = scyjava.jimport("ij.IJ")
    imp = IJ.openImage(str(path))
    if imp is None:
        raise FileNotFoundError(f"IJ.openImage returned None for: {path}")
    return imp


# ---------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------

def segment_and_save_objects(imp_pillar, path_objects):
    ImageHandler           = scyjava.jimport("mcib3d.image3d.ImageHandler")
    Objects3DIntPopulation = scyjava.jimport("mcib3d.geom2.Objects3DIntPopulation")
    ImageLabeller          = scyjava.jimport("mcib3d.image3d.ImageLabeller")

    img_binary  = ImageHandler.wrap(imp_pillar)
    labeller    = ImageLabeller()
    img_labeled = labeller.getLabels(img_binary)

    pop = Objects3DIntPopulation(img_labeled)
    n   = pop.getNbObjects()

    print(f"    [segment_and_save_objects] segmented {n} objects")
    pop.saveObjects(str(path_objects))
    print(f"    [segment_and_save_objects] saved to {path_objects.name}")

    return pop


def measure_and_save_volumes(population, path_converted):
    lines   = ["Object\tVolume"]
    objects = population.getObjects3DInt()
    n       = population.getNbObjects()

    for i in range(n):
        obj    = objects.get(i)
        volume = obj.size()
        lines.append(f"{i + 1}\t{volume}")

    path_converted.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"    [measure_and_save_volumes] {n} objects to {path_converted.name}")


def process_field(field_dir, myelin_thresh, debris_thresh):
    IJ = scyjava.jimport("ij.IJ")

    print(f"  [process_field] {field_dir.name}")

    dir_masks   = field_dir / "MASKS"
    dir_objects = field_dir / "OBJECTS"
    dir_data    = field_dir / "DATA"
    ensure_dirs([dir_objects, dir_data])

    path_pillar    = dir_masks   / "mask-pillars-rim.tif"
    path_objects   = dir_objects / f"Objects{myelin_thresh}.zip"
    path_converted = dir_data    / f"V_Data-{myelin_thresh}_converted.txt"

    imp_pillar = open_image(path_pillar)
    population = segment_and_save_objects(imp_pillar, path_objects)
    imp_pillar.close()

    # NOTE: myelin mask was opened before but never used → removed

    measure_and_save_volumes(population, path_converted)

    IJ.run("Close All")
    IJ.run("Collect Garbage")

    print(f"  [process_field] done: {field_dir.name}")


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main(settings):
    print("DEBUG received base_path:", settings["base_path"])

    base_path = Path(settings["base_path"])

    if base_path.name.lower() != "ordered":
        ordered_candidate = base_path / "ORDERED"
        if ordered_candidate.exists():
            base_path = ordered_candidate
        else:
            print(f"WARNING: ORDERED folder not found inside {base_path}")

    well_start = settings.get("well_start")
    well_end   = settings.get("well_end")

    well_range = settings.get("well_range")

    if well_range is None:
        if well_start is None or well_end is None:
            raise ValueError(
                "Missing well_range OR well_start/well_end in settings"
            )
        well_range = range(well_start, well_end + 1)

    thresholds    = settings["thresholds"]
    myelin_thresh = thresholds.get("myelin") or 8000
    debris_thresh = thresholds.get("debris") or 15000

    skip_config = load_skip_config()

    # 🔥 CRITICAL: match masking.py behavior
    skip_channels = settings.get("skip_channels", skip_config["skip_channels"])
    skip_config["skip_channels"] = skip_channels

    print(f"\nBase path:  {base_path}")
    print(f"Well range: {list(well_range)}")
    print(f"Thresholds — myelin: {myelin_thresh}, debris: {debris_thresh}")

    if skip_config["skip_fovs"] or skip_config["skip_channels"] or skip_config["skip_fovs_per_well"]:
        print(f"Skip FOVs: {sorted(skip_config['skip_fovs'])}")
        print(f"Skip channels: {sorted(skip_config['skip_channels'])}")
        print(f"Per-well skipped FOVs: {skip_config['skip_fovs_per_well']}\n")

    # -----------------------------------------------------------------
    # Channel validation (NEW)
    # -----------------------------------------------------------------
    required_channels = get_required_channels()

    channels = load_channels_from_config()
    available_channels = {
        ch.get("label", "").strip().lower()
        for ch in channels if ch.get("label")
    }

    missing_from_data = required_channels - available_channels
    if missing_from_data:
        print(f"WARNING: Required channels not present in upload: {missing_from_data}")

    # Guard: skip if required channels are disabled
    missing_required = sorted(required_channels & skip_config["skip_channels"])
    if missing_required:
        print(
            f"Skipping create_data stage because required channels are excluded: "
            f"{', '.join(missing_required)}"
        )
        return

    # -----------------------------------------------------------------
    # Process wells
    # -----------------------------------------------------------------
    for k in well_range:
        well_name = f"B{k:02d}"
        well_path = base_path / well_name

        print(f"\nProcessing well: {well_name}  ({well_path})")

        try:
            field_dirs = get_field_dirs(well_path)
        except FileNotFoundError:
            print(f"  Well directory not found, skipping: {well_path}")
            continue

        print(f"  Found {len(field_dirs)} field(s)")

        for field_dir in field_dirs:
            if should_skip_field(well_name, field_dir.name, skip_config):
                print(f"  - {field_dir.name}: skipped by config")
                continue

            try:
                process_field(field_dir, myelin_thresh, debris_thresh)
            except Exception as exc:
                print(f"  X {field_dir.name}: {exc}")

    print("Done.")




if __name__ == "__main__":
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        _cfg = json.load(f)

    _base_path = _cfg.get("OrderedTrack", "")

    _fiji_path  = Path(_base_path).parent.parent / "Fiji"
    _mcib3d_dir = _fiji_path / "plugins" / "mcib3d-suite"

    scyjava.config.add_classpath(
        str(_mcib3d_dir / "mcib3d-core-4.1.7b.jar"),
        str(_mcib3d_dir / "mcib3d_plugins-4.1.7b.jar"),
        str(_mcib3d_dir / "mcib3d_dev-0.0.2.jar"),
        str(_mcib3d_dir / "quickhull3d-1.0.0.jar"),
        str(_mcib3d_dir / "mcib3d-jipipe-0.0.3.jar"),
    )

    ij = imagej.init(str(_fiji_path), mode="headless")
    print(f"ImageJ version: {ij.getVersion()}")

    _skip = load_skip_config()

    _settings = {
        "base_path": _base_path,
        "well_range": range(10, 11),
        "thresholds": {
            "myelin": _cfg.get("MyelinThreshold", 8000),
            "debris": _cfg.get("DebrisThreshold", 1500),
        },
        "skip_channels": _skip["skip_channels"],  
    }

    try:
        main(_settings)
    finally:
        ij.dispose()