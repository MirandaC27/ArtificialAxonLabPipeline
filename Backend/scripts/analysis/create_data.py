"""3D pillar segmentation and per-object, per-Z myelin wrapping measurements."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy import ndimage
import tifffile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "data" / "upload_settings.json"
MASKING_SETTINGS_PATH = PROJECT_ROOT / "data" / "masking_settings.json"


def load_skip_config():
    if not CONFIG_PATH.exists():
        return {"skip_fovs": set(), "skip_fovs_per_well": {}}
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    raw_global = list(data.get("DisabledFOVs", [])) + list(data.get("SkipFOVs", []))
    per_well = {
        str(well): {
            int(value) for value in values if str(value).strip().isdigit()
        }
        for well, values in (data.get("SkipFOVsPerWell") or {}).items()
    }
    return {
        "skip_fovs": {
            int(value) for value in raw_global if str(value).strip().isdigit()
        },
        "skip_fovs_per_well": per_well,
    }


def parse_fov_num(field_name):
    parts = field_name.split("_")
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return int(parts[1])


def should_skip_field(well_name, field_name, skip_config):
    number = parse_fov_num(field_name)
    if number is None:
        return False
    return (
        number in skip_config["skip_fovs"]
        or number in skip_config["skip_fovs_per_well"].get(well_name, set())
    )


def read_mask_stack(path):
    data = np.asarray(tifffile.imread(path))
    data = np.squeeze(data)
    if data.ndim < 2:
        raise ValueError(f"Mask has no image plane: {path}")
    if data.ndim == 2:
        data = data[np.newaxis, ...]
    elif data.ndim > 3:
        data = data.reshape((-1, data.shape[-2], data.shape[-1]))
    return data > 0


def aligned_stacks(pillar_path, myelin_path, fallback_depth=9):
    pillars = read_mask_stack(pillar_path)
    myelin = read_mask_stack(myelin_path)
    shape = tuple(min(left, right) for left, right in zip(pillars.shape, myelin.shape))
    slices = tuple(slice(0, length) for length in shape)
    pillars = pillars[slices]
    myelin = myelin[slices]
    synthetic_z = pillars.shape[0] == 1
    if synthetic_z:
        depth = max(2, int(fallback_depth or 9))
        pillars = np.repeat(pillars, depth, axis=0)
        myelin = np.repeat(myelin, depth, axis=0)
    return pillars, myelin, synthetic_z


def wrapping_category(fraction):
    if fraction > 0.8:
        return 100
    if fraction > 0.5:
        return 80
    if fraction > 0.2:
        return 50
    return 20


def measure_objects(pillars, myelin, minimum_voxels=1, synthetic_z=False):
    labels, object_count = ndimage.label(
        pillars,
        structure=np.ones((3, 3, 3), dtype=np.uint8),
    )
    details = []
    objects = []
    kept_label = 0
    for source_label in range(1, object_count + 1):
        object_mask = labels == source_label
        voxel_count = int(object_mask.sum())
        if voxel_count < minimum_voxels:
            labels[object_mask] = 0
            continue
        kept_label += 1
        labels[object_mask] = kept_label
        z_indices = np.flatnonzero(object_mask.any(axis=(1, 2)))
        wrapped_voxels = 0
        fractions = []
        categories = []
        for z_index in z_indices:
            plane = object_mask[z_index]
            axon_pixels = int(plane.sum())
            myelin_pixels = int(np.count_nonzero(myelin[z_index] & plane))
            fraction = myelin_pixels / axon_pixels if axon_pixels else 0.0
            category = wrapping_category(fraction)
            details.append({
                "Label": kept_label,
                "Z": int(z_index),
                "axon_pixels": axon_pixels,
                "myelin_pixels": myelin_pixels,
                "fraction_wrapped": fraction,
                "category": category,
                "synthetic_z": synthetic_z,
            })
            wrapped_voxels += myelin_pixels
            fractions.append(fraction)
            categories.append(category)
        objects.append({
            "Object": kept_label,
            "Volume": voxel_count,
            "wrapped_voxels": wrapped_voxels,
            "z_start": int(z_indices.min()) if len(z_indices) else 0,
            "z_end": int(z_indices.max()) if len(z_indices) else 0,
            "z_slices": int(len(z_indices)),
            "mean_fraction_wrapped": float(np.mean(fractions)) if fractions else 0.0,
            "max_fraction_wrapped": float(max(fractions)) if fractions else 0.0,
            "max_category": int(max(categories)) if categories else 20,
            "synthetic_z": synthetic_z,
        })
    return labels, details, objects


def write_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def process_field(field_dir, settings):
    masks_dir = field_dir / "MASKS"
    data_dir = field_dir / "DATA"
    objects_dir = field_dir / "OBJECTS"
    data_dir.mkdir(parents=True, exist_ok=True)
    objects_dir.mkdir(parents=True, exist_ok=True)

    pillar_path = masks_dir / "mask-pillars-rim.tif"
    overlap_matches = sorted(masks_dir.glob("mask-myelin-overlap-*.tif"))
    if not pillar_path.exists():
        raise FileNotFoundError(f"Missing 3D pillar-rim mask: {pillar_path}")
    if not overlap_matches:
        raise FileNotFoundError(f"Missing 3D myelin-overlap mask in {masks_dir}")

    pillars, myelin, synthetic_z = aligned_stacks(
        pillar_path,
        overlap_matches[0],
        fallback_depth=settings.get("z_slice_count", 9),
    )
    minimum_voxels = max(
        1, int((settings.get("particle_size") or {}).get("min") or 1)
    )
    labels, details, objects = measure_objects(
        pillars,
        myelin,
        minimum_voxels=minimum_voxels,
        synthetic_z=synthetic_z,
    )
    if not objects:
        raise RuntimeError(f"No 3D pillar objects were detected in {field_dir}")

    threshold = (settings.get("thresholds") or {}).get("myelin") or 8000
    write_csv(
        data_dir / f"Wrapping_Data-{threshold}.csv",
        details,
        [
            "Label", "Z", "axon_pixels", "myelin_pixels",
            "fraction_wrapped", "category", "synthetic_z",
        ],
    )
    write_csv(
        data_dir / f"Object_Summary-{threshold}.csv",
        objects,
        [
            "Object",
            "Volume",
            "wrapped_voxels",
            "z_start",
            "z_end",
            "z_slices",
            "mean_fraction_wrapped",
            "max_fraction_wrapped",
            "max_category",
            "synthetic_z",
        ],
    )
    with (data_dir / f"V_Data-{threshold}_converted.txt").open(
        "w", encoding="utf-8"
    ) as handle:
        handle.write("Object\tVolume\n")
        for row in objects:
            handle.write(f"{row['Object']}\t{row['Volume']}\n")
    np.savez_compressed(
        objects_dir / f"Objects{threshold}.npz",
        labels=labels.astype(np.int32),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wells", help="Comma-separated well numbers assigned to this worker")
    args = parser.parse_args()
    settings = json.loads(MASKING_SETTINGS_PATH.read_text(encoding="utf-8"))
    base_path = Path(settings["base_path"])
    wells = settings["well_range"]
    if args.wells:
        wells = [int(value) for value in args.wells.split(",") if value.strip()]
    skip_config = load_skip_config()
    failures = []
    for well_number in wells:
        well_name = f"B{int(well_number):02d}"
        well_path = base_path / well_name
        if not well_path.exists():
            print(f"Well directory not found, skipping: {well_path}")
            print(f"AXONLAB_PROGRESS::{well_name}", flush=True)
            continue
        for field_dir in sorted(path for path in well_path.iterdir() if path.is_dir()):
            if should_skip_field(well_name, field_dir.name, skip_config):
                continue
            try:
                process_field(field_dir, settings)
            except Exception as exc:
                failures.append(f"{well_name}/{field_dir.name}: {exc}")
        print(f"AXONLAB_PROGRESS::{well_name}", flush=True)
    if failures:
        raise RuntimeError("3D measurement failed for " + "; ".join(failures))


if __name__ == "__main__":
    main()
