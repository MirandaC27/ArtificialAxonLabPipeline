JQ="../controller/jq-windows-amd64.exe"
JSON="../view/folder_paths.json"

"$JQ" -r '.Tracks[]' "$JSON"
"$JQ" -r '.Tracks1[]' "$JSON"