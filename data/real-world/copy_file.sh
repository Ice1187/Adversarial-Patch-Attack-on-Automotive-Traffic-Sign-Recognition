#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 source_directory destination_directory"
    exit 1
fi

SOURCE_DIR=$1
DEST_DIR=$2

# Check if the source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Source directory $SOURCE_DIR does not exist."
    exit 1
fi

# Create the destination directory if it doesn't exist
mkdir -p "$DEST_DIR"

# Function to generate a unique filename
generate_unique_filename() {
    local dest_dir=$1
    local base_name=$2
    local extension=$3
    local new_name=$base_name.$extension
    local counter=1

    while [ -e "$dest_dir/$new_name" ]; do
        new_name="${base_name}_${counter}.$extension"
        counter=$((counter + 1))
    done

    echo "$new_name"
}

# Find and copy all .jpg files recursively
find "$SOURCE_DIR" -type f -name '*.jpg' | while read -r file; do
    base_name=$(basename "$file" .jpg)
    extension="jpg"
    unique_name=$(generate_unique_filename "$DEST_DIR" "$base_name" "$extension")
    cp "$file" "$DEST_DIR/$unique_name"
    echo "Copied $file to $DEST_DIR/$unique_name"
done

echo "All .jpg files have been copied to $DEST_DIR"

