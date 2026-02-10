# Step 1: Rename Keyence files for 2D assay data, single channel
JQ="../controller/jq-windows-amd64.exe"
JSON="../view/folder_paths.json"

DIR0="$PWD"
DIR1=$("$JQ" -r '.Data[]' "$JSON")  # Path to data

cd "$DIR0" || { echo "Failed to cd to DIR0: $DIR0"; exit 1; }

TRACKS=$("$JQ" -r '.Tracks[]' "$JSON")
TRACKS1=$("$JQ" -r '.Tracks1[]' "$JSON")

cd "$TRACKS" || { echo "Failed to cd to TRACKS: $TRACKS"; exit 1; }

ls -d W* > "$DIR0/dirlist"

dirnum=$(wc -l < "$DIR0/dirlist")
echo "$dirnum"

for ((j=1; j<=dirnum; j++))
do
  dirname=$(awk -v k="$j" 'NR == k {print $1}' "$DIR0/dirlist")
  echo "$dirname"

  cd "$TRACKS/$dirname" || { echo "Failed to cd into $dirname"; continue; }

  wellname=$(echo _* | awk -F '[_]' '{print $2}')

  ls -d P* > "$DIR0/tracklist"
  tracknum=$(wc -l < "$DIR0/tracklist")
  echo "$tracknum"

  for ((n = 1; n <= tracknum; n++))
  do
    trackname=$(awk -v k="$n" 'NR == k {print $1}' "$DIR0/tracklist")
    echo "$trackname"

    cd "$TRACKS/$dirname/$trackname" || { echo "Failed to cd into $trackname"; continue; }
    pwd

    oldname1=$(echo *CH1.tif)  # rMDeb
    echo "oldname $oldname1"

    newname1=$(echo "$oldname1" | awk -F 'P0' '{print $2}' | awk -v well="$wellname" -F '_CH1' '{print well "_" $1 "_debris.tif"}')
    echo "newname $newname1"

    cp "$TRACKS/$dirname/$trackname/$oldname1" "$TRACKS1/$newname1"
  done
done

echo 'Done'
exit
