#create_data.py

import imagej
import scyjava
from pathlib import Path
import sys

# Import settings collector from the frontend
sys.path.append(str(Path(__file__).resolve().parent))
from masking_front import collect_settings

SEGMENT_LOW  = 128
SEGMENT_HIGH = 255

def ensure_dirs(dirs):
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_field_dirs(well_path):
    return sorted([p for p in well_path.iterdir() if p.is_dir()])

def open_image(path):
    imp = IJ.openImage(str(path))
    if imp is None:
        raise FileNotFoundError(f"IJ.openImage returned None for: {path}")
    return imp

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
    print(f"  [process_field] {field_dir.name}")

    dir_masks   = field_dir / "MASKS"
    dir_objects = field_dir / "OBJECTS"
    dir_data    = field_dir / "DATA"
    ensure_dirs([dir_objects, dir_data])

    path_pillar    = dir_masks   / "mask-pillars-rim.tif"
    path_myelin    = dir_masks   / f"mask-myelin-overlap-{myelin_thresh}-{debris_thresh}.tif"
    path_objects   = dir_objects / f"Objects{myelin_thresh}.zip"
    path_converted = dir_data    / f"V_Data-{myelin_thresh}_converted.txt"

    imp_pillar = open_image(path_pillar)
    population = segment_and_save_objects(imp_pillar, path_objects)
    imp_pillar.close()

    imp_myelin = open_image(path_myelin)
    measure_and_save_volumes(population, path_converted)
    imp_myelin.close()

    IJ.run("Close All")
    IJ.run("Collect Garbage")
    print(f"  [process_field] done: {field_dir.name}")

def main():
   
    settings = collect_settings()
    if settings is None:
        print("Cancelled by user.")
        return

    base_path     = settings["base_path"]
    well_range    = settings["well_range"]
    thresholds    = settings["thresholds"]

    myelin_thresh = thresholds.get("myelin")
    debris_thresh = thresholds.get("debris")

    if myelin_thresh is None or debris_thresh is None:
        print("Error: myelin and debris thresholds are required.")
        return

    #FIX THIS. Remember that Fiji is now necessary because of the 3D object manager.
    FIJI_PATH  = base_path.parent.parent / "Fiji"   # adjust this relative path to match your layout
    mcib3d_dir = FIJI_PATH / "plugins" / "mcib3d-suite"
    scyjava.config.add_classpath(
        str(mcib3d_dir / "mcib3d-core-4.1.7b.jar"),
        str(mcib3d_dir / "mcib3d_plugins-4.1.7b.jar"),
        str(mcib3d_dir / "mcib3d_dev-0.0.2.jar"),
        str(mcib3d_dir / "quickhull3d-1.0.0.jar"),
        str(mcib3d_dir / "mcib3d-jipipe-0.0.3.jar"),
    )

    ij = imagej.init(str(FIJI_PATH), mode="headless")
    print(f"ImageJ version: {ij.getVersion()}")

    global IJ, WindowManager
    IJ            = scyjava.jimport("ij.IJ")
    WindowManager = scyjava.jimport("ij.WindowManager")

    # --- Main processing loop ---
    for k in well_range:
        well_name = f"B{k}"
        well_path = base_path / well_name
        print(f"\nProcessing well: {well_name}  ({well_path})")

        try:
            field_dirs = get_field_dirs(well_path)
        except FileNotFoundError:
            print(f"  Well directory not found, skipping: {well_path}")
            continue

        field_dirs = field_dirs[:9]
        print(f"  Found {len(field_dirs)} field(s) (capped at 9)")

        for field_dir in field_dirs:
            print(field_dir.name)
            try:
                process_field(field_dir, myelin_thresh, debris_thresh)
            except Exception as exc:
                print(f"  {field_dir.name}: {exc}")

    print("Done.")
    ij.dispose()

if __name__ == "__main__":
    main()