# GoPro Sequential Exporter

Automates **GoPro Player** on Windows to export GoPro `.360` videos as reframed MP4 files, **one at a time**. Uses the Windows `.360` file association to open each clip, drives the Player interface, waits for export to complete, closes Player, then moves to the next clip.

## Requirements

- Windows 11 with GoPro Player installed and `.360` files associated with it.
- Python 3.9+ and dependencies:

  ```cmd
  py -m pip install pyautogui pygetwindow pyperclip pywin32
  ```

- Keep `gopro_rating_title.png` alongside `gopro_sequential_export.py` for optional rating-popup detection.
- Use the same display resolution and scaling as when the click coordinates were calibrated (2560 × 1440). Note that you may need to fine tune the coordinates for you display.
- Close GoPro Player before starting; avoid using the mouse or keyboard while it runs.

## Usage

Test **one pending clip** (default):

```cmd
py gopro_sequential_export.py "D:\Videos\Trip\MAX2" "D:\Videos\Trip\MAX2\rf"
```

Export **all pending clips**:

```cmd
py gopro_sequential_export.py "D:\Videos\Trip\MAX2" "D:\Videos\Trip\MAX2\rf" --all
```

Useful options:

| Option | Description |
|---|---|
| `--keep-direction-lock` | Do not turn off Direction Lock |
| `--keep-horizon-level` | Do not turn off Horizon Level |
| `--stall-minutes 30` | Stop if the output file has not appeared or grown for 30 minutes (default: 15) |
| `--restart-pause 5` | Pause 5 seconds between Player sessions (default: 3) |
| `--debug-clicks` | Preview mouse positions without clicking or exporting |

## Behavior and safety

- Output names are `<original_stem>_reframed.mp4`, e.g. `GS010018_reframed.mp4`.
- Existing MP4 outputs are **skipped**; to re-export a clip with different settings, move or rename its existing output first.
- While exporting, Player writes `<original_stem>_reframed.partial.mp4`; it is renamed to the final name only after the export completes. A leftover `.partial.mp4` from an interrupted run is deleted and re-exported on the next run.
- Export completion requires a new Explorer window on the output folder (opened by Player) plus a stable file size; only that window is closed.
- Keep `sync_gopro_timestamps.py` alongside the exporter; it supplies the timestamp copy.
- By default, the script clicks to turn **Direction Lock** and **Horizon Level** off; use the options above to leave either enabled.
- GoPro Player remembers export settings such as **4K, HEVC, and quality**; configure them in the application first.
- Export duration is not capped, but lack of output-file growth triggers a stall error. A failure stops the batch and attempts to save `gopro_export_error.png` alongside the script.
- Move the mouse to the **upper-left corner** for PyAutoGUI's emergency stop.
- The script does not intentionally delete source files. Backups are recommended because it automates GUI clicks.
- Exported MP4 files inherit the original `.360` file's creation and modification times.
- Set the output resolution manually before export, it uses that resolution during export.
- Set the export window small, without advanced options visible. Otherwise mouse click will not hit the correct button.

## Fixing timestamps of existing exports

`sync_gopro_timestamps.py` copies the creation and modification times from each `.360` clip to its exported MP4. The exporter does this automatically; run the script separately for MP4s exported manually or by an older version. Give the `.360` folder first, then the MP4 folder. Without `--apply` it only shows what would change:

```cmd
py sync_gopro_timestamps.py "D:\Videos\Trip\MAX2" "D:\Videos\Trip\MAX2\rf"
py sync_gopro_timestamps.py "D:\Videos\Trip\MAX2" "D:\Videos\Trip\MAX2\rf" --apply
```

- An MP4 matches a clip when it is named `<original_stem>.mp4` or `<original_stem>_<anything>.mp4`, e.g. `GS010018_reframed.mp4` or `GS010018_reframed_nohl.mp4`. `.partial.mp4` files are skipped.
- `--suffix _reframed_nohl.mp4` limits matching to one naming pattern.
- Only `.mp4` files are modified. If the first folder contains no `.360` files (e.g. the arguments are swapped), the script stops without changing anything.
