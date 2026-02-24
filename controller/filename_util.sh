#!/usr/bin/env bash

cleaned_file_name() {
    datadir="$1"
    exp=$(basename "$datadir")
    date=$(date +"%Y-%m-%d")
    echo "${date}_${exp}_CLEANED"
}

ordered_file_name() {
    datadir="$1"
    exp=$(basename "$datadir")
    date=$(date +"%Y-%m-%d")
    echo "${date}_${exp}_ORDERED"
}
