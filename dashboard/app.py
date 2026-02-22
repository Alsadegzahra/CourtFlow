from __future__ import annotations

from pathlib import Path
import json
import streamlit as st

from src.b2_storage.db import list_matches, get_match, list_artifacts
from src.common.config import PROJECT_ROOT, DATA_DIR


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def safe_exists(p: Path) -> bool:
    try:
        return p.exists()
    except Exception:
        return False


st.set_page_config(page_title="CourtFlow Dashboard", layout="wide")
st.title("CourtFlow — MVP Dashboard (DB + Outputs Viewer)")

st.caption(f"Project root: {PROJECT_ROOT}")
st.caption(f"Data dir: {DATA_DIR}")

# ---- Load matches from DB ----
matches = list_matches(limit=200)
if not matches:
    st.warning("No matches found in SQLite. Create a match and finalize it first.")
    st.stop()

match_ids = [m["match_id"] for m in matches]
selected_match_id = st.sidebar.selectbox("Select a match", match_ids)

match = get_match(selected_match_id)
if not match:
    st.error(f"Match not found: {selected_match_id}")
    st.stop()

output_dir = Path(match["output_dir"])
source_uri = Path(match["source_uri"]) if match["source_type"] == "FILE" else None

st.sidebar.markdown("---")
st.sidebar.write("Selected match_id:")
st.sidebar.code(selected_match_id)
st.sidebar.write("Output dir:")
st.sidebar.code(str(output_dir))

# ---- Header metrics ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Match ID", match.get("match_id", "—"))
c2.metric("Court ID", match.get("court_id", "—"))
c3.metric("State", match.get("state", "—"))
c4.metric("Source Type", match.get("source_type", "—"))

c5, c6, c7, c8 = st.columns(4)
c5.metric("Started", match.get("started_at", "—") or "—")
c6.metric("Ended", match.get("ended_at", "—") or "—")
c7.metric("Created", match.get("created_at", "—") or "—")
c8.metric("Updated", match.get("updated_at", "—") or "—")

if match.get("last_error"):
    st.error(f"Last error: {match['last_error']}")

st.markdown("---")

# ---- Paths to common files ----
meta_path = output_dir / "meta" / "meta.json"
report_path = output_dir / "reports" / "report.json"
tracks_path = output_dir / "tracks" / "tracks.json"
calib_path = output_dir / "calibration" / "homography.json"

highlights_dir = output_dir / "highlights"
highlights_mp4 = highlights_dir / "highlights.mp4"
highlights_clips_dir = highlights_dir / "clips"
renders_dir = output_dir / "renders"

# ---- Source Video ----
st.subheader("Source Video")
if match["source_type"] == "FILE":
    if source_uri and source_uri.exists():
        st.video(str(source_uri))
        st.caption(str(source_uri))
    else:
        st.warning(f"Source file not found: {source_uri}")
else:
    st.info(f"Source type is {match['source_type']} (URI: {match['source_uri']}). MVP viewer only plays FILE sources.")

st.markdown("---")

# ---- Meta ----
st.subheader("Meta (meta/meta.json)")
if meta_path.exists():
    meta = read_json(meta_path)
    st.json(meta)
else:
    st.info("meta/meta.json not found yet (pipeline may not have run).")

# ---- Calibration ----
st.subheader("Calibration (calibration/homography.json)")
if calib_path.exists():
    st.success("Calibration found ✅")
    with st.expander("View calibration/homography.json"):
        st.json(read_json(calib_path))
else:
    st.info("No calibration file yet (expected later).")

st.markdown("---")

# ---- Tracks ----
st.subheader("Tracks (tracks/tracks.json)")
if tracks_path.exists():
    try:
        tracks = read_json(tracks_path)
        if isinstance(tracks, list):
            st.write(f"Track records: **{len(tracks)}**")
            if len(tracks) > 0:
                st.dataframe(tracks[:50])
            else:
                st.info("tracks.json is empty (stub).")
        else:
            st.json(tracks)
    except Exception as e:
        st.warning(f"Could not read tracks.json: {e}")
else:
    st.info("tracks/tracks.json not found (stub stage).")

st.markdown("---")

# ---- Report ----
st.subheader("Report (reports/report.json)")
report = None
if report_path.exists():
    report = read_json(report_path)
    st.json(report)
else:
    st.info("reports/report.json not found yet (pipeline may not have run).")

st.markdown("---")

# ---- Highlights ----
st.subheader("Highlights")

if highlights_mp4.exists():
    st.success("Highlights video found ✅")
    st.video(str(highlights_mp4))
    st.caption(str(highlights_mp4))
else:
    st.info("No highlights/highlights.mp4 yet.")

# If report has exported clips, show them
exported = []
if report is not None and isinstance(report, dict):
    exported = report.get("exported_highlights", []) or []

if exported:
    st.write(f"Exported highlight clips: **{len(exported)}**")
    for item in exported:
        filename = item.get("file")
        reason = item.get("reason", "—")
        start = item.get("start", "—")
        end = item.get("end", "—")

        clip_path = highlights_clips_dir / filename if filename else None
        st.markdown(f"**{filename}**  \nReason: `{reason}` | {start}s → {end}s")
        if clip_path and clip_path.exists():
            st.video(str(clip_path))
        else:
            st.warning(f"Missing clip file: {clip_path}")
else:
    # fallback: show any mp4 clips in highlights/clips
    if highlights_clips_dir.exists():
        mp4s = sorted(highlights_clips_dir.glob("*.mp4"))
        if mp4s:
            st.info("Showing mp4 clips found in highlights/clips/")
            for clip_path in mp4s:
                st.caption(clip_path.name)
                st.video(str(clip_path))
        else:
            st.info("No highlight clips found in highlights/clips/.")
    else:
        st.info("No highlights/clips folder found (it should exist after highlight export).")

st.markdown("---")

# ---- Renders ----
st.subheader("Renders (renders/)")
if renders_dir.exists():
    render_files = sorted([p for p in renders_dir.iterdir() if p.is_file()])
    if not render_files:
        st.info("No renders yet.")
    else:
        for p in render_files:
            st.write(f"- {p.name}")
            if p.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                st.image(str(p), caption=p.name, use_container_width=True)
            elif p.suffix.lower() in [".mp4", ".mov"]:
                st.video(str(p))
else:
    st.info("No renders folder found (it should exist).")

st.markdown("---")

# ---- Artifacts from DB ----
st.subheader("Artifacts (from SQLite)")
arts = list_artifacts(selected_match_id)
if arts:
    # Make it readable: newest first
    st.dataframe(
        [
            {
                "type": a["type"],
                "status": a["status"],
                "path": a["path"],
                "size_bytes": a.get("size_bytes"),
                "created_at": a.get("created_at"),
            }
            for a in arts
        ]
    )
else:
    st.info("No artifacts registered in DB for this match yet.")

st.caption("MVP dashboard = viewer + debugging tool. As tracking/analytics get implemented, this becomes your verification UI.")