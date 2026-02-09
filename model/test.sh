#!/bin/bash

FILE="../view/folder_paths.txt"

if [ ! -f "$FILE" ]; then
    echo "Error: $FILE not found!"
    exit 1
fi

cat "$FILE"

exit 0
