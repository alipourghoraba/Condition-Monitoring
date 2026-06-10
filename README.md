# Binary Sensor Data Loader – Backend Module

A lightweight Python backend module for reading raw binary sensor files (`.bin`), downsampling them with block averaging, and preparing JSON-serializable output for web frontends and dashboards.

## Purpose

This module reads raw binary sensor recordings such as current, vibration, or other high-frequency measurements sampled at **10 kHz** (`10,000 samples/second`).  
It then downsamples the data to a much lower frequency, such as **2.5 Hz**, using **block averaging** as an anti-aliasing method.

The result is a small, clean dataset that can be sent directly to a frontend for plotting or stored as JSON for later use.

## Input and Output

### Input

- Binary files (`.bin`) containing 32-bit or 64-bit floating-point values
- Little-endian or big-endian byte order
- A folder path containing the `.bin` files
- Original sampling rate, default: `10000.0`
- Target output rate, default: `2.5`

### Output

The module returns a Python dictionary made only of plain primitives, so it is directly JSON-serializable:

```json
{
  "filename1.bin": {
    "time": [0.0, 0.4, 0.8, ..., 98.8],
    "values": [0.123, -0.456, 0.789, ...],
    "duration": 98.8,
    "num_points": 248
  },
  "filename2.bin": { ... }
}
```

#### Field descriptions

- **time** – evenly spaced timestamps in seconds
- **values** – downsampled signal values
- **duration** – total recording duration, equal to the last timestamp
- **num_points** – number of downsampled points

## Main Functions

### `load_and_downsample(file_path, original_rate, target_rate, data_type, endian, method)`

Loads a single `.bin` file, downsamples it, and returns `(times, values)`.

### `process_folder(folder_path, ...)`

Processes all `.bin` files in a folder and returns:

```python
{
    "file1.bin": (times, values),
    "file2.bin": (times, values)
}
```

### `to_json_ready(data)`

Converts the output of `process_folder` into a JSON-friendly dictionary:

```python
{
    "file1.bin": {
        "time": [...],
        "values": [...],
        "duration": ...,
        "num_points": ...
    }
}
```

### `txt_to_bin(txt_path, bin_path, data_type, endian)`

Optional helper that converts a text file containing one float per line into binary format.  
This is useful for testing and quick data preparation.

## Parameters

| Parameter | Type | Default | Description |
|---|---:|---:|---|
| `original_rate` | float | `10000.0` | Original sampling frequency in Hz |
| `target_rate` | float | `2.5` | Desired output frequency in Hz |
| `data_type` | str | `'float64'` | Either `'float32'` or `'float64'` |
| `endian` | str | `'little'` | Either `'little'` or `'big'` |
| `method` | str | `'average'` | `'average'` for anti-aliasing, or `'decimate'` for simple subsampling |
| `verbose` | bool | `False` | Prints progress and error messages when enabled |

## Step-by-Step Usage for Backend Developers

### 1. Place the module in your project

Copy the complete code into a file named:

```bash
sensor_loader.py
```

### 2. Install dependencies

The module works with the Python standard library only.

If you want to use the Flask REST API, install Flask:

```bash
pip install flask
```

If Flask is not installed, the script automatically falls back to saving a JSON file.

### 3. Prepare your data

Ensure your raw sensor files are stored in a folder such as:

```text
D:\Fault_Detector\Technical\Sample_Data\archive_1779185499_1779185509\raw
```

The files should have the `.bin` extension.

If you only have `.txt` files containing one float per line, you can uncomment the conversion block inside:

```python
if __name__ == "__main__":
```

This will convert the text files into `.bin` files on the first run.

### 4. Configure the script

Open `sensor_loader.py` and edit the configuration section near the bottom:

```python
DATA_FOLDER = r"D:\Fault_Detector\Technical\Sample_Data\archive_1779185499_1779185509\raw"
OUTPUT_JSON = r"D:\Fault_Detector\Technical\Sample_Data\sensor_data.json"
TARGET_RATE = 2.5
ORIG_RATE = 10000.0
```

Update `DATA_FOLDER` and `OUTPUT_JSON` to match your local paths.

### 5. Run the script

From the command line:

```bash
python sensor_loader.py
```

### 6. What happens when you run it?

- If **Flask is installed**, a web server starts at:

  ```text
  http://localhost:5000/api/signals
  ```

  You can optionally change the target rate using a query parameter:

  ```text
  http://localhost:5000/api/signals?target_rate=3.0
  ```

- If **Flask is not installed**, the script processes all `.bin` files, saves the downsampled data as `sensor_data.json` at the configured path, and prints a summary.

### 7. Use the output in your backend

#### Option A – JSON file

After running the script, a JSON file is created. Your backend can load it like this:

```python
import json

with open("sensor_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# data is now ready to send to the frontend
```

#### Option B – Flask endpoint

If the Flask server is running, your frontend can fetch the data directly:

```javascript
fetch("http://localhost:5000/api/signals")
  .then((response) => response.json())
  .then((data) => console.log(data));
```

### 8. Integrate into your production backend

You can copy the functions `load_and_downsample`, `process_folder`, and `to_json_ready` into your existing codebase, or keep the module as a separate file.

Example:

```python
from sensor_loader import process_folder, to_json_ready

all_data = process_folder("/path/to/bin/files", target_rate=2.5)
json_data = to_json_ready(all_data)

# send json_data as a JSON response
```

## Important Notes

- **Memory efficient** – The whole binary file is read at once, but the downsampled output is very small, making it lightweight for frontend plotting.
- **Error resilient** – Corrupt or wrongly formatted files are skipped. Errors are printed only when `verbose=True`.
- **Pure Python** – Only standard library modules such as `struct`, `os`, `glob`, and `json` are required. Flask is optional.
- **Direct JSON** – The output uses only Python primitives (`list`, `dict`, `float`, `int`, `str`), so `json.dumps()` works without a custom encoder.
- **Anti-aliasing** – Block averaging preserves the overall trend and reduces high-frequency noise, making it suitable for low-frequency visualization.

## Example Folder Output

When the module processes a folder, each file becomes a JSON-ready object:

```python
{
    "sensor1.bin": {
        "time": [0.0, 0.4, 0.8, 1.2],
        "values": [0.15, 0.10, 0.08, 0.12],
        "duration": 1.2,
        "num_points": 4
    }
}
```

