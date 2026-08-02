import os

import requests


BASE_URL = os.getenv("AXONLAB_API_URL", "http://localhost:8000").rstrip("/")


# ---------------------------------------------------
# Upload API

UPLOAD_URL = f"{BASE_URL}/upload-step1"


def save_upload_step1(upload_data, settings_data, masking_data=None):
    payload = {
        **upload_data,
        "settings_data": settings_data,
        "masking_data": masking_data or {},
    }
    response = requests.post(UPLOAD_URL, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def get_recent_upload_step1():
    response = requests.get(f"{UPLOAD_URL}/recent", timeout=10)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------
# Settings API

SETTINGS_URL = f"{BASE_URL}/settings"


def save_settings(settings_data):
    response = requests.post(SETTINGS_URL, json=settings_data, timeout=10)
    response.raise_for_status()
    return response.json()


def get_recent_settings():
    response = requests.get(f"{SETTINGS_URL}/recent", timeout=10)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------
# Masking API

MASKING_URL = f"{BASE_URL}/masking"


def save_masking(masking_data):
    response = requests.post(MASKING_URL, json=masking_data, timeout=10)
    response.raise_for_status()
    return response.json()


def get_recent_masking():
    response = requests.get(f"{MASKING_URL}/recent", timeout=10)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------
# Config API

CONFIGS_URL = f"{BASE_URL}/upload-configs"


def save_config(config_name, upload_data, settings_data, masking_data=None):
    payload = {
        "config_name": config_name,
        **upload_data,
        "settings_data": settings_data,
        "masking_data": masking_data or {},
    }
    response = requests.post(CONFIGS_URL, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def get_configs():
    response = requests.get(CONFIGS_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def delete_config(config_id):
    response = requests.delete(f"{CONFIGS_URL}/{config_id}", timeout=10)
    response.raise_for_status()
    return response.json()


def reorder_configs(ids):
    response = requests.post(f"{CONFIGS_URL}/reorder", json=ids, timeout=10)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------
# Results API

RESULTS_URL = f"{BASE_URL}/results"


def save_result_csv(filename, content_base64, overwrite=False):
    return requests.post(
        RESULTS_URL,
        json={
            "filename": filename,
            "content_base64": content_base64,
            "overwrite": overwrite,
        },
        timeout=30,
    )


def get_result_csvs():
    response = requests.get(RESULTS_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def get_result_csv(result_id):
    response = requests.get(f"{RESULTS_URL}/{result_id}", timeout=30)
    response.raise_for_status()
    return response.json()


def delete_result_csv(result_id):
    response = requests.delete(f"{RESULTS_URL}/{result_id}", timeout=10)
    response.raise_for_status()


def reorder_result_csvs(ids):
    response = requests.post(f"{RESULTS_URL}/reorder/all", json=ids, timeout=10)
    response.raise_for_status()
    return response.json()

# ---------------------------------------------------
# Analysis API

ANALYSIS_URL = f"{BASE_URL}/analysis"


def start_analysis_job(upload_data, settings_data, masking_data):
    response = requests.post(
        f"{ANALYSIS_URL}/jobs",
        json={
            "upload_data": upload_data,
            "settings_data": settings_data,
            "masking_data": masking_data,
        },
        timeout=15,
    )
    if response.status_code == 409:
        # Reconnect to the existing worker instead of showing a conflict.
        try:
            detail = response.json().get("detail", "")
            job_id = int(detail.split("Analysis job ", 1)[1].split()[0])
        except (AttributeError, IndexError, TypeError, ValueError):
            response.raise_for_status()
        return get_analysis_job(job_id)
    response.raise_for_status()
    return response.json()


def get_analysis_job(job_id):
    response = requests.get(f"{ANALYSIS_URL}/jobs/{job_id}", timeout=10)
    response.raise_for_status()
    return response.json()
