import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

from consolidate_results import consolidate_results


ANALYSIS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ANALYSIS_DIR.parents[1]
DATA_DIR = BACKEND_DIR / "data"


def normalized_payload(payload):
    upload = payload.get("upload_data") or {}
    masking = payload.get("masking_data") or {}
    base_path = masking.get("base_path")
    if not base_path:
        ordered = upload.get("ordered_track") or []
        base_path = ordered[0] if ordered else ""
    if not base_path:
        raise ValueError("No ordered-data base path is configured.")
    well_start = int(masking.get("well_start", 2))
    well_end = int(masking.get("well_end", 11))
    thresholds = dict(masking.get("thresholds") or {})
    for channel, enabled in (masking.get("auto_thresholds") or {}).items():
        if enabled:
            thresholds[channel] = "auto"
    masking_settings = {
        **masking,
        "thresholds": thresholds,
        "base_path": base_path,
        "well_range": list(range(well_start, well_end + 1)),
    }
    upload_settings = {
        "OrderedTrack": upload.get("ordered_track") or [base_path],
        "DisabledFOVs": upload.get("disabled_fovs") or [],
        "Channels": upload.get("channels") or [],
        "SkipChannels": [
            channel.get("label", "")
            for channel in upload.get("channels") or []
            if isinstance(channel, dict) and not channel.get("active", True)
        ],
    }
    return Path(base_path), masking_settings, upload_settings


def run_stage(script_name, env):
    result = subprocess.run(
        [sys.executable, str(ANALYSIS_DIR / script_name)],
        cwd=str(ANALYSIS_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"{script_name} failed: {details}")
    return result.stdout


def upload_final_csv(api_url, csv_path):
    encoded = base64.b64encode(csv_path.read_bytes()).decode("ascii")
    endpoint = f"{api_url.rstrip('/')}/results"
    payload = {"filename": csv_path.name, "content_base64": encoded, "overwrite": True}
    response = requests.post(endpoint, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def run_pipeline(payload, api_url):
    base_path, masking_settings, upload_settings = normalized_payload(payload)
    if not base_path.exists():
        raise FileNotFoundError(f"Ordered-data directory does not exist: {base_path}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "masking_settings.json").write_text(json.dumps(masking_settings, indent=2), encoding="utf-8")
    (DATA_DIR / "upload_settings.json").write_text(json.dumps(upload_settings, indent=2), encoding="utf-8")
    env = os.environ.copy()
    run_stage("masking.py", env)
    run_stage("create_data.py", env)
    with tempfile.TemporaryDirectory(prefix="axonlab-results-") as temp_dir:
        final_path = Path(temp_dir) / "final_results.csv"
        final_path, row_count = consolidate_results(base_path, final_path)
        record = upload_final_csv(api_url, final_path)
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