#!/bin/bash

# Check if bucket path is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 gs://bucket/path/"
    exit 1
fi

BUCKET_PATH=$1
TEMP_DIR="/tmp/edge_files_temp"

# Create temp directory
mkdir -p $TEMP_DIR

# List all edge files in the bucket
gsutil ls "${BUCKET_PATH}/edges/*.csv" | while read file; do
    echo "Processing $file"
    
    # Get filename
    filename=$(basename "$file")
    local_file="${TEMP_DIR}/${filename}"
    
    # Download file
    gsutil cp "$file" "$local_file"
    
    # Modify header (first line only)
    sed -i.bak '1s/~label:String/~label/' "$local_file"
    
    # Upload modified file back
    gsutil cp "$local_file" "$file"
    
    # Clean up
    rm "$local_file" "${local_file}.bak"
    
    echo "✓ Completed $filename"
done

# Remove temp directory
rm -rf $TEMP_DIR

echo "All files processed!" 