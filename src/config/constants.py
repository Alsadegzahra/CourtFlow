"""
Court constants: padel dimensions, default ROI padding, schema versions.
Used by calibration, vision, and analytics.
"""
from __future__ import annotations

# Padel court dimensions (meters) – standard double
COURT_WIDTH_M = 10.0
COURT_HEIGHT_M = 20.0  # full length

# Default padding around court ROI in image (pixels) – for homography/ROI
DEFAULT_ROI_PADDING_PX = 20

# Schema versions for artifacts
CALIBRATION_SCHEMA_VERSION = "v1"
REPORT_SCHEMA_VERSION = "phase1_v1"
