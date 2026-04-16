import os
import requests

BASE_URL = os.getenv("AXONLAB_API_URL", "http://localhost:8000").rstrip("/")

def add_numbers(a, b):
    response = requests.post(
        f"{BASE_URL}/add",
        json={"a": a, "b": b},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()