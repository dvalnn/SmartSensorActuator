#!/usr/bin/env bash

# Check if required commands exist
for cmd in base64 crc32; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "Error: $cmd command not found" >&2
    exit 1
  fi
done

# Check if arguments are provided
if [ "$#" -eq 2 ]; then
    INPUT_FILE="$1"
    OUTPUT_JSON="$2"
    # Validate input file exists
    if [ ! -f "$INPUT_FILE" ]; then
        echo "Error: Input file '$INPUT_FILE' not found" >&2
        exit 1
    fi
elif [ "$#" -eq 0 ]; then
    INPUT_FILE="/dev/stdin"
    OUTPUT_JSON="/dev/stdout"
else
    echo "Usage: $0 [input_file output_json]" >&2
    exit 1
fi

# Get CRC32 checksum in hex format with 0x prefix
if [ "$INPUT_FILE" = "/dev/stdin" ]; then
    TEMP_FILE=$(mktemp)
    cat > "$TEMP_FILE"
    BASE64_STR=$(base64 -w 0 "$TEMP_FILE")
    CRC32_HEX="0x$(crc32 < "$TEMP_FILE")"
    rm "$TEMP_FILE"
else
    BASE64_STR=$(base64 -w 0 "$INPUT_FILE")
    CRC32_HEX="0x$(crc32 < "$INPUT_FILE")"
fi

# Create JSON output
JSON_CONTENT="{\"base64\":\"$BASE64_STR\",\"crc32\":\"$CRC32_HEX\"}"

echo "$JSON_CONTENT" > "$OUTPUT_JSON"
