#!/bin/bash

# Directory to list files from
directory="src"

# Use find to list all files in the directory recursively
find "$directory" -type f | while read -r file; do
    # Get the filename without the directory path
    filename=$(basename "$file")

    # Output filename
    echo "File: $filename"

    # Output file content
    echo "Content:"
    cat "$file"
    echo "----------------------------------------"
done

