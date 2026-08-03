"""Build FOV/well summaries and portable analysis artifacts."""

import io
from pathlib import Path

import pandas as pd


def read_imagej_table(path):
    if path is None or not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, sep=r"\s+", engine="python")
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError):
        return pd.DataFrame()


def first_match(directory, pattern):
    matches = sorted(directory.glob(pattern))
    return matches[0] if matches else None


def table_metrics(table, prefix):
    if table.empty:
        return {
            f"{prefix}_count": 0,
            f"{prefix}_area": 0.0,
            f"{prefix}_mean_intensity": 0.0,
        }
    area_column = next((name for name in ("Area", "Total Area") if name in table), None)
    mean_column = next((name for name in ("Mean", "Mean intensity") if name in table), None)
    return {
        f"{prefix}_count": int(len(table)),
        f"{prefix}_area": float(table[area_column].fillna(0).sum()) if area_column else 0.0,
        f"{prefix}_mean_intensity": float(table[mean_column].fillna(0).mean()) if mean_column else 0.0,
    }


def longest_consecutive(z_values):
    longest = current = 0
    previous = None
    for value in sorted(set(int(item) for item in z_values)):
        current = current + 1 if previous is not None and value == previous + 1 else 1
        longest = max(longest, current)
        previous = value
    return longest


def wrapping_metrics(path, z_step_um):
    empty = {
        "total_pillars": 0,
        "wrap_any_pillars": 0,
        "wrap_50_pillars": 0,
        "wrap_80_pillars": 0,
        "wrap_80_pillars_three_slices": 0,
        "wrap_80_pillars_five_slices": 0,
        "wrap_any_myelin_pixels": 0,
        "wrap_50_myelin_pixels": 0,
        "wrap_80_myelin_pixels": 0,
        "average_full_wrapping_length_um": 0.0,
    }
    if path is None or not path.exists():
        return empty
    table = pd.read_csv(path)
    if table.empty:
        return empty
    grouped = table.groupby("Label")
    any_labels = set(table.loc[table["fraction_wrapped"] > 0, "Label"])
    labels_50 = set(table.loc[table["fraction_wrapped"] > 0.5, "Label"])
    labels_80 = set(table.loc[table["fraction_wrapped"] > 0.8, "Label"])
    runs = []
    for label in labels_80:
        rows = grouped.get_group(label)
        run = longest_consecutive(rows.loc[rows["fraction_wrapped"] > 0.8, "Z"])
        runs.append(run)
    return {
        "total_pillars": int(table["Label"].nunique()),
        "wrap_any_pillars": len(any_labels),
        "wrap_50_pillars": len(labels_50),
        "wrap_80_pillars": len(labels_80),
        "wrap_80_pillars_three_slices": sum(run >= 3 for run in runs),
        "wrap_80_pillars_five_slices": sum(run >= 5 for run in runs),
        "wrap_any_myelin_pixels": int(
            table.loc[table["fraction_wrapped"] > 0, "myelin_pixels"].sum()
        ),
        "wrap_50_myelin_pixels": int(
            table.loc[table["fraction_wrapped"] > 0.5, "myelin_pixels"].sum()
        ),
        "wrap_80_myelin_pixels": int(
            table.loc[table["fraction_wrapped"] > 0.8, "myelin_pixels"].sum()
        ),
        "average_full_wrapping_length_um": (
            float(pd.Series(runs).mean() * z_step_um) if runs else 0.0
        ),
    }


def nuclei_count(data_dir):
    table = read_imagej_table(data_dir / "nuclei.out")
    if table.empty:
        return 0
    if "Count" in table:
        return int(table["Count"].fillna(0).sum())
    return int(len(table))


def build_fov_summary(base_path, settings):
    rows = []
    selected = {f"B{int(number):02d}" for number in settings["well_range"]}
    z_step_um = float(settings.get("z_step_um") or 1.0)
    for well_dir in sorted(path for path in Path(base_path).iterdir() if path.is_dir()):
        if selected and well_dir.name not in selected:
            continue
        for field_dir in sorted(path for path in well_dir.iterdir() if path.is_dir()):
            data_dir = field_dir / "DATA"
            if not data_dir.exists():
                continue
            output_patterns = (
                "nuclei.out", "Total-MBP-2D-*.out", "Total-2D-debris-*.out",
                "Total-2D-GFAP-*.out", "Total-2D-axons.out", "Wrapping_Data-*.csv",
            )
            has_output = any(first_match(data_dir, pattern) for pattern in output_patterns)
            if not has_output:
                continue
            row = {
                "well": well_dir.name,
                "fov": field_dir.name,
                "image_type": settings.get("image_type", "3D"),
                "nuclei_count": nuclei_count(data_dir),
            }
            row.update(table_metrics(
                read_imagej_table(first_match(data_dir, "Total-MBP-2D-*.out")),
                "myelin",
            ))
            row.update(table_metrics(
                read_imagej_table(first_match(data_dir, "Total-2D-debris-*.out")),
                "debris",
            ))
            row.update(table_metrics(
                read_imagej_table(first_match(data_dir, "Total-2D-GFAP-*.out")),
                "gfap",
            ))
            row.update(table_metrics(
                read_imagej_table(data_dir / "Total-2D-axons.out"),
                "axon",
            ))
            wrapping_path = first_match(data_dir, "Wrapping_Data-*.csv")
            row.update(wrapping_metrics(wrapping_path, z_step_um))
            rows.append(row)
    return pd.DataFrame(rows)


def build_wrapping_details(base_path, settings):
    frames = []
    selected = {f"B{int(number):02d}" for number in settings["well_range"]}
    for path in sorted(Path(base_path).glob("*/**/DATA/Wrapping_Data-*.csv")):
        well = path.parents[2].name
        if selected and well not in selected:
            continue
        try:
            table = pd.read_csv(path)
        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError):
            continue
        if table.empty:
            continue
        table.insert(0, "fov", path.parents[1].name)
        table.insert(0, "well", well)
        frames.append(table)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_well_summary(fov_table):
    if fov_table.empty:
        return pd.DataFrame()
    numeric = list(fov_table.select_dtypes(include="number").columns)
    mean_columns = {
        name for name in numeric
        if "mean_" in name or name.startswith("average_")
    }
    aggregations = {
        name: ("mean" if name in mean_columns else "sum")
        for name in numeric
    }
    result = fov_table.groupby("well", as_index=False).agg(aggregations)
    result.insert(1, "fov_count", fov_table.groupby("well").size().values)
    metadata_columns = [name for name in ("image_type",) if name in fov_table]
    metadata = fov_table.groupby("well", as_index=False)[metadata_columns].first()
    result = metadata.merge(result, on="well", how="left")
    return result


def dataframe_csv_bytes(table):
    return table.to_csv(index=False).encode("utf-8")


def excel_bytes(fov_table, well_table, wrapping_table=None):
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            fov_table.to_excel(writer, index=False, sheet_name="FOV Summary")
            well_table.to_excel(writer, index=False, sheet_name="Well Summary")
            if wrapping_table is not None and not wrapping_table.empty:
                wrapping_table.to_excel(
                    writer, index=False, sheet_name="Wrapping Details"
                )
    except ImportError:
        return None
    return output.getvalue()


def build_report_artifacts(base_path, settings, job_id):
    fov_table = build_fov_summary(base_path, settings)
    if fov_table.empty:
        raise RuntimeError(
            "Analysis produced no FOV measurements. Check active channels and thresholds."
        )
    well_table = build_well_summary(fov_table)
    wrapping_table = build_wrapping_details(base_path, settings)
    prefix = f"analysis_job_{job_id}"
    artifacts = [
        {
            "filename": f"{prefix}_fov_summary.csv",
            "artifact_type": "fov_summary",
            "mime_type": "text/csv",
            "content": dataframe_csv_bytes(fov_table),
        },
        {
            "filename": f"{prefix}_well_summary.csv",
            "artifact_type": "well_summary",
            "mime_type": "text/csv",
            "content": dataframe_csv_bytes(well_table),
        },
    ]
    if not wrapping_table.empty:
        artifacts.append({
            "filename": f"{prefix}_wrapping_per_object_per_z.csv",
            "artifact_type": "wrapping_details",
            "mime_type": "text/csv",
            "content": dataframe_csv_bytes(wrapping_table),
        })
    workbook = (
        excel_bytes(fov_table, well_table, wrapping_table)
        if settings.get("export_excel", True) else None
    )
    if workbook:
        artifacts.append({
            "filename": f"{prefix}_summaries.xlsx",
            "artifact_type": "excel",
            "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "content": workbook,
        })
    return artifacts, int(len(fov_table))
