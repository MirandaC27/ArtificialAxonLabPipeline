#!/usr/bin/env bash
# Clean/Order implementation used by the Tkinter workflow.

2Dvs3D(){
    if [ "$IMAGE_TYPE" = "3D" ]; then
        # 3D has Plate level.
        PLATE_DIR=$(find "$TRACKS" -mindepth 1 -maxdepth 1 -type d | head -n 1)

        if [ -z "$PLATE_DIR" ]; then
            echo "No Plate directory found inside $TRACKS"
            exit 1
        fi

        BASE_DIR="$PLATE_DIR"
    else
        # 2D has no Plate level.
        BASE_DIR="$TRACKS"
    fi
}

process_wells(){
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

        process_tracks
    done
}

process_tracks() {
    max_jobs=5

    for ((n=1; n<=tracknum; n++))
    do
        (
            trackname=$(awk -v k="$n" 'NR == k {print $1}' "$DATA_DIR/tracklist")
            echo "  Position: $trackname"

            cd "$BASE_DIR/$dirname/$trackname" || {
                echo "Failed to cd into $trackname"
                exit
            }

            process_channels
        ) &

        if (( $(jobs -r | wc -l) >= max_jobs )); then
            wait -n
        fi
    done

    wait
}

process_channels(){
    for ((c=0; c<channel_count; c++))
    do
        channel_code="${CHANNEL_CODES[$c]}"
        channel_label="${CHANNEL_LABELS[$c]}"

        oldname=$(echo *"${channel_code}".tif 2>/dev/null)

        if [ -z "$oldname" ] || [ "$oldname" = "*${channel_code}.tif" ]; then
            echo "    No file found for $channel_code"
            continue
        fi

        echo "    Found: $oldname"

        position_id=$(echo "$oldname" | awk -F 'P0' '{print $2}')
        position_id=$(echo "$position_id" | awk -F "_${channel_code}" '{print $1}')

        newname="${wellname}_${position_id}_${channel_label}.tif"

        echo "    Renaming -> $newname"

        cp "$BASE_DIR/$dirname/$trackname/$oldname" "$TRACKS1/$newname"
    done
}

# End CleanData functions.
