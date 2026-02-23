## B5b – Coordinate Conversion (Pixel → Court)

- **Responsibility**: Use `CalibrationHomography` to convert pixel coordinates from `TrackRecord` entries into court-space coordinates (`x_court`, `y_court`).
- **Main code**: `coords.py`

### Tools / Libraries

- Likely: NumPy or simple matrix math utilities
- JSON I/O helpers from `src.common.io_utils`

### Models / Intelligence

- _(Primarily geometric logic — no heavy ML expected here.)_

