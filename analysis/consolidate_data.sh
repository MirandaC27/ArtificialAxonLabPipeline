#!/usr/bin/env bash

# Resolve project root (assumes script is inside /analysis/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

TRACKS="/Users/chloemiranda/capstone/CLEANED/ORDERED"

# Create results folder at project root
RESULTS_DIR="$PROJECT_ROOT/results"
mkdir -p "$RESULTS_DIR"

OUTFILE="$RESULTS_DIR/nuclei_summary.csv"

echo "well,fov,nuclei" > "$OUTFILE"

echo "Scanning: $TRACKS"
echo "Output: $OUTFILE"

for WELL_PATH in "$TRACKS"/*/; do
  [[ -d "$WELL_PATH" ]] || continue

  well=$(basename "$WELL_PATH")
  echo "Processing well: $well"

  for FOV_PATH in "$WELL_PATH"/*/; do
    [[ -d "$FOV_PATH" ]] || continue

    fov=$(basename "$FOV_PATH")
    FILE="$FOV_PATH/DATA/nuclei.out"

    if [[ ! -f "$FILE" ]]; then
      echo "$well,$fov,0" >> "$OUTFILE"
      continue
    fi

    nuclei=$(awk 'NR==2 {print $1}' "$FILE")
    nuclei=${nuclei:-0}

    echo "$well,$fov,$nuclei" >> "$OUTFILE"
  done
done

echo "Done → $OUTFILE"