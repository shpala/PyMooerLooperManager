#!/usr/bin/env python3
"""Compare two WAV files to identify differences."""

import sys
import os
from pathlib import Path

try:
    import numpy as np
    import scipy.io.wavfile as wav
except ImportError:
    print("ERROR: scipy is required for this script")
    print("Install with: pip install scipy")
    sys.exit(1)


def analyze_wav(filepath):
    """Analyze a WAV file and return its properties."""
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        return None

    try:
        sample_rate, data = wav.read(filepath)

        file_size = os.path.getsize(filepath)
        num_samples = len(data)

        # Determine if mono or stereo
        if len(data.shape) == 1:
            channels = 1
            shape_str = f"({num_samples},)"
        else:
            channels = data.shape[1]
            shape_str = f"({data.shape[0]}, {data.shape[1]})"

        duration = num_samples / sample_rate

        # Bit depth
        dtype = data.dtype
        if dtype == np.int16:
            bits_per_sample = 16
        elif dtype == np.int32:
            bits_per_sample = 32
        elif dtype == np.float32:
            bits_per_sample = 32
        elif dtype == np.float64:
            bits_per_sample = 64
        else:
            bits_per_sample = "Unknown"

        # Audio data statistics
        if channels == 1:
            min_val = np.min(data)
            max_val = np.max(data)
            mean_val = np.mean(data)
            rms = np.sqrt(np.mean(data.astype(float)**2))
        else:
            min_val = np.min(data, axis=0)
            max_val = np.max(data, axis=0)
            mean_val = np.mean(data, axis=0)
            rms = np.sqrt(np.mean(data.astype(float)**2, axis=0))

        return {
            'filepath': filepath,
            'file_size': file_size,
            'sample_rate': sample_rate,
            'channels': channels,
            'num_samples': num_samples,
            'duration': duration,
            'dtype': dtype,
            'bits_per_sample': bits_per_sample,
            'shape': shape_str,
            'min': min_val,
            'max': max_val,
            'mean': mean_val,
            'rms': rms,
            'data': data,
        }
    except Exception as e:
        print(f"ERROR analyzing {filepath}: {e}")
        return None


def print_analysis(info):
    """Print analysis information."""
    if info is None:
        return

    print(f"\nFile: {info['filepath']}")
    print(f"  File size: {info['file_size']:,} bytes ({info['file_size']/(1024**2):.2f} MB)")
    print(f"  Sample rate: {info['sample_rate']:,} Hz")
    print(f"  Channels: {info['channels']} ({'stereo' if info['channels'] == 2 else 'mono'})")
    print(f"  Samples: {info['num_samples']:,}")
    print(f"  Duration: {info['duration']:.3f} seconds ({info['duration']/60:.2f} minutes)")
    print(f"  Data type: {info['dtype']}")
    print(f"  Bits per sample: {info['bits_per_sample']}")
    print(f"  Array shape: {info['shape']}")

    if info['channels'] == 1:
        print(f"  Range: [{info['min']}, {info['max']}]")
        print(f"  Mean: {info['mean']:.2f}")
        print(f"  RMS: {info['rms']:.2f}")
    else:
        print(f"  Range: L[{info['min'][0]}, {info['max'][0]}], R[{info['min'][1]}, {info['max'][1]}]")
        print(f"  Mean: L={info['mean'][0]:.2f}, R={info['mean'][1]:.2f}")
        print(f"  RMS: L={info['rms'][0]:.2f}, R={info['rms'][1]:.2f}")


def compare_audio_data(info1, info2):
    """Compare audio data between two files."""
    print("\n" + "=" * 70)
    print("AUDIO DATA COMPARISON")
    print("=" * 70)

    data1 = info1['data']
    data2 = info2['data']

    # Check if shapes match
    if data1.shape != data2.shape:
        print(f"\n⚠ SHAPE MISMATCH:")
        print(f"  File 1: {data1.shape}")
        print(f"  File 2: {data2.shape}")

        # Try to compare up to the smaller length
        min_len = min(len(data1), len(data2))
        print(f"\n  Comparing first {min_len:,} samples...")
        data1_trimmed = data1[:min_len]
        data2_trimmed = data2[:min_len]
    else:
        print(f"\n✓ Shape matches: {data1.shape}")
        data1_trimmed = data1
        data2_trimmed = data2

    # Check if data is identical
    if np.array_equal(data1_trimmed, data2_trimmed):
        print("\n✓ AUDIO DATA IS IDENTICAL")
        return

    # Calculate differences
    print("\n⚠ AUDIO DATA IS DIFFERENT")

    # Convert to same type for comparison if needed
    if data1_trimmed.dtype != data2_trimmed.dtype:
        print(f"\n  Data types differ: {data1_trimmed.dtype} vs {data2_trimmed.dtype}")
        # Convert to float for comparison
        d1_float = data1_trimmed.astype(np.float64)
        d2_float = data2_trimmed.astype(np.float64)
    else:
        d1_float = data1_trimmed.astype(np.float64)
        d2_float = data2_trimmed.astype(np.float64)

    diff = d1_float - d2_float

    # Statistics on differences
    num_different = np.count_nonzero(diff)
    total_samples = diff.size
    pct_different = (num_different / total_samples) * 100

    print(f"\n  Different samples: {num_different:,} / {total_samples:,} ({pct_different:.2f}%)")

    if num_different > 0:
        print(f"  Max absolute difference: {np.max(np.abs(diff)):.2f}")
        print(f"  Mean absolute difference: {np.mean(np.abs(diff)):.2f}")
        print(f"  RMS difference: {np.sqrt(np.mean(diff**2)):.2f}")

        # Show first few differences
        diff_indices = np.where(diff.ravel() != 0)[0][:10]
        if len(diff_indices) > 0:
            print(f"\n  First few differences:")
            for idx in diff_indices[:5]:
                if len(data1_trimmed.shape) == 1:
                    print(f"    Sample {idx}: {data1_trimmed[idx]} vs {data2_trimmed[idx]} (diff: {diff[idx]:.2f})")
                else:
                    row = idx // data1_trimmed.shape[1]
                    col = idx % data1_trimmed.shape[1]
                    ch = 'L' if col == 0 else 'R'
                    print(f"    Sample {row} ({ch}): {data1_trimmed[row, col]} vs {data2_trimmed[row, col]} (diff: {diff[row, col]:.2f})")


def main():
    """Main comparison function."""
    if len(sys.argv) != 3:
        print("Usage: python compare_wav_files.py <file1.wav> <file2.wav>")
        print()
        print("Example:")
        print("  python compare_wav_files.py GL_LOOPFILE_03.wav track_3.wav")
        return 1

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    print("=" * 70)
    print("WAV FILE COMPARISON")
    print("=" * 70)

    # Analyze both files
    info1 = analyze_wav(file1)
    info2 = analyze_wav(file2)

    if info1 is None or info2 is None:
        return 1

    # Print analysis
    print_analysis(info1)
    print_analysis(info2)

    # Compare properties
    print("\n" + "=" * 70)
    print("PROPERTY COMPARISON")
    print("=" * 70)

    properties = [
        ('File size', 'file_size', 'bytes'),
        ('Sample rate', 'sample_rate', 'Hz'),
        ('Channels', 'channels', ''),
        ('Num samples', 'num_samples', ''),
        ('Duration', 'duration', 'seconds'),
        ('Bits per sample', 'bits_per_sample', 'bits'),
    ]

    for prop_name, prop_key, unit in properties:
        val1 = info1[prop_key]
        val2 = info2[prop_key]

        if val1 == val2:
            print(f"  ✓ {prop_name}: {val1:,} {unit}".strip())
        else:
            print(f"  ⚠ {prop_name}: {val1:,} vs {val2:,} {unit}".strip())
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                diff = val2 - val1
                pct = (diff / val1 * 100) if val1 != 0 else 0
                print(f"     Difference: {diff:+,} ({pct:+.2f}%)")

    # Compare audio data
    compare_audio_data(info1, info2)

    print("\n" + "=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
