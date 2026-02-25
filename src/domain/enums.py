"""
Status enums and schema versions used across pipeline and calibration.
"""
from __future__ import annotations

from enum import Enum


class CalibrationStatus(str, Enum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


class MatchState(str, Enum):
    CREATED = "CREATED"
    RECORDING = "RECORDING"
    FINALIZING = "FINALIZING"
    FINALIZED = "FINALIZED"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"
