import csv
from pathlib import Path


FINAL_COLUMNS = [
    "well", "fov", "particle", "Area", "Mean", "Min", "Max", "Circ",
    "IntDen", "RawIntDen", "AR", "Round", "Solidity", "Volume",
]


def find_particle_file(field_dir):
    matches = sorted((field_dir / "DATA").glob("Total-MBP-2D-*.out"))
    return matches[0] if matches else None


def parse_result_file(path):
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        lines = [line.strip() for line in handle if line.strip()]
    if len(lines) < 2:
        return []
    rows = []
    for line in lines[1:]:
        values = line.replace("\t", " ").split()
        if values:
            rows.append(values)
    return rows




def load_volumes(field_dir):
    matches = sorted((field_dir / "DATA").glob("V_Data-*_converted.txt"))
    if not matches:
        return {}
    volumes = {}
    with matches[0].open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line in list(handle)[1:]:
            values = line.replace("\t", " ").split()
            if len(values) >= 2:
                volumes[values[0]] = values[1]
    return volumes

def consolidate_results(base_path, output_path):
    base_path = Path(base_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(FINAL_COLUMNS)
        for well_path in sorted(path for path in base_path.iterdir() if path.is_dir()):
            for field_path in sorted(path for path in well_path.iterdir() if path.is_dir()):
                result_file = find_particle_file(field_path)
                if result_file is None:
                    continue
                volumes = load_volumes(field_path)
                for values in parse_result_file(result_file):
                    particle = values[0]
                    measurements = values[1:]
                    row = [well_path.name, field_path.name, particle, *measurements, volumes.get(particle, "")]
                    writer.writerow(row[:len(FINAL_COLUMNS)])
                    written += 1
    return output_path, written