# cycle-count-zc — Cycle Counting via Zero-Crossings (Hysteresis)

Small utility for counting **cycles** in time-series signals using a zero-crossing method with fixed hysteresis.  
It reuses your existing `file_io.py` to read Lynx files (`.tem`, `.ltx`, `.ltd`) and text files (`.csv`, `.txt`, `.asc`) and writes a tab-separated summary (`cycle_counts.tsv`).

## What it does
- Opens a file picker (GUI) to select one or more input files.
- For each file, counts **cycles** per channel using zero-crossings with a three-state hysteresis.
- Ignores the column named `Time` (case-insensitive).
- Produces a per-file summary with columns: `File`, `Duration (s)`, and one column per channel.
- Saves the result to `cycle_counts.tsv` in the current working directory.

> Terminology: this tool reports **cycles** (not raw crossing flips). Internally we count sign flips between the positive and negative hysteresis states and then compute `cycles = flips // 2`.

## How it works (algorithm)
Three-state hysteresis state machine:

- State 0 (neutral): the signal has not exceeded `+THRESHOLD` or `−THRESHOLD`.
- State +1: the signal is above `+THRESHOLD`.
- State −1: the signal is below `−THRESHOLD`.

A “flip” is registered only when the state switches directly between +1 and −1 (or −1 and +1).  
The cycle count equals `flips // 2`. This reduces false counts due to small oscillations around zero.

Default threshold:
- `THRESHOLD = 10.0` (change inside `cycle_count_zc.py` if you need a different value).

## Input formats
Supported formats depend on `file_io.py`:
- Lynx via COM (Windows): `.tem`, `.ltx`, `.ltd`
- Text: `.csv`, `.txt`, `.asc`

On non-Windows systems, Lynx/COM formats may not be available; use text formats.

## Output
- File: `cycle_counts.tsv` (tab-separated).
- Columns: `File`, `Duration (s)`, plus one column for each channel (excluding `Time`).
- One row per selected input file.

Note: If files contain different channel sets, the header is derived from the **last** processed file (preserves original behavior of your earlier script).

## Installation
1) Create and activate a virtual environment  
Windows:
- `python -m venv .venv`
- `.venv\Scripts\activate`

macOS / Linux:
- `python3 -m venv .venv`
- `source .venv/bin/activate`

2) Install dependencies
- `pip install -r requirements.txt`

Tip (Windows/Lynx): `pywin32` is required only if you will read `.tem/.ltx/.ltd` via COM.

## Usage
- Run: `python cycle_count_zc.py`  
- Select one or more files in the dialog.  
- The results are saved to `./cycle_counts.tsv`.

## Configuration
- Hysteresis threshold: edit the constant `THRESHOLD` at the top of `cycle_count_zc.py`.
- Output filename: edit `OUTPUT_FILENAME` if you want a different name or format.
- Columns language: the script currently uses English headers in the output (`File`, `Duration (s)`); channel names are taken from your data.

## Known limitations and scope
- This is a **simple** cycle estimator. It does not replace Rainflow counting for fatigue analysis.
- Cycle counts depend on the chosen `THRESHOLD`; choose a value that reflects your noise level and application.
- Header comes from the last processed file; ensure consistent channel sets across files if you need a unified table.

## Suggested repository structure
- `cycle_count_zc.py`
- `file_io.py`
- `requirements.txt`
- `README.md`
- `.gitignore`
- `tests/` (optional)

## Troubleshooting
- “Failed to read …”: confirm the file type is supported by `file_io.py` and that dependencies are installed (e.g., `pywin32` on Windows for Lynx).
- Empty or missing output: verify that at least one non-`Time` channel is present and that the selected files are valid.
- Permission issues on output: ensure `cycle_counts.tsv` is not open in another program.

## License
MIT Licens.

## Credits
Developed by Brenick Resende Assumpção.  
This utility is part of the same ecosystem as SigProc and reuses the shared `file_io.py`.

## Nota em português
Este utilitário **conta ciclos** (via zero-crossings com histerese), não cruzamentos brutos. O limiar (`THRESHOLD`) controla a sensibilidade do contador; ajuste conforme o nível de ruído do seu sinal. Para análises de fadiga, utilize contagem Rainflow.
