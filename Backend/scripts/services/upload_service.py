# Step 1 Service file to execute rename_organize_keyence.sh.

import subprocess

from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "rename_organize_keyence.sh"
)


def _payload_dict(payload):
    if hasattr(payload, "model_dump"):
        return payload.model_dump()

    return dict(payload)


def build_script_args(payload):
    data = _payload_dict(payload)
    active_channels = [
        channel for channel in data.get("channels", [])
        if channel.get("active", True)
    ]

    channel_codes = "|".join(
        channel.get("code", "") for channel in active_channels
    )
    channel_labels = "|".join(
        channel.get("label", "") for channel in active_channels
    )
    disabled_fovs = ",".join(
        str(fov) for fov in data.get("disabled_fovs", [])
    )

    return [
        data.get("tracks", [""])[0] if data.get("tracks") else "",
        data.get("tracks1", [""])[0] if data.get("tracks1") else "",
        data.get("ordered_track", [""])[0] if data.get("ordered_track") else "",
        data.get("data", [""])[0] if data.get("data") else "",
        data.get("image_type", "3D"),
        data.get("microscope", "Keyence"),
        str(data.get("num_fovs", 0)),
        disabled_fovs,
        channel_codes,
        channel_labels,
    ]


def run_processing(payload):
    result = subprocess.run(
        [
            r"C:\Program Files\Git\bin\bash.exe",
            str(SCRIPT_PATH),
            *build_script_args(payload),
        ],
        capture_output=True,
        text=True
    )

    return result.stdout
