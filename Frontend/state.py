upload_data = {
    "folders": [],
    "tracks": [],
    "tracks1": [],
    "ordered_track": [],
    "data": [],

    "image_type": "3D",
    "microscope": "Keyence",
    "num_fovs": 0,

    "disabled_fovs": [],
    "channels": []
}


settings_data = {
    "experiment": "",
    "frames": 0,
    "distance": "",
    "run_ezra": False
}


history_state = {
    "saved": False,
    "history_id": None
}


def reset_history_state():
    history_state["saved"] = False
    history_state["history_id"] = None