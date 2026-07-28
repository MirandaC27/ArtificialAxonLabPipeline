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


masking_data = {
    "base_path": "",
    "well_start": 2,
    "well_end": 11,
    "thresholds": {"axon": None, "myelin": 8000, "nuclei": None, "debris": 15000, "GFAP": None},
    "auto_thresholds": {"axon": False, "myelin": False, "nuclei": False, "debris": False, "GFAP": False},
    "particle_size": {"min": 2, "max": 2000},
}

history_state = {
    "saved": False,
    "history_id": None
}


def reset_history_state():
    history_state["saved"] = False
    history_state["history_id"] = None

def reset_all_state():
    upload_data.clear()
    upload_data.update({
        "folders": [],
        "tracks": [],
        "tracks1": [],
        "ordered_track": [],
        "data": [],
        "image_type": "3D",
        "microscope": "Keyence",
        "num_fovs": 0,
        "disabled_fovs": [],
        "channels": [],
    })

    settings_data.clear()
    settings_data.update({
        "experiment": "",
        "frames": 0,
        "distance": "",
        "run_ezra": False,
    })

    masking_data.clear()
    masking_data.update({
        "base_path": "",
        "well_start": 2,
        "well_end": 11,
        "thresholds": {
            "axon": None,
            "myelin": 8000,
            "nuclei": None,
            "debris": 15000,
            "GFAP": None,
        },
        "auto_thresholds": {
            "axon": False,
            "myelin": False,
            "nuclei": False,
            "debris": False,
            "GFAP": False,
        },
        "particle_size": {"min": 2, "max": 2000},
    })

    reset_history_state()