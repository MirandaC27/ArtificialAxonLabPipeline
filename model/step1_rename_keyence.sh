# Step 1: Rename Keyence files for 2D or 3D data (multi-channel, dynamic via JSON)

# Get directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Absolute path to jq
JQ="$SCRIPT_DIR/../controller/jq-macos-arm64"
JSON="$SCRIPT_DIR/../view/folder_paths.json"

DIR0="$PWD"

# Read paths from JSON
DIR1=$("$JQ" -r '.Data[]' "$JSON")
TRACKS=$("$JQ" -r '.Tracks[]' "$JSON")
TRACKS1=$("$JQ" -r '.Tracks1[]' "$JSON")
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

#2D vs 3D

if [ "$IMAGE_TYPE" = "3D" ]; then

    # 3D has Plate level
    PLATE_DIR=$(find "$TRACKS" -mindepth 1 -maxdepth 1 -type d | head -n 1)

    if [ -z "$PLATE_DIR" ]; then
        echo "No Plate directory found inside $TRACKS"
        exit 1
    fi

    echo "Plate directory: $PLATE_DIR"
    BASE_DIR="$PLATE_DIR"

else
    # 2D has no Plate level
    BASE_DIR="$TRACKS"
fi

cd "$BASE_DIR" || { echo "Failed to cd into base directory"; exit 1; }

# well loop
ls -d W* > "$DIR0/dirlist"
dirnum=$(wc -l < "$DIR0/dirlist")
echo "Number of wells: $dirnum"

for ((j=1; j<=dirnum; j++))
do
  dirname=$(awk -v k="$j" 'NR == k {print $1}' "$DIR0/dirlist")
  echo "Well folder: $dirname"

  cd "$BASE_DIR/$dirname" || { echo "Failed to cd into $dirname"; continue; }

  wellname=$(echo _* | awk -F '[_]' '{print $2}')
  echo "Well name: $wellname"

  ls -d P* > "$DIR0/tracklist"
  tracknum=$(wc -l < "$DIR0/tracklist")
  echo "Positions: $tracknum"

  for ((n=1; n<=tracknum; n++))
  do
    trackname=$(awk -v k="$n" 'NR == k {print $1}' "$DIR0/tracklist")
    echo "  Position: $trackname"

    cd "$BASE_DIR/$dirname/$trackname" || { echo "Failed to cd into $trackname"; continue; }

    #channel loop
    for ((c=0; c<channel_count; c++))
    do
        channel_code=$("$JQ" -r ".Channels[$c].code" "$JSON")
        channel_label=$("$JQ" -r ".Channels[$c].label" "$JSON")

        oldname=$(echo *"${channel_code}".tif 2>/dev/null)

        if [ -z "$oldname" ] || [ "$oldname" = "*${channel_code}.tif" ]; then
            echo "    No file found for $channel_code"
            continue
        fi

        echo "    Found: $oldname"

        position_id=$(echo "$oldname" | awk -F 'P0' '{print $2}')
        position_id=$(echo "$position_id" | awk -F "_${channel_code}" '{print $1}')

        newname="${wellname}_${position_id}_${channel_label}.tif"

        echo "    Renaming → $newname"

        cp "$BASE_DIR/$dirname/$trackname/$oldname" "$TRACKS1/$newname"

    done
  done
done

echo "Done"
exit