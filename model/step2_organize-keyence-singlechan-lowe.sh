# Step 2: Organize Keyence single-channel images
#         Assumes that Columns 2-11 are being used in each plate row (edit if untrue)
JQ="../controller/jq-windows-amd64.exe"
JSON="../view/folder_paths.json"

DIR0="$PWD"
DIR1=$("$JQ" -r '.Data[]' "$JSON")  # Path to data
numFOVs=6;

DIR2=$("$JQ" -r '.Cleaned[]' "$JSON")
DIR3="$DIR1/2025-08-12_rMDeb_Plate2_1xSecAb_ORDERED"

cd "$DIR0" || { echo "Failed to cd to DIR0"; exit 1; }
dirlist="dirlist-ROW-LETTER" # Plate rows to analyze (e.g. B C D)
echo "$dirlist"
dirnum=$(wc -l < "$dirlist")

# Go over plate rows listed in dirlist
for ((j=1; j<=dirnum; j++)); do
  dirname=$(awk -v kk="$j" 'NR == kk {print $1}' "$dirlist")
  echo "$dirname"

  # Go over plate row columns 2 to 9
  for ((k=2; k<=9; k++)); do
    well="${dirname}${k}"
    echo "$well"

    mkdir -p "$DIR3/$well"

    for ((n=1; n<=numFOVs; n++)); do
      file="${dirname}0${k}_000${n}"
      echo "$file"

      destdir="$DIR3/$well/$file"
      mkdir -p "$destdir"/{DATA,OIR,MASKS,TEMP,OBJECTS}

      cp "$DIR2/${file}_debris.tif" "$destdir/OIR/debris.tif"
    done
  done

  # Go over plate row columns 10 and 11
  for ((k=10; k<=11; k++)); do
    well="${dirname}${k}"
    echo "$well"

    mkdir -p "$DIR3/$well"

    for ((n=1; n<=numFOVs; n++)); do
      file="${dirname}${k}_000${n}"
      echo "$file"

      destdir="$DIR3/$well/$file"
      mkdir -p "$destdir"/{DATA,OIR,MASKS,TEMP,OBJECTS}

      cp "$DIR2/${file}_debris.tif" "$destdir/OIR/debris.tif"
    done
  done

  echo 'Done with' "$dirname"
  cd "$DIR0"
done

exit
