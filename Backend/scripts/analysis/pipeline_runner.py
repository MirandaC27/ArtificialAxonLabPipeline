import argparse
import base64
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import json
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path, PureWindowsPath

import requests

try:
    from .consolidate_results import consolidate_results
except ImportError:
    from consolidate_results import consolidate_results


ANALYSIS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ANALYSIS_DIR.parents[1]
DATA_DIR = BACKEND_DIR / "data"


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
    masking_settings = {
        **masking,
        "thresholds": thresholds,
        "base_path": str(base_path),
        "well_range": list(range(well_start, well_end + 1)),
    }
    upload_settings = {
        "OrderedTrack": [str(base_path)],
        "DisabledFOVs": upload.get("disabled_fovs") or [],
        "Channels": upload.get("channels") or [],
        "SkipChannels": [
            channel.get("label", "")
            for channel in upload.get("channels") or []
            if isinstance(channel, dict) and not channel.get("active", True)
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


def build_final_csv(payload, progress_callback=None):
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
    run_parallel_stage("masking.py", wells, env, progress_callback, 5, 55, "Creating masks")
    run_parallel_stage("create_data.py", wells, env, progress_callback, 55, 92, "Measuring objects")
    progress_callback(95, "Consolidating CSV results")
    with tempfile.TemporaryDirectory(prefix="axonlab-results-") as temp_dir:
        final_path, row_count = consolidate_results(base_path, Path(temp_dir) / "final_results.csv")
        if row_count == 0:
            raise RuntimeError("Analysis produced no particle rows. Check channel selection and masking thresholds.")
        content = final_path.read_bytes()
    progress_callback(99, f"Saving {row_count} rows to PostgreSQL")
    return content, row_count


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
    content, row_count = build_final_csv(payload)
    record = upload_final_csv(api_url, content)
    return {"record": record, "row_count": row_count}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--api-url", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    print(json.dumps(run_pipeline(payload, args.api_url)))


if __name__ == "__main__":
    main()
