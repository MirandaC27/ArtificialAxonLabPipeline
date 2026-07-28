import os
import requests

BASE_URL = os.getenv("AXONLAB_API_URL", "http://localhost:8000").rstrip("/")

#---------------------------------------------------
def save_masking(masking_data):
    response = requests.post(f"{BASE_URL}/masking", json=masking_data, timeout=10)
    response.raise_for_status()
    return response.json()


def save_upload_step1(upload_data, settings_data, masking_data=None):
    payload = {
        **upload_data,
        "settings_data": settings_data,
        "masking_data": masking_data or {}
    }

    response = requests.post(
        f"{BASE_URL}/upload-step1",
        json=payload,
        timeout=10
    )

    response.raise_for_status()
    return response.json()


def get_recent_upload_step1():
    response = requests.get(
        f"{BASE_URL}/upload-step1/recent",
        timeout=10
    )

    response.raise_for_status()
    return response.json()


# ---------------------------------------------------
# Saved configurations

def save_config(config_name, upload_data, settings_data, masking_data=None):
    payload = {
        "config_name": config_name,
        **upload_data,
        "settings_data": settings_data,
        "masking_data": masking_data or {}
    }

    response = requests.post(
        f"{BASE_URL}/upload-configs",
        json=payload,
        timeout=10
    )

    response.raise_for_status()
    return response.json()


def get_configs():
    response = requests.get(
        f"{BASE_URL}/upload-configs",
        timeout=10
    )

    response.raise_for_status()
    return response.json()


def reorder_configs(ids):
    response = requests.post(
        f"{BASE_URL}/upload-configs/reorder",
        json=ids,
        timeout=10
    )

    response.raise_for_status()
    return response.json()