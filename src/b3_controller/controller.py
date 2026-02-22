# src/b3_controller/controller.py
from __future__ import annotations

import time

from src.b2_storage.db import list_matches_by_state, update_match
from src.pipeline.pipeline import run_pipeline_for_match, HighlightConfig


def process_one_match(match_row: dict) -> None:
    match_id = match_row["match_id"]

    try:
        # Pipeline will set PROCESSING too, but we keep this for clarity in logs
        update_match(match_id, state="PROCESSING")

        # Dummy highlight config (same as MVP defaults)
        cfg = HighlightConfig(
            clip_len_s=12.0,
            every_s=60.0,
            max_clips=10,
        )

        out = run_pipeline_for_match(match_id, cfg)
        update_match(match_id, state="DONE")
        print(f"[B3] DONE {match_id} -> {out}")

    except Exception as e:
        update_match(match_id, state="FAILED", last_error=str(e))
        print(f"[B3] FAILED {match_id}: {e}")


def run_loop(poll_sec: int = 2) -> None:
    print("[B3] Controller loop started. Watching for FINALIZED matches...")
    while True:
        finalized = list_matches_by_state("FINALIZED")
        for m in finalized:
            process_one_match(m)
        time.sleep(poll_sec)


if __name__ == "__main__":
    run_loop()