
SKIP_FOVS=($("$JQ" -r '.SkipFOVs[]? // empty' "$JSON"))
SKIP_CHANNELS=($("$JQ" -r '.SkipChannels[]? // empty' "$JSON"))

setup_wells(){
    numFOVs=$("$JQ" -r '.NumFOVs' "$JSON")
    if [ -z "$numFOVs" ] || [ "$numFOVs" = "null" ]; then
        numFOVs=9
    fi

    echo "Detecting wells from filenames..."

    find "$DIR2" -name "*.tif" -printf "%f\n" | awk -F '_' '/^[A-Z][0-9]{2}/ {print $1}' | sort -u > "$DATA_DIR/welllist"
    
    wells=()
    while read -r line
    do
        wells+=("$line")
    done < "$DATA_DIR/welllist"

}

channel_tiffs_into_oir(){
    for ((c=0; c<channel_count; c++))
    do
        label=$("$JQ" -r ".Channels[$c].label" "$JSON")

        if should_skip_channel "$label"; then
            echo "Skipping channel $label"
            continue
        fi

        src="$DIR2/${file}_${label}.tif"

        if [ -f "$src" ]; then
            cp "$src" "$destdir/OIR/"
        else
            echo "Missing: $src"
        fi
    done
}

process_fovs() {
    max_jobs=5

    for ((fov=1; fov<=numFOVs; fov++))
    do
        if should_skip_fov "$well" "$fov"; then
            echo "Skipping FOV $fov in $well"
            continue
        fi

        printf -v fov_fmt "%04d" "$fov"
        file="${well}_${fov_fmt}"
        destdir="$DIR3/$well/$file"

        (
            mkdir -p "$destdir"/{DATA,OIR,MASKS,TEMP,OBJECTS}
            channel_tiffs_into_oir
        ) &

        if (( $(jobs -r | wc -l) >= max_jobs )); then
            wait -n
        fi
    done

    wait
}

ordered_wells(){
    for well in "${wells[@]}"
    do
        echo "Well: $well"

        mkdir -p "$DIR3/$well"

        process_fovs

        echo "Finished well $well"
    done
}


should_skip_fov() {
    local well="$1"
    local fov="$2"

    for skip in "${SKIP_FOVS[@]}"; do
        [[ "$fov" -eq "$skip" ]] && return 0
    done

    # Per-well skip
    per_well=$("$JQ" -r --arg w "$well" '.SkipFOVsPerWell[$w][]? // empty' "$JSON")
    for skip in $per_well; do
        [[ "$fov" -eq "$skip" ]] && return 0
    done

    return 1
}

should_skip_channel() {
    local label="$1"

    for skip in "${SKIP_CHANNELS[@]}"; do
        [[ "$label" == "$skip" ]] && return 0
    done

    return 1
}

