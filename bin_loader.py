#!/usr/bin/env python3
"""
Binary Sensor Data Loader – Complete Backend Edition
----------------------------------------------------
Reads .bin files (float32/float64, little/big endian) sampled at 10 kHz,
downsamples to a target frequency (e.g., 2.5 Hz) using block averaging,
and outputs JSON‑serializable data either via a Flask REST API or a JSON file.
"""

import struct
import os
import glob
from typing import List, Tuple, Dict, Literal


# ----------------------------------------------------------------------
# Core loader and downsampler
# ----------------------------------------------------------------------

def load_and_downsample(
    file_path: str,
    original_rate: float = 10000.0,
    target_rate: float = 2.5,
    data_type: Literal['float32', 'float64'] = 'float64',
    endian: Literal['little', 'big'] = 'little',
    method: Literal['average', 'decimate'] = 'average'
) -> Tuple[List[float], List[float]]:
    """
    Load a binary file and downsample the whole signal.

    Args:
        file_path: Path to the .bin file.
        original_rate: Original sampling frequency in Hz.
        target_rate: Desired output frequency in Hz.
        data_type: 'float32' (4 bytes) or 'float64' (8 bytes).
        endian: 'little' or 'big'.
        method: 'average' (recommended) or 'decimate'.

    Returns:
        (time_stamps, downsampled_values) – both lists of floats.
    """
    # Format parameters
    if data_type == 'float32':
        fmt_char = 'f'
        bytes_per_sample = 4
    elif data_type == 'float64':
        fmt_char = 'd'
        bytes_per_sample = 8
    else:
        raise ValueError("data_type must be 'float32' or 'float64'")

    endian_char = '<' if endian == 'little' else '>'

    # Read file
    with open(file_path, 'rb') as f:
        raw_data = f.read()

    file_size = len(raw_data)
    if file_size % bytes_per_sample != 0:
        raise ValueError(
            f"File size {file_size} is not a multiple of {bytes_per_sample} bytes"
        )

    num_samples = file_size // bytes_per_sample
    pack_fmt = f"{endian_char}{num_samples}{fmt_char}"
    samples = struct.unpack(pack_fmt, raw_data)   # tuple of floats

    # Downsampling parameters
    decimation = max(1, int(round(original_rate / target_rate)))
    output_interval = decimation / original_rate   # seconds per output point

    # Downsample
    downsampled = []
    if method == 'average':
        num_blocks = num_samples // decimation
        for i in range(num_blocks):
            start = i * decimation
            end = start + decimation
            block = samples[start:end]
            avg = sum(block) / decimation
            downsampled.append(avg)
    else:  # decimate
        downsampled = list(samples[::decimation])

    # Timestamps
    time_stamps = [i * output_interval for i in range(len(downsampled))]

    return time_stamps, downsampled


def process_folder(
    folder_path: str,
    original_rate: float = 10000.0,
    target_rate: float = 2.5,
    data_type: Literal['float32', 'float64'] = 'float64',
    endian: Literal['little', 'big'] = 'little',
    method: Literal['average', 'decimate'] = 'average',
    verbose: bool = False
) -> Dict[str, Tuple[List[float], List[float]]]:
    """
    Load and downsample every .bin file in a folder.

    Returns:
        Dictionary mapping filenames to (time_stamps, values) tuples.
    """
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    results = {}
    bin_files = glob.glob(os.path.join(folder_path, "*.bin"))
    if not bin_files:
        raise FileNotFoundError(f"No .bin files found in {folder_path}")

    for bin_path in bin_files:
        base_name = os.path.basename(bin_path)
        try:
            t, v = load_and_downsample(
                bin_path, original_rate, target_rate, data_type, endian, method
            )
            results[base_name] = (t, v)
            if verbose:
                print(f"OK: {base_name} -> {len(v)} points, duration {t[-1]:.2f} s")
        except Exception as e:
            if verbose:
                print(f"ERROR: {base_name} -> {e}")
            continue

    return results


def to_json_ready(data: Dict[str, Tuple[List[float], List[float]]]) -> dict:
    """
    Convert process_folder output into a JSON‑serializable dictionary.
    """
    out = {}
    for name, (t, v) in data.items():
        out[name] = {
            "time": t,
            "values": v,
            "duration": t[-1] if t else 0.0,
            "num_points": len(t)
        }
    return out


# ----------------------------------------------------------------------
# Optional helper: convert .txt to .bin (useful if you only have text files)
# ----------------------------------------------------------------------

def txt_to_bin(
    txt_path: str,
    bin_path: str,
    data_type: Literal['float32', 'float64'] = 'float64',
    endian: Literal['little', 'big'] = 'little'
) -> None:
    """
    Convert a text file with one float per line to a binary file.
    """
    with open(txt_path, 'r') as f:
        lines = [float(line.strip()) for line in f if line.strip()]

    fmt_char = 'd' if data_type == 'float64' else 'f'
    endian_char = '<' if endian == 'little' else '>'
    fmt = endian_char + fmt_char

    with open(bin_path, 'wb') as f:
        for val in lines:
            f.write(struct.pack(fmt, val))


# ----------------------------------------------------------------------
# Main – either start a Flask server or save to JSON
# ----------------------------------------------------------------------

if __name__ == "__main__":
    # ==================== CONFIGURATION ====================
    DATA_FOLDER = r""
    OUTPUT_JSON = r""
    TARGET_RATE = 2.5          # Hz – final display rate
    ORIG_RATE = 10000.0        # 10 kHz
    # =======================================================

    # Optionally convert .txt files to .bin (uncomment if needed)
    # for txt_file in glob.glob(os.path.join(DATA_FOLDER, "*.txt")):
    #     bin_file = txt_file.replace('.txt', '.bin')
    #     if not os.path.exists(bin_file):
    #         print(f"Converting {os.path.basename(txt_file)} -> {os.path.basename(bin_file)}")
    #         txt_to_bin(txt_file, bin_file, data_type='float64', endian='little')

    try:
        # Try to import Flask – if available, start a REST API server
        from flask import Flask, jsonify, request

        app = Flask(__name__)

        @app.route('/api/signals', methods=['GET'])
        def get_signals():
            try:
                target = float(request.args.get('target_rate', TARGET_RATE))
                all_data = process_folder(
                    DATA_FOLDER,
                    original_rate=ORIG_RATE,
                    target_rate=target,
                    data_type='float64',
                    endian='little',
                    method='average',
                    verbose=False
                )
                json_ready = to_json_ready(all_data)
                return jsonify(json_ready)
            except FileNotFoundError as e:
                return jsonify({"error": f"Data folder not found: {str(e)}"}), 404
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        print("Starting Flask server...")
        print(f"Access the API at: http://localhost:5000/api/signals")
        app.run(debug=True, host='0.0.0.0', port=5000)

    except ImportError:
        # Flask not installed – fallback to saving a JSON file
        print("Flask not installed. Falling back to JSON file output.")
        print("Install Flask with: pip install flask")
        print()

        all_data = process_folder(DATA_FOLDER, target_rate=TARGET_RATE, verbose=True)
        json_ready = to_json_ready(all_data)

        # Ensure the output directory exists
        output_dir = os.path.dirname(OUTPUT_JSON)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        import json
        with open(OUTPUT_JSON, "w") as f:
            json.dump(json_ready, f, indent=2)

        print(f"\nData saved to: {OUTPUT_JSON}")
        print("\n=== Summary ===")
        for name, info in json_ready.items():
            print(f"{name}: {info['num_points']} points, {info['duration']:.2f} s")