# Step 1: Rename Keyence files for 2D or 3D data (multi-channel or single-channel, dynamic via JSON)

# Get directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Absolute path to jq
OS="$(uname -s)"

if [[ "$OS" == "Darwin" ]]; then
    JQ="$SCRIPT_DIR/../controller/jq-macos-arm64"    
else
    JQ="$SCRIPT_DIR/../controller/jq-windows-amd64.exe"
fi

JSON="$SCRIPT_DIR/../data/folder_paths.json"

DIR0="$PWD"
DATA_DIR="$SCRIPT_DIR/../data"

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
ls -d W* > "$DATA_DIR/dirlist"
dirnum=$(wc -l < "$DATA_DIR/dirlist")
echo "Number of wells: $dirnum"

for ((j=1; j<=dirnum; j++))
do
  dirname=$(awk -v k="$j" 'NR == k {print $1}' "$DATA_DIR/dirlist")
  echo "Well folder: $dirname"

  cd "$BASE_DIR/$dirname" || { echo "Failed to cd into $dirname"; continue; }

  wellname=$(echo _* | awk -F '[_]' '{print $2}')
  echo "Well name: $wellname"

  ls -d P* > "$DATA_DIR/tracklist"
  tracknum=$(wc -l < "$DATA_DIR/tracklist")
  echo "Positions: $tracknum"

  for ((n=1; n<=tracknum; n++))
  do
    trackname=$(awk -v k="$n" 'NR == k {print $1}' "$DATA_DIR/tracklist")
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

#Step 2: organizing. Did not finish in time for doc. it will be fixed by presentation.

DIR2="$TRACKS1"  # CLEANED directory from rename stage
DIR3="${TRACKS1%/}/ORDERED"

mkdir -p "$DIR3"

numFOVs=$("$JQ" -r '.NumFOVs' "$JSON")
if [ -z "$numFOVs" ] || [ "$numFOVs" = "null" ]; then
    numFOVs=9
fi

echo "Detecting wells from filenames..."

ls "$DIR2"/*.tif 2>/dev/null | xargs -n1 basename | awk -F '_' '{print $1}' | grep -E '^[A-Z][0-9]{2}$' | sort -u > "$DATA_DIR/welllist"

wells=()
while read -r line
do
    wells+=("$line")
done < "$DATA_DIR/welllist"


for well in "${wells[@]}"
do
    echo "Well: $well"

    mkdir -p "$DIR3/$well"

    for ((fov=1; fov<=numFOVs; fov++))
    do
        printf -v fov_fmt "%04d" "$fov"

        file="${well}_${fov_fmt}"

        destdir="$DIR3/$well/$file"
        mkdir -p "$destdir"/{DATA,OIR,MASKS,TEMP,OBJECTS}

        for ((c=0; c<channel_count; c++))
        do
            label=$("$JQ" -r ".Channels[$c].label" "$JSON")
            src="$DIR2/${file}_${label}.tif"

            if [ -f "$src" ]; then
                cp "$src" "$destdir/OIR/"
            else
                echo "Missing: $src"
            fi
        done
    done

    echo "Finished well $well"
done

echo ""
echo "Pipeline Complete"
exit