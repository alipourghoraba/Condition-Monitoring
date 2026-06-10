Binary Sensor Data Loader – Backend Module
Purpose
This module reads raw binary files (.bin) containing sensor data (current, vibration, etc.) sampled at 10 kHz (10,000 samples/second). It downsamples the entire recording to a much lower frequency (e.g., 2.5 Hz) using block averaging (anti‑aliasing). The output is lightweight, JSON‑serializable, and ready to be sent to a web frontend for real‑time plotting.
Input / Output
Input
Binary files (.bin) – each file contains 32‑bit or 64‑bit floating‑point numbers (float32 / float64), little‑endian or big‑endian.

Path to the folder containing the .bin files.

Original sampling rate (default 10,000 Hz).

Target output rate (default 2.5 Hz).

Output
A Python dictionary (plain primitives) that is directly JSON‑serializable: 
