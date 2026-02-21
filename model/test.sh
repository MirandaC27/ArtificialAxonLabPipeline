#!/bin/bash
JQ="../controller/jq-windows-amd64.exe"
JSON="../view/folder_paths.json"

DATA=$("$JQ" -r '.Data[]' "$JSON")
TRACKS=$("$JQ" -r '.Tracks[]' "$JSON")
TRACKS1=$("$JQ" -r '.Tracks1[]' "$JSON")

echo "---------Printing Folder Paths---------"
echo "Data: $DATA"
echo "Tracks: $TRACKS"
echo "Tracks1: $TRACKS1"

echo "---------Running CleanedFileName function from HelperFunctions.py---------"
name=$(python3 ../controller/runHelper.py CleanedFileName "$DATA")

echo "Cleaned File Name: $name"

exit