#!/usr/bin/env bash

# Step 1: Rename Olympus files (2D or 3D)

# Get directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect OS for jq
OS="$(uname -s)"
if [[ "$OS" == "Darwin" ]]; then
    JQ="$SCRIPT_DIR/../services/jq-macos-arm64"
else
    JQ="$SCRIPT_DIR/../services/jq-windows-amd64.exe"
fi

JSON="$SCRIPT_DIR/../data/upload_settings.json"

DIR0="$PWD"
DATA_DIR="$SCRIPT_DIR/../data"

# Read paths from JSON
DIR1=$("$JQ" -r '.Data[]' "$JSON")
TRACKS=$("$JQ" -r '.Tracks[]' "$JSON")     # RAW Olympus folder
TRACKS1=$("$JQ" -r '.Tracks1[]' "$JSON")   # CLEAN output
IMAGE_TYPE=$("$JQ" -r '.ImageType' "$JSON")

echo "Microscope: Olympus"
echo "Image Type: $IMAGE_TYPE"
echo "RAW: $TRACKS"
echo "CLEAN: $TRACKS1"

cd "$DIR0" || { echo "Failed to cd to DIR0"; exit 1; }

# Create CLEAN directory
mkdir -p "$TRACKS1"

# Validate RAW directory
cd "$TRACKS" || { echo "Failed to cd to TRACKS: $TRACKS"; exit 1; }

# Get number of channels
channel_count=$("$JQ" '.Channels | length' "$JSON")
echo "Number of channels: $channel_count"

# --- Generate file list ---
ls *.oir > "$DATA_DIR/tracklist" 2>/dev/null
tracknum=$(wc -l < "$DATA_DIR/tracklist")

if [ "$tracknum" -eq 0 ]; then
    echo "⚠️ No .oir files found in $TRACKS"
    exit 1
fi

echo "Found $tracknum Olympus files."

# --- Loop through files ---
for ((n = 1; n <= tracknum; n++)); do

    filename=$(awk -v k="$n" 'NR == k {print $1}' "$DATA_DIR/tracklist")
    echo ""
    echo "Processing: $filename"

    # Example filename: B02_0001.oir
    base=$(basename "$filename" .oir)

    # Extract well and position
    well=$(echo "$base" | awk -F '_' '{print $1}')        # B02
    position=$(echo "$base" | awk -F '_' '{print $2}')    # 0001

    # Normalize well name (optional: B02 → B2)
    row=$(echo "$well" | cut -c1)
    col=$(echo "$well" | cut -c2- | sed 's/^0*//')
    well_clean="${row}${col}"

    echo "  Well: $well_clean"
    echo "  Position: $position"

    # --- Handle channels ---
    for ((c=0; c<channel_count; c++)); do

        channel_label=$("$JQ" -r ".Channels[$c].label" "$JSON")

        # Olympus OIR = multi-channel in ONE file
        # So we don't split here — just rename once per channel logically

        newname="${well_clean}_${position}_${channel_label}.oir"

        echo "  → $newname"

        cp "$TRACKS/$filename" "$TRACKS1/$newname"

    done

done

echo ""
echo "Olympus renaming complete."
exit 0