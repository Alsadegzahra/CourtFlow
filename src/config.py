from pathlib import Path

# Project root = folder that contains input_videos/, outputs/, src/
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_VIDEOS_DIR = PROJECT_ROOT / "input_videos"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Standard output subfolders per match
MATCH_SUBFOLDERS = [
    "meta",
    "calibration",
    "tracks",
    "reports",
    "renders",
    "highlights",
]

def match_output_dir(match_id: str) -> Path:
    return OUTPUTS_DIR / match_id
