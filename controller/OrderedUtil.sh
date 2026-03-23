setup_wells(){
    numFOVs=$("$JQ" -r '.NumFOVs' "$JSON")
    if [ -z "$numFOVs" ] || [ "$numFOVs" = "null" ]; then
        numFOVs=9
    fi

    echo "Detecting wells from filenames..."

    find "$DIR2" -name "*.tif" -printf "%f\n" \
    | awk -F '_' '/^[A-Z][0-9]{2}/ {print $1}' \
    | sort -u \
    > "$DATA_DIR/welllist"
    
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
        src="$DIR2/${file}_${label}.tif"

        if [ -f "$src" ]; then
            cp "$src" "$destdir/OIR/"
        else
            echo "Missing: $src"
        fi
    done
}

process_fovs(){
    for ((fov=1; fov<=numFOVs; fov++))
    do
        printf -v fov_fmt "%04d" "$fov"

        file="${well}_${fov_fmt}"

        destdir="$DIR3/$well/$file"
        mkdir -p "$destdir"/{DATA,OIR,MASKS,TEMP,OBJECTS}

        channel_tiffs_into_oir
    done
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


