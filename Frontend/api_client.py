import os
import requests

BASE_URL = os.getenv("AXONLAB_API_URL", "http://localhost:8000").rstrip("/")

def add_numbers(a, b):
    response = requests.post(
        f"{BASE_URL}/add",
        json={"a": a,
              "b": b
        },
        timeout=5,
    )
    response.raise_for_status()
    return response.json()

def add_name(first_name, last_name):
    response = requests.post(
        f"{BASE_URL}/name",
        json={
            "first_name": first_name,
            "last_name": last_name
        },
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def upload_settings(
    selected_folders,
    image_type,
    microscope,
    num_fovs,
    channels,
    disabled_fovs,
    start_time,
):
    response = requests.post(
        f"{BASE_URL}/upload_settings",
        json={
            "selected_folders": selected_folders,
            "image_type": image_type,
            "microscope": microscope,
            "num_fovs": num_fovs,
            "channels": channels,
            "disabled_fovs": disabled_fovs,
            "start_time": start_time,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def update_latest_end_time(end_time):
    response = requests.patch(
        f"{BASE_URL}/upload_settings/latest/end_time",
        json={"end_time": end_time},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def export_latest_settings():
    response = requests.get(
        f"{BASE_URL}/export_settings/latest",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()