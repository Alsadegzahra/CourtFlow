"""
Backward compatibility: re-export from domain/report_contract.
Prefer: from src.domain.report_contract import empty_tracks, empty_report
"""
from __future__ import annotations

from src.domain.report_contract import empty_tracks, empty_report

__all__ = ["empty_tracks", "empty_report"]
