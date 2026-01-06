#!/usr/bin/env python3
"""
Find and extract ASAR archives from mooer.exe
Improved version with better pattern matching
"""

import struct
import os

def find_json_start(data, start_pos, max_search=1000):
    """Find the start of JSON after potential ASAR header."""
    for i in range(start_pos, min(start_pos + max_search, len(data))):
        if data[i:i+1] == b'{':
            return i
    return None

def find_asar_archives(data):
    """Search for ASAR archives by looking for JSON metadata."""
    print(f"Searching {len(data)} bytes for ASAR archives...")

    offsets = []
    pos = 0

    # Search for JSON that looks like ASAR metadata
    # ASAR metadata typically starts with {"files":{"
    search_patterns = [
        b'{"files":{',
        b'{"files": {',
    ]

    for pattern in search_patterns:
        pos = 0
        while True:
            pos = data.find(pattern, pos)
            if pos == -1:
                break

            # Check if there's a valid ASAR header before this JSON
            # ASAR header is 16 bytes before the JSON:
            # 4 bytes pickle size + 4 bytes header size + 8 bytes file size
            if pos >= 16:
                try:
                    header_offset = pos - 16
                    pickle_size = struct.unpack('<I', data[header_offset:header_offset+4])[0]
                    header_size = struct.unpack('<I', data[header_offset+4:header_offset+8])[0]
                    file_size = struct.unpack('<Q', data[header_offset+8:header_offset+16])[0]

                    # Sanity check the sizes
                    if (0 < pickle_size < 100000 and
                        0 < header_size < 50000000 and
                        0 < file_size < 500000000):

                        # Verify that JSON actually continues
                        json_sample = data[pos:pos+200].decode('utf-8', errors='ignore')
                        if '"files"' in json_sample and '{' in json_sample:
                            offsets.append({
                                'offset': header_offset,
                                'pickle_size': pickle_size,
                                'header_size': header_size,
                                'file_size': file_size,
                                'json_start': pos,
                                'pattern': pattern.decode()
                            })
                            print(f"\nFound potential ASAR at offset {header_offset} (0x{header_offset:X})")
                            print(f"  Pickle size: {pickle_size}")
                            print(f"  Header size: {header_size}")
                            print(f"  File size: {file_size}")
                            print(f"  Total size: {16 + header_size + file_size} bytes")
                            print(f"  JSON starts at: {pos} (0x{pos:X})")
                            print(f"  JSON preview: {json_sample[:100]}")
                except Exception as e:
                    pass

            # Also record positions without header for manual inspection
            elif pos >= 0:
                json_sample = data[pos:pos+100].decode('utf-8', errors='ignore')
                if '"files"' in json_sample and len(json_sample) > 50:
                    print(f"\nFound JSON at {pos} (0x{pos:X}) without valid ASAR header:")
                    print(f"  {json_sample[:80]}")

            pos += 1

    return offsets

def extract_asar(data, asar_info, output_path):
    """Extract ASAR archive to file."""
    offset = asar_info['offset']
    total_size = 16 + asar_info['header_size'] + asar_info['file_size']

    print(f"\nExtracting {total_size} bytes from offset {offset} to {output_path}")

    asar_data = data[offset:offset+total_size]

    with open(output_path, 'wb') as f:
        f.write(asar_data)

    print(f"Wrote {len(asar_data)} bytes to {output_path}")
    return True

def main():
    exe_file = 'exe/mooer.exe'

    if not os.path.exists(exe_file):
        print(f"Error: {exe_file} not found")
        return 1

    print(f"Reading {exe_file}...")
    with open(exe_file, 'rb') as f:
        data = f.read()

    print(f"Read {len(data)} bytes ({len(data)/1024/1024:.1f} MB)")

    # Find ASAR archives
    archives = find_asar_archives(data)

    if not archives:
        print("\n❌ No valid ASAR archives found")
        return 1

    print(f"\n✓ Found {len(archives)} potential ASAR archive(s)")

    # Extract each archive
    for i, asar_info in enumerate(archives):
        output_file = f"app_{i}.asar"
        try:
            extract_asar(data, asar_info, output_file)
            print(f"\n✓ Successfully extracted to {output_file}")
            print(f"  Next: npx @electron/asar extract {output_file} extracted_app_{i}/")
        except Exception as e:
            print(f"\n❌ Failed to extract archive #{i}: {e}")

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
