#!/bin/bash

export AXONLAB_API_URL="http://127.0.0.1:8000"

docker compose up -d --build

sleep 5

python -m frontend.tkinter_app
