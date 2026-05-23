#!/usr/bin/env bash

# Step 1: Rename Keyence files for 2D or 3D data (multi-channel or single-channel, dynamic via JSON)

# Get directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${AALP_RESOURCE_ROOT_BASH:-$(cd "$SCRIPT_DIR/.." && pwd)}"
DATA_DIR="${AALP_DATA_DIR_BASH:-$PROJECT_ROOT/data}"

# Absolute path to jq
OS="$(uname -s)"

if [[ "$OS" == "Darwin" ]]; then
    JQ="$PROJECT_ROOT/services/jq-macos-arm64"
else
    JQ="$PROJECT_ROOT/services/jq-windows-amd64.exe"
fi

JSON="$DATA_DIR/upload_settings.json"

source "$PROJECT_ROOT/controller/CleanDataController.sh"
source "$PROJECT_ROOT/controller/OrderDataController.sh"

DIR0="$PWD"

# Read paths from JSON
DIR1=$("$JQ" -r 'if has("DataBash") then .DataBash[] else .Data[] end' "$JSON")
TRACKS=$("$JQ" -r 'if has("TracksBash") then .TracksBash[] else .Tracks[] end' "$JSON")
TRACKS1=$("$JQ" -r 'if has("Tracks1Bash") then .Tracks1Bash[] else .Tracks1[] end' "$JSON")
IMAGE_TYPE=$("$JQ" -r '.ImageType' "$JSON")

echo "Image Type: $IMAGE_TYPE"
echo "RAW: $TRACKS"
echo "CLEAN: $TRACKS1"

cd "$DIR0" || { echo "Failed to cd to DIR0: $DIR0"; exit 1; }

# Create CLEAN directory
mkdir -p "$TRACKS1"

# Get number of channels from JSON
channel_count=$("$JQ" '.Channels | length' "$JSON")
echo "Number of channels: $channel_count"

# Validate RAW directory
cd "$TRACKS" || { echo "Failed to cd to TRACKS: $TRACKS"; exit 1; }

#2D vs 3D function
2Dvs3D

cd "$BASE_DIR" || { echo "Failed to cd into base directory"; exit 1; }

#well, track, channel loop
process_wells

echo "Done"

#Step 2: organizing cleaned data. 

DIR2="$TRACKS1"  # CLEANED directory from rename stage
DIR3="${TRACKS1%/}/ORDERED"

mkdir -p "$DIR3"

setup_wells
ordered_wells

echo ""
echo "Pipeline Complete"
exit
