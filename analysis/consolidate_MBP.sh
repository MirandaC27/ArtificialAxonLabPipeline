#!/usr/bin/env bash

# Resolve project root (script is inside /analysis/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

OS="$(uname -s)"
if [[ "$OS" == "Darwin" ]]; then
    JQ="$PROJECT_ROOT/services/jq-macos-arm64"
else
    JQ="$PROJECT_ROOT/services/jq-windows-amd64.exe"
fi

JSON="$PROJECT_ROOT/data/upload_settings.json"
TRACKS=$("$JQ" -r '.OrderedTrack[0]' "$JSON")

RESULTS_DIR="$PROJECT_ROOT/results"
mkdir -p "$RESULTS_DIR"

OUTFILE="$RESULTS_DIR/mbp_particles.csv"

echo "well,fov,particle,Area,Mean,Min,Max,Circ,IntDen,RawIntDen,AR,Round,Solidity" > "$OUTFILE"

echo "Scanning: $TRACKS"
echo "Output: $OUTFILE"

for WELL_PATH in "$TRACKS"/*/; do
  [[ -d "$WELL_PATH" ]] || continue
  well=$(basename "$WELL_PATH")

  echo "Processing well: $well"

  for FOV_PATH in "$WELL_PATH"/*/; do
    [[ -d "$FOV_PATH" ]] || continue
    fov=$(basename "$FOV_PATH")

    DATA="$FOV_PATH/DATA"

    # Find MBP file dynamically (handles threshold naming)
    FILE=$(find "$DATA" -maxdepth 1 -name "Total-MBP-2D-*.out" | head -n 1)

    if [[ ! -f "$FILE" ]]; then
      echo "  Missing MBP file for $well $fov"
      continue
    fi

    # Skip header, process rows
    tail -n +2 "$FILE" | while read -r line; do

      # Normalize spacing toCSV
      parsed=$(echo "$line" | awk '{$1=$1; print}' | tr ' ' ',')

      # Extract particle index separately
      particle=$(echo "$parsed" | cut -d',' -f1)
      values=$(echo "$parsed" | cut -d',' -f2-)

      echo "$well,$fov,$particle,$values" >> "$OUTFILE"

    done

  done
done

echo "Done: $OUTFILE"
