#!/usr/bin/env python3
"""
Advanced ASAR extraction - scans for actual ASAR binary structure
"""

import struct
import os
import json

def is_valid_asar_header(data, offset):
    """
    Check if offset points to a valid ASAR header.
    ASAR format:
    - 4 bytes: pickle size (should be 4)
    - 4 bytes: header size (JSON size + padding)
    - 8 bytes: file size (total data size)
    - N bytes: JSON header (should start with {)
    """
    try:
        if offset + 16 > len(data):
            return None

        pickle_size = struct.unpack('<I', data[offset:offset+4])[0]
        header_size = struct.unpack('<I', data[offset+4:offset+8])[0]
        file_size = struct.unpack('<Q', data[offset+8:offset+16])[0]

        # Pickle size should always be 4 for ASAR
        if pickle_size != 4:
            return None

        # Sanity check sizes
        if header_size < 10 or header_size > 50_000_000:
            return None
        if file_size < 100 or file_size > 500_000_000:
            return None

        # Check if JSON starts right after header
        json_offset = offset + 16
        if json_offset + 10 > len(data):
            return None

        # JSON should start with '{'
        if data[json_offset:json_offset+1] != b'{':
            return None

        # Try to find closing } within reasonable distance
        json_sample = data[json_offset:json_offset+min(1000, header_size)]
        try:
            json_str = json_sample.decode('utf-8', errors='strict')
            if not json_str.startswith('{'):
                return None
        except:
            return None

        return {
            'offset': offset,
            'pickle_size': pickle_size,
            'header_size': header_size,
            'file_size': file_size,
            'total_size': 16 + header_size + file_size,
            'json_offset': json_offset
        }
    except:
        return None

def scan_for_asar(data, step=4):
    """Scan data for ASAR archives."""
    print(f"Scanning {len(data):,} bytes (step={step})...")
    found = []

    for offset in range(0, len(data) - 16, step):
        if offset % 10_000_000 == 0:
            print(f"  Progress: {offset:,} / {len(data):,} ({offset*100//len(data)}%)")

        asar_info = is_valid_asar_header(data, offset)
        if asar_info:
            print(f"\n✓ Found ASAR at offset {offset:,} (0x{offset:X})")
            print(f"  Pickle size: {asar_info['pickle_size']}")
            print(f"  Header size: {asar_info['header_size']:,}")
            print(f"  File size: {asar_info['file_size']:,}")
            print(f"  Total size: {asar_info['total_size']:,}")

            # Show JSON preview
            json_start = asar_info['json_offset']
            json_preview = data[json_start:json_start+200].decode('utf-8', errors='ignore')
            print(f"  JSON preview: {json_preview[:100]}")

            found.append(asar_info)

            # Skip ahead past this ASAR
            offset += asar_info['total_size']

    return found

def extract_asar(exe_path, asar_info, output_path):
    """Extract ASAR to file."""
    print(f"\nExtracting ASAR from offset {asar_info['offset']:,}...")

    with open(exe_path, 'rb') as f:
        f.seek(asar_info['offset'])
        data = f.read(asar_info['total_size'])

    with open(output_path, 'wb') as f:
        f.write(data)

    print(f"✓ Wrote {len(data):,} bytes to {output_path}")
    return True

def main():
    exe_file = 'exe/mooer.exe'

    if not os.path.exists(exe_file):
        print(f"Error: {exe_file} not found")
        return 1

    print(f"Reading {exe_file}...")
    with open(exe_file, 'rb') as f:
        data = f.read()

    print(f"Read {len(data):,} bytes ({len(data)/1024/1024:.1f} MB)\n")

    # Scan with 4-byte alignment (faster, might miss some)
    archives = scan_for_asar(data, step=4)

    if not archives:
        print("\n❌ No ASAR archives found")
        return 1

    print(f"\n✓ Found {len(archives)} ASAR archive(s)\n")

    # Extract each archive
    for i, asar_info in enumerate(archives):
        output_file = f"app_v3_{i}.asar"
        try:
            extract_asar(exe_file, asar_info, output_file)
            print(f"  To unpack: npx @electron/asar extract {output_file} extracted_app_{i}/\n")
        except Exception as e:
            print(f"❌ Failed to extract archive #{i}: {e}\n")

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
