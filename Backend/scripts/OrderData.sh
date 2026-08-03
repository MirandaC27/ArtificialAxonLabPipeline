#!/usr/bin/env bash
# Clean/Order implementation used by the Tkinter workflow.

setup_wells(){
    echo "Detecting wells from filenames..."

    find "$DIR2" -name "*.tif" | sed 's|.*/||' | awk -F '_' '/^[A-Z][0-9]{2}/ {print $1}' | sort -u > "$DATA_DIR/welllist"

    wells=()
    while read -r line
    do
        wells+=("$line")
    done < "$DATA_DIR/welllist"
}

channel_tiffs_into_oir(){
    for ((c=0; c<channel_count; c++))
    do
        label="${CHANNEL_LABELS[$c]}"
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
        if is_disabled_fov "$fov"; then
            echo "Skipping disabled FOV $fov for $well"
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

# End OrderData functions.
