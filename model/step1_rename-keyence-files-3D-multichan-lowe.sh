# Step 1: Rename Keyence files for 3D assay data (on Artificial Axons), multi-channel, with or without debris channel
JQ="../controller/jq-windows-amd64.exe"
JSON="../view/folder_paths.json"
source ../controller/filename_util.sh

DIR0="$PWD"
DIR1=$("$JQ" -r '.Data[]' "$JSON")  # Path to data

cd "$DIR0" || { echo "Failed to cd to DIR0: $DIR0"; exit 1; }

TRACKS=$("$JQ" -r '.Tracks[]' "$JSON")

cleaned_dir=$(cleaned_file_name "$DIR1")
mkdir -p "$DIR1/$cleaned_dir"
TRACKS1="$DIR1/$cleaned_dir"

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

    oldname1=$(echo *CH3.tif)  # nuclei
    oldname2=$(echo *CH4.tif)  # myelin
    oldname3=$(echo *CH2.tif)  # axons
    #oldname4=$(echo *CH1.tif)  # debris
    
    echo "oldname $oldname1 $oldname2 $oldname3"          #without debris
    #echo "oldname $oldname1 $oldname2 $oldname3 $oldname4"  #with debris

    newname1=$(echo "$oldname1" | awk -F 'P0' '{print $2}' | awk -v well="$wellname" -F '_CH3' '{print well "_" $1 "_nuclei.tif"}')
    newname2=$(echo "$oldname2" | awk -F 'P0' '{print $2}' | awk -v well="$wellname" -F '_CH4' '{print well "_" $1 "_myelin.tif"}')
    newname3=$(echo "$oldname3" | awk -F 'P0' '{print $2}' | awk -v well="$wellname" -F '_CH2' '{print well "_" $1 "_axons.tif"}')
    #newname4=$(echo "$oldname4" | awk -F 'P0' '{print $2}' | awk -v well="$wellname" -F '_CH1' '{print well "_" $1 "_debris.tif"}')

    echo "newname $newname1 $newname2 $newname3"      #without debris 
    #echo "newname $newname1 $newname2 $newname3 $newname4"  #with debris

    cp "$TRACKS/$dirname/$trackname/$oldname1" "$TRACKS1/$newname1"
    cp "$TRACKS/$dirname/$trackname/$oldname2" "$TRACKS1/$newname2"
    cp "$TRACKS/$dirname/$trackname/$oldname3" "$TRACKS1/$newname3"
    #cp "$TRACKS/$dirname/$trackname/$oldname4" "$TRACKS1/$newname4"
  done
done

echo 'Done'
exit
