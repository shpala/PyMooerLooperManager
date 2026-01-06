#!/usr/bin/env python3
"""
Extract app.asar from mooer.exe

ASAR file format has a specific header structure.
This script searches for ASAR signatures and attempts extraction.
"""

import struct
import json
import os
import sys

def find_asar_offset(data):
    """Search for ASAR file signature in data."""
    # ASAR files start with a 16-byte header containing size info
    # Followed by JSON metadata
    # Look for patterns that indicate ASAR start

    offsets = []
    search_term = b'"files":'

    # First, find potential JSON metadata sections
    pos = 0
    while True:
        pos = data.find(search_term, pos)
        if pos == -1:
            break

        # Check if there's a size indicator before this
        # ASAR header format: 4 bytes (pickle size) + 4 bytes (header size) + 8 bytes (file size)
        if pos >= 16:
            potential_offset = pos - 16
            try:
                # Read the header info
                pickle_size = struct.unpack('<I', data[potential_offset:potential_offset+4])[0]
                header_size_with_padding = struct.unpack('<I', data[potential_offset+4:potential_offset+8])[0]
                file_size = struct.unpack('<Q', data[potential_offset+8:potential_offset+16])[0]

                # Validate sizes are reasonable
                if (pickle_size < 1000000 and header_size_with_padding < 10000000 and
                    file_size > 0 and file_size < 500000000):
                    offsets.append({
                        'offset': potential_offset,
                        'pickle_size': pickle_size,
                        'header_size': header_size_with_padding,
                        'file_size': file_size,
                        'json_offset': pos
                    })
                    print(f"Found potential ASAR at offset {potential_offset}: "
                          f"pickle={pickle_size}, header={header_size_with_padding}, size={file_size}")
            except Exception as e:
                pass

        pos += 1

    return offsets

def extract_asar(exe_path, output_path, offset_info):
    """Extract ASAR file from executable."""
    with open(exe_path, 'rb') as f:
        f.seek(offset_info['offset'])
        # Read the entire ASAR (header + file data)
        total_size = 16 + offset_info['header_size'] + offset_info['file_size']
        data = f.read(total_size)

        with open(output_path, 'wb') as out:
            out.write(data)

    print(f"Extracted {len(data)} bytes to {output_path}")
    return True

def main():
    exe_file = 'exe/mooer.exe'

    if not os.path.exists(exe_file):
        print(f"Error: {exe_file} not found")
        return 1

    print(f"Searching for ASAR archives in {exe_file}...")
    print("This may take a while due to the large file size (173 MB)...")

    # Read the entire file
    with open(exe_file, 'rb') as f:
        data = f.read()

    print(f"Read {len(data)} bytes")

    # Find ASAR offsets
    offsets = find_asar_offset(data)

    if not offsets:
        print("No ASAR archives found using signature search.")
        print("Trying alternative approach: searching for large JSON structures...")

        # Alternative: look for large JSON objects that might be ASAR metadata
        # (This is a fallback approach)
        return 1

    print(f"\nFound {len(offsets)} potential ASAR archive(s)")

    # Extract each found ASAR
    for i, offset_info in enumerate(offsets):
        output_file = f"app_{i}.asar"
        print(f"\n--- Extracting ASAR #{i} ---")
        try:
            extract_asar(exe_file, output_file, offset_info)
            print(f"Successfully extracted to {output_file}")
            print(f"Now run: npx @electron/asar extract {output_file} extracted_app_{i}/")
        except Exception as e:
            print(f"Failed to extract ASAR #{i}: {e}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
