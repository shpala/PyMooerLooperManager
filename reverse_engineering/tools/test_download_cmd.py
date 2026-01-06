#!/usr/bin/env python3
"""Test to understand download command structure."""

import sys
sys.path.insert(0, '/home/shpala/dev/gl100/src')

from gl100.protocol import GL100Protocol

# Create download commands for chunks 0, 1, 2, 3
for chunk in [0, 1, 2, 3]:
    cmd = GL100Protocol.create_download_command(slot=1, chunk=chunk)
    print(f"Chunk {chunk:3d}: {' '.join(f'{b:02x}' for b in cmd[:16])}")
