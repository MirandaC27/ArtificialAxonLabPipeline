import os
import requests

BASE_URL = os.getenv("AXONLAB_API_URL", "http://localhost:8001").rstrip("/")

#---------------------------------------------------
def add_numbers(a, b):
    response = requests.post(
        f"{BASE_URL}/add",
        json={
            "a": a, 
            "b": b
        },
        timeout=5,
    )
    response.raise_for_status()
    return response.json()

#---------------------------------------------------
def combine_name(first_name, last_name):
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

#---------------------------------------------------
def save_session(a, b, first_name, last_name):
    response = requests.post(
        f"{BASE_URL}/sessions",
        json={
            "a": a,
            "b": b,
            "first_name": first_name,
            "last_name": last_name
        },
        timeout=5
    )

    response.raise_for_status()
    return response.json()


def get_recent_sessions():
    response = requests.get(
        f"{BASE_URL}/sessions/recent",
        timeout=5
    )

    response.raise_for_status()
    return response.json()

#---------------------------------------------------
def save_config(config_name, a, b, first_name, last_name):
    response = requests.post(
        f"{BASE_URL}/configs",
        json={
            "config_name": config_name,
            "a": a,
            "b": b,
            "first_name": first_name,
            "last_name": last_name
        },
        timeout=5
    )
    response.raise_for_status()
    return response.json()


def get_configs():
    response = requests.get(
        f"{BASE_URL}/configs",
        timeout=5
    )
    response.raise_for_status()
    return response.json()


def reorder_configs(config_ids):
    response = requests.post(
        f"{BASE_URL}/configs/reorder",
        json=config_ids,
        timeout=5
    )

    response.raise_for_status()
    return response.json()