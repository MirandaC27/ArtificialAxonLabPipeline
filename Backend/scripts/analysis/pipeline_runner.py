import argparse
import base64
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import json
import os
import subprocess
import sys
import threading
from pathlib import Path, PureWindowsPath

import requests

try:
    from .reporting import build_report_artifacts
except ImportError:
    from reporting import build_report_artifacts


ANALYSIS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ANALYSIS_DIR.parents[1]
DATA_DIR = BACKEND_DIR / "data"

CHANNEL_ALIASES = {
    "axon": "axon", "axons": "axon", "pillar": "axon", "pillars": "axon",
    "myelin": "myelin", "mbp": "myelin",
    "nuclei": "nuclei", "nucleus": "nuclei", "dapi": "nuclei",
    "debris": "debris", "gfap": "gfap",
}


def normalize_channel_label(value):
    label = str(value or "").strip().lower()
    return CHANNEL_ALIASES.get(label, label)


def positive_float(value, default=1.0):
    try:
        number = float(str(value).strip().split()[0])
    except (TypeError, ValueError, IndexError):
        return default
    return number if number > 0 else default


def positive_int(value, default=9):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 1 else default


def to_container_data_path(value):
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("No ordered-data base path is configured.")
    container_root = Path(os.getenv("AXONLAB_CONTAINER_DATA_ROOT", "/data"))
    if raw.replace("\\", "/").startswith(f"{container_root.as_posix()}/"):
        return Path(raw)
    host_root = os.getenv("AXONLAB_HOST_DATA_ROOT", "").strip()
    if not host_root:
        raise ValueError("AXONLAB_HOST_DATA_ROOT is not configured in Docker.")
    try:
        relative = PureWindowsPath(raw).relative_to(PureWindowsPath(host_root))
    except ValueError as exc:
        raise ValueError(
            f"The selected data path {raw!r} is outside the mounted data root {host_root!r}."
        ) from exc
    return container_root.joinpath(*relative.parts)


def normalized_payload(payload):
    upload = payload.get("upload_data") or {}
    analysis_settings = payload.get("settings_data") or {}
    masking = payload.get("masking_data") or {}
    raw_base_path = masking.get("base_path")
    if not raw_base_path:
        ordered = upload.get("ordered_track") or []
        raw_base_path = ordered[0] if ordered else ""
    base_path = to_container_data_path(raw_base_path)
    well_start = int(masking.get("well_start", 2))
    well_end = int(masking.get("well_end", 11))
    thresholds = dict(masking.get("thresholds") or {})
    for channel, enabled in (masking.get("auto_thresholds") or {}).items():
        if enabled:
            thresholds[channel] = "auto"
    channels = upload.get("channels") or []
    active_channels = [
        normalize_channel_label(channel.get("label"))
        for channel in channels
        if isinstance(channel, dict)
        and channel.get("label")
        and not channel.get("disabled", False)
        and channel.get("active", True)
    ]
    if not channels:
        active_channels = ["axon", "myelin", "nuclei", "debris"]
    channel_numbers = {
        normalize_channel_label(channel.get("label")): int(channel.get("num", 1))
        for channel in channels
        if isinstance(channel, dict)
        and channel.get("label")
        and str(channel.get("num", "")).isdigit()
    }
    image_type = str(upload.get("image_type") or "3D").strip().upper()
    masking_settings = {
        **masking,
        "thresholds": thresholds,
        "base_path": str(base_path),
        "well_range": list(range(well_start, well_end + 1)),
        "image_type": image_type,
        "active_channels": active_channels,
        "channel_numbers": channel_numbers,
        "z_step_um": positive_float(analysis_settings.get("distance")),
        "z_slice_count": positive_int(analysis_settings.get("frames")),
    }
    upload_settings = {
        "OrderedTrack": [str(base_path)],
        "DisabledFOVs": upload.get("disabled_fovs") or [],
        "Channels": channels,
        "ImageType": image_type,
        "SkipChannels": [
            channel.get("label", "")
            for channel in channels
            if isinstance(channel, dict)
            and (channel.get("disabled", False) or not channel.get("active", True))
        ],
    }
    return base_path, masking_settings, upload_settings


def run_stage(script_name, env, args=None, line_callback=None):
    command = [sys.executable, str(ANALYSIS_DIR / script_name), *(args or [])]
    process = subprocess.Popen(
        command,
        cwd=str(ANALYSIS_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    output = deque(maxlen=250)
    for line in process.stdout:
        output.append(line.rstrip())
        if line_callback:
            line_callback(line.rstrip())
    return_code = process.wait()
    if return_code != 0:
        details = "\n".join(output).strip()
        raise RuntimeError(f"{script_name} failed: {details}")
    return "\n".join(output)


def run_parallel_stage(script_name, wells, env, progress_callback, start_percent, end_percent, label):
    worker_count = max(1, min(int(os.getenv("ANALYSIS_WORKERS", "2")), len(wells)))
    groups = [wells[index::worker_count] for index in range(worker_count)]
    completed = 0
    lock = threading.Lock()

    def report_line(line):
        nonlocal completed
        if not line.startswith("AXONLAB_PROGRESS::"):
            return
        well_name = line.split("::", 1)[1]
        with lock:
            completed += 1
            fraction = completed / len(wells)
            percent = start_percent + round((end_percent - start_percent) * fraction)
        progress_callback(percent, f"{label}: {well_name} ({completed}/{len(wells)} wells)")

    def run_group(worker_index, group):
        worker_env = env.copy()
        # JGO's environment builder is not concurrency-safe. Give every Fiji
        # worker a stable environment cache while retaining the shared Maven
        # repository for already-downloaded artifacts.
        worker_cache_root = Path(
            os.getenv("ANALYSIS_JGO_CACHE_ROOT", "/root/.cache/axonlab-jgo")
        )
        worker_env["JGO_CACHE_DIR"] = str(worker_cache_root / f"worker-{worker_index}")
        run_stage(
            script_name,
            worker_env,
            ["--wells", ",".join(str(well) for well in group)],
            report_line,
        )

    progress_callback(start_percent, f"{label}: starting {worker_count} Docker workers")
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [
            executor.submit(run_group, worker_index, group)
            for worker_index, group in enumerate(groups)
            if group
        ]
        for future in futures:
            future.result()


def build_analysis_artifacts(payload, job_id, progress_callback=None):
    progress_callback = progress_callback or (lambda percent, message: None)
    base_path, masking_settings, upload_settings = normalized_payload(payload)
    if not base_path.exists():
        raise FileNotFoundError(
            f"Mounted ordered-data directory does not exist: {base_path}. Check AXONLAB_DATA_ROOT."
        )
    fiji_path = Path(os.getenv("FIJI_PATH", "/opt/fiji"))
    if not fiji_path.exists():
        raise FileNotFoundError(
            f"Docker Fiji directory does not exist: {fiji_path}."
        )
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "masking_settings.json").write_text(json.dumps(masking_settings, indent=2), encoding="utf-8")
    (DATA_DIR / "upload_settings.json").write_text(json.dumps(upload_settings, indent=2), encoding="utf-8")
    env = os.environ.copy()
    env["ORDERED_TRACK"] = str(base_path)
    wells = [int(well) for well in masking_settings["well_range"]]
    if not wells:
        raise ValueError("No wells were selected for analysis.")
    image_type = masking_settings["image_type"]
    active_channels = set(masking_settings["active_channels"])
    run_parallel_stage("masking.py", wells, env, progress_callback, 5, 60, f"Creating {image_type} masks")
    if image_type == "3D":
        missing = {"axon", "myelin"} - active_channels
        if missing:
            raise ValueError(
                "3D wrapping analysis requires active axon and myelin channels. "
                f"Missing: {', '.join(sorted(missing))}."
            )
        run_parallel_stage("create_data.py", wells, env, progress_callback, 60, 92, "Measuring 3D wrapping")
    else:
        progress_callback(92, "2D analysis selected; skipping 3D object measurements")
    progress_callback(94, "Building FOV and well summaries")
    artifacts, row_count = build_report_artifacts(
        base_path, masking_settings, job_id
    )
    progress_callback(99, f"Saving {len(artifacts)} artifacts to PostgreSQL")
    return artifacts, row_count


def build_final_csv(payload, progress_callback=None):
    """Backward-compatible helper returning the primary FOV CSV."""
    artifacts, row_count = build_analysis_artifacts(
        payload, "manual", progress_callback
    )
    primary = next(
        artifact for artifact in artifacts
        if artifact["artifact_type"] == "fov_summary"
    )
    return primary["content"], row_count


def upload_final_csv(api_url, content):
    endpoint = f"{api_url.rstrip('/')}/results"
    payload = {
        "filename": "final_results.csv",
        "content_base64": base64.b64encode(content).decode("ascii"),
        "overwrite": True,
    }
    response = requests.post(endpoint, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def run_pipeline(payload, api_url):
    artifacts, row_count = build_analysis_artifacts(payload, "manual")
    records = []
    for artifact in artifacts:
        endpoint = f"{api_url.rstrip('/')}/results"
        response = requests.post(
            endpoint,
            json={
                "filename": artifact["filename"],
                "content_base64": base64.b64encode(artifact["content"]).decode("ascii"),
                "mime_type": artifact["mime_type"],
                "artifact_type": artifact["artifact_type"],
                "overwrite": True,
            },
            timeout=60,
        )
        response.raise_for_status()
        records.append(response.json())
    return {"records": records, "row_count": row_count}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--api-url", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    print(json.dumps(run_pipeline(payload, args.api_url)))


if __name__ == "__main__":
    main()
