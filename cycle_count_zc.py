"""
Cycle counting via zero-crossings with hysteresis.

This utility opens a file picker, reads one or more time-series files using
`file_io.read_file_data`, computes **cycle counts** per channel using a
zero-crossing method with fixed hysteresis, and exports a tab-separated file
`cycle_counts.tsv` in the current working directory.

Notes
-----
- This counts **cycles**, not raw crossings. Internally, crossings between
  the positive and negative hysteresis states are counted and then divided
  by two (integer division) to obtain cycles.
- The "Time" column (case-insensitive) is ignored.
- Supported file types depend on `file_io.py` (.tem, .ltx, .ltd, .csv, .txt, .asc).
- Header columns for channels are taken from the **last** processed file
  (to preserve original behavior).
"""

from __future__ import annotations

import os
from typing import Iterable

import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog

import file_io

# ----------------------------
# Configuration
# ----------------------------
THRESHOLD: float = 10.0
"""Absolute hysteresis threshold for entering/leaving ±state."""

OUTPUT_FILENAME: str = "cycle_counts.tsv"
"""Output file name (tab-separated)."""


def count_cycles_zero_crossing(signal: Iterable[float], threshold: float = THRESHOLD) -> int:
    """
    Count cycles using zero-crossings with a three-state hysteresis.

    The signal must first exceed +threshold or -threshold to enter a state.
    A "crossing" is registered when the state flips directly between +1 and -1.
    The number of **cycles** is then defined as ``crossings // 2``.

    Parameters
    ----------
    signal : array_like
        1D sequence of samples.
    threshold : float, optional
        Absolute hysteresis threshold. Default is ``THRESHOLD``.

    Returns
    -------
    int
        Cycle count computed as half the number of sign flips between
        ±threshold states (integer division).

    Examples
    --------
    >>> count_cycles_zero_crossing([0, 11, -12, 13, -14])
    1
    >>> # Explanation: flips = 2  →  cycles = 2 // 2 = 1
    """
    x = np.asarray(signal)
    flips = 0
    state = 0  # 0 = neutral, +1 = above +threshold, -1 = below -threshold

    for value in x:
        if state == 0:
            if value > threshold:
                state = 1
            elif value < -threshold:
                state = -1
            # remain neutral otherwise

        elif state == 1:
            if value < -threshold:
                flips += 1
                state = -1

        else:  # state == -1
            if value > threshold:
                flips += 1
                state = 1

    cycles = flips // 2
    return int(cycles)


def process_files() -> None:
    """
    Open files, compute cycle counts per channel, and export a TSV summary.

    Behavior
    --------
    - Shows a GUI file picker to select one or more files.
    - For each file, reads data via `file_io.read_file_data`.
    - Ignores the "Time" column (case-insensitive).
    - Writes an output TSV named `cycle_counts.tsv` to the current directory,
      with columns: ["File", "Duration (s)", <channel names from last file>].
    """
    # Hide the main Tk window; show only the file dialog
    root = tk.Tk()
    root.withdraw()

    paths = filedialog.askopenfilenames(
        title="Select files",
        filetypes=[("All", "*.tem *.ltx *.ltd *.csv *.txt *.asc")],
    )

    if not paths:
        print("No file selected.")
        return

    rows: list[list[object]] = []

    for path in paths:
        try:
            df, base, duration, channel_names, fs = file_io.read_file_data(path)
        except Exception as exc:
            print(f"Failed to read {path}: {exc}")
            continue

        # One summary row per file:
        # filename, duration (s), then cycle counts per channel (excluding Time)
        row = [os.path.basename(path), round(float(duration[0]), 4)]
        channels = [c for c in df.columns if c.lower() != "time"]

        for col in channels:
            cycles = count_cycles_zero_crossing(df[col].values, threshold=THRESHOLD)
            row.append(cycles)

        rows.append(row)

    # Header based on the last processed file (preserves original behavior)
    channels = [c for c in df.columns if c.lower() != "time"]
    header = ["File", "Duration (s)"] + channels

    out_df = pd.DataFrame(rows, columns=header)
    out_path = os.path.join(os.getcwd(), OUTPUT_FILENAME)
    out_df.to_csv(out_path, sep="\t", index=False)

    print(f"\nResults exported to: {out_path}")


if __name__ == "__main__":
    process_files()
