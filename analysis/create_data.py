import imagej
import scyjava
from pathlib import Path

ij = imagej.init("/Users/chloemiranda/capstone/Fiji", mode="headless")
print(f"ImageJ version: {ij.getVersion()}")

IJ            = scyjava.jimport("ij.IJ")
WindowManager = scyjava.jimport("ij.WindowManager")

# Thresholds
MYELIN_THRESH = 24500

BASE_PATH  = Path(r"/Users/chloemiranda/capstone/CLEANED/ORDERED")
WELL_RANGE = range(10, 11)  # k=10 to k=10 inclusive


def ensure_dirs(dirs):
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def get_field_dirs(well_path):
    """Return sorted list of subdirectories (fields) in a well directory."""
    return sorted([p for p in well_path.iterdir() if p.is_dir()])


def process_field_3d(field_dir, manager3d):
    """
    Process a single field:
      1. Open pillar rim mask → segment with 3D Manager → save objects
      2. Open myelin overlap mask → measure volume → save & convert results
      3. Clean up 3D Manager and close all images
    """
    print(f"  [process_field_3d] {field_dir.name}")

    dir_masks   = field_dir / "MASKS"
    dir_objects = field_dir / "OBJECTS"
    dir_data    = field_dir / "DATA"
    ensure_dirs([dir_objects, dir_data])

    pillar_name  = "mask-pillars-rim.tif"
    myelin_name  = f"mask-myelin-overlap-{MYELIN_THRESH}-clean.tif"
    objects_name = f"Objects{MYELIN_THRESH}.zip"
    data_name    = f"Data-{MYELIN_THRESH}.txt"

    path_pillar  = dir_masks   / pillar_name
    path_myelin  = dir_masks   / myelin_name
    path_objects = dir_objects / objects_name
    path_data    = dir_data    / data_name

    # --- Step 1: Segment pillars and save 3D objects ---
    imp_pillar = IJ.openImage(str(path_pillar))
    if imp_pillar is None:
        raise FileNotFoundError(f"Could not open: {path_pillar}")
    imp_pillar.show()

    manager3d.segment(128, 255)       # Ext.Manager3D_Segment(128, 255)
    manager3d.addImage()              # Ext.Manager3D_AddImage()
    manager3d.save(str(path_objects)) # Ext.Manager3D_Save(pathobjects)

    # --- Step 2: Open myelin overlap mask and measure volume ---
    imp_myelin = IJ.openImage(str(path_myelin))
    if imp_myelin is None:
        raise FileNotFoundError(f"Could not open: {path_myelin}")
    imp_myelin.show()

    manager3d.selectAll()                          # Ext.Manager3D_SelectAll()
    manager3d.list()                               # Ext.Manager3D_List()
    manager3d.saveResult("V", str(path_data))      # Ext.Manager3D_SaveResult("V", pathdata)

    # --- Step 3: Convert CSV → TSV (replicate the inline IJM conversion) ---
    #   The macro writes a "V_<filename>" CSV next to pathdata;
    #   we read it, swap commas for tabs, and write a "_converted.txt" file.
    csv_path = dir_data / f"V_{data_name}"
    txt_path = dir_data / f"V_{data_name.replace('.txt', '_converted.txt')}"

    if csv_path.exists():
        csv_text = csv_path.read_text(encoding="utf-8")
        txt_text = csv_text.replace(",", "\t")
        txt_path.write_text(txt_text, encoding="utf-8")
        print(f"    [process_field_3d] converted {csv_path.name} → {txt_path.name}")
    else:
        print(f"    [process_field_3d] WARNING: expected CSV not found: {csv_path}")

    # --- Step 4: Clean up ---
    manager3d.closeResult("V")  # Ext.Manager3D_CloseResult("V")
    manager3d.delete()          # Ext.Manager3D_Delete()

    IJ.run("Close All")
    IJ.run("Collect Garbage")

    print(f"    [process_field_3d] done: {field_dir.name}")


def get_manager3d():
    """
    Initialise the 3D Manager plugin and return a thin wrapper that exposes
    the Ext.Manager3D_* macro functions as regular Python method calls.
    """
    # Run the plugin once so it registers itself as the active 3D manager
    IJ.run("3D Manager")

    # The 3D Manager exposes its API through the ImageJ macro extension
    # mechanism.  In pyimagej we drive it via run_macro, mirroring the
    # original IJM Ext.* calls exactly.
    class Manager3D:
        @staticmethod
        def _ext(call: str):
            ij.py.run_macro(f'Ext.Manager3D_{call};')

        def segment(self, low: int, high: int):
            self._ext(f"Segment({low},{high})")

        def addImage(self):
            self._ext("AddImage()")

        def save(self, path: str):
            # Paths passed to macro extensions need forward-slash separators
            safe = path.replace("\\", "/")
            self._ext(f'Save("{safe}")')

        def selectAll(self):
            self._ext("SelectAll()")

        def list(self):
            self._ext("List()")

        def saveResult(self, result_type: str, path: str):
            safe = path.replace("\\", "/")
            self._ext(f'SaveResult("{result_type}", "{safe}")')

        def closeResult(self, result_type: str):
            self._ext(f'CloseResult("{result_type}")')

        def delete(self):
            self._ext("Delete()")

        def close(self):
            self._ext("Close()")

    return Manager3D()


def main():
    manager3d = get_manager3d()

    for k in WELL_RANGE:
        well_name = f"E{k}"
        well_path = BASE_PATH / well_name
        print(f"\nProcessing well: {well_name}  ({well_path})")

        try:
            field_dirs = get_field_dirs(well_path)
        except FileNotFoundError:
            print(f"  Well directory not found, skipping: {well_path}")
            continue

        # The original macro iterates i=0..8 (first 9 subdirs)
        field_dirs = field_dirs[:9]
        print(f"  Found {len(field_dirs)} field(s) (capped at 9)")

        for field_dir in field_dirs:
            print(field_dir.name)
            try:
                process_field_3d(field_dir, manager3d)
            except Exception as exc:
                print(f"  ✗ {field_dir.name}: {exc}")

    manager3d.close()  # Ext.Manager3D_Close()
    print("Done.")


if __name__ == "__main__":
    main()
    ij.dispose()