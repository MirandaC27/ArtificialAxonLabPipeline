#!/usr/bin/env bash

# Resolve project root (script is inside /analysis/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_ROOT="$(dirname "$PROJECT_ROOT")"

# Use the ordered folder selected for the current session. The pipeline exports
# ORDERED_TRACK; a direct/manual invocation can pass the path as argument 1.
TRACKS="${1:-${ORDERED_TRACK:-}}"

if [[ -z "$TRACKS" && -f "$BACKEND_ROOT/data/upload_settings.json" ]]; then
  TRACKS="$(python - "$BACKEND_ROOT/data/upload_settings.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    ordered = json.load(handle).get("OrderedTrack") or []
print(ordered[0] if ordered else "")
PY
)"
fi

if [[ -z "$TRACKS" ]]; then
  echo "Usage: $0 <ordered-folder>" >&2
  echo "Or set ORDERED_TRACK to the session's ordered folder." >&2
  exit 2
fi

if [[ ! -d "$TRACKS" ]]; then
  echo "Ordered folder does not exist: $TRACKS" >&2
  exit 2
fi

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