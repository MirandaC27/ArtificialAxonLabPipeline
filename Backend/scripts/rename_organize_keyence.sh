# Clean and order Keyence files for 2D or 3D data using Tkinter inputs.

set -euo pipefail

# Positional inputs from the Tkinter page / upload service.
TRACKS="${1:-}"
TRACKS1="${2:-}"
DIR3="${3:-}"
DIR1="${4:-}"
IMAGE_TYPE="${5:-3D}"
MICROSCOPE="${6:-Keyence}"
numFOVs="${7:-9}"
DISABLED_FOVS="${8:-}"
CHANNEL_CODES_ARG="${9:-}"
CHANNEL_LABELS_ARG="${10:-}"

# Get directory of this script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR0="$PWD"
DATA_DIR="$SCRIPT_DIR/../data"

source "$SCRIPT_DIR/CleanData.sh"
source "$SCRIPT_DIR/OrderData.sh"

IFS='|' read -r -a CHANNEL_CODES <<< "$CHANNEL_CODES_ARG"
IFS='|' read -r -a CHANNEL_LABELS <<< "$CHANNEL_LABELS_ARG"
IFS=',' read -r -a DISABLED_FOV_LIST <<< "$DISABLED_FOVS"

channel_count=${#CHANNEL_CODES[@]}
DIR2="$TRACKS1"

is_disabled_fov() {
    local candidate="$1"
    local disabled

    for disabled in "${DISABLED_FOV_LIST[@]}"; do
        disabled="${disabled//[[:space:]]/}"

        if [ -n "$disabled" ] && [ "$disabled" = "$candidate" ]; then
            return 0
        fi
    done

    return 1
}

if [ -z "$TRACKS" ]; then
    echo "Missing required argument 1: raw track directory"
    exit 1
fi

if [ -z "$TRACKS1" ]; then
    echo "Missing required argument 2: cleaned output directory"
    exit 1
fi

if [ -z "$DIR3" ]; then
    DIR3="${TRACKS1%/}/ORDERED"
fi

if [ -z "$numFOVs" ] || [ "$numFOVs" = "0" ]; then
    numFOVs=9
fi

if [ "$channel_count" -eq 0 ] || [ -z "${CHANNEL_CODES[0]:-}" ]; then
    echo "Missing channel inputs"
    exit 1
fi

if [ "${#CHANNEL_LABELS[@]}" -ne "$channel_count" ]; then
    echo "Channel code/label count mismatch"
    exit 1
fi

echo "Image Type: $IMAGE_TYPE"
echo "Microscope: $MICROSCOPE"
echo "RAW: $TRACKS"
echo "CLEAN: $TRACKS1"
echo "ORDERED: $DIR3"
echo "DATA: ${DIR1:-None}"
echo "Number of FOVs: $numFOVs"
echo "Disabled FOVs: ${DISABLED_FOVS:-None}"
echo "Number of channels: $channel_count"

cd "$DIR0" || { echo "Failed to cd to DIR0: $DIR0"; exit 1; }

mkdir -p "$DATA_DIR"
mkdir -p "$TRACKS1"
mkdir -p "$DIR3"

cd "$TRACKS" || { echo "Failed to cd to TRACKS: $TRACKS"; exit 1; }

2Dvs3D

cd "$BASE_DIR" || { echo "Failed to cd into base directory"; exit 1; }

process_wells

echo "Done"
echo ""
echo "Step 2: organizing cleaned data."

setup_wells
ordered_wells

echo ""
echo "Pipeline Complete"
