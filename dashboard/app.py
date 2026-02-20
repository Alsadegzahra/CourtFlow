from pathlib import Path
import json
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_match_dirs(outputs_dir: Path):
    if not outputs_dir.exists():
        return []
    return sorted(
        [p for p in outputs_dir.iterdir() if p.is_dir()],
        key=lambda p: p.name,
        reverse=True
    )


def safe_exists(p: Path) -> bool:
    try:
        return p.exists()
    except Exception:
        return False


st.set_page_config(page_title="CourtFlow Phase 1 Dashboard", layout="wide")
st.title("CourtFlow — Phase 1 Dashboard (MVP Viewer)")

match_dirs = list_match_dirs(OUTPUTS_DIR)
if not match_dirs:
    st.warning("No matches found in outputs/. Run: python -m src.run_match --video ... --run_pipeline")
    st.stop()

match_names = [p.name for p in match_dirs]
selected = st.sidebar.selectbox("Select a match", match_names)
match_dir = OUTPUTS_DIR / selected

st.sidebar.markdown("---")
st.sidebar.write("Match folder:")
st.sidebar.code(str(match_dir))

meta_path = match_dir / "meta" / "meta.json"
report_path = match_dir / "reports" / "report.json"
tracks_path = match_dir / "tracks" / "tracks.json"
highlights_dir = match_dir / "highlights"
renders_dir = match_dir / "renders"
calib_path = match_dir / "calibration" / "homography.json"

if not meta_path.exists():
    st.error(f"Missing meta.json: {meta_path}")
    st.stop()

meta = read_json(meta_path)
video_path = Path(meta.get("video_path", ""))

# ---- Header metrics ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Match ID", meta.get("match_id", "—"))
c2.metric("Court ID", meta.get("court_id", "—"))
c3.metric("Status", meta.get("status", "—"))
c4.metric("Created At", meta.get("created_at", "—"))

# ---- Pipeline stages ----
with st.expander("Pipeline Stages", expanded=False):
    stages = meta.get("pipeline_stages", [])
    if stages:
        for s in stages:
            st.write(f"- {s}")
    else:
        st.info("No pipeline stages found in meta.json")

# ---- Video Metadata ----
st.subheader("Video Metadata")
st.json(meta.get("video", {}))

# ---- Video Player ----
st.subheader("Video")
if video_path and video_path.exists():
    st.video(str(video_path))
else:
    st.warning(f"Video file not found at: {video_path}")

# ---- Calibration ----
st.subheader("Calibration (Court Homography)")
if calib_path.exists():
    st.success("Calibration found ✅")
    with st.expander("View calibration/homography.json"):
        st.json(read_json(calib_path))
else:
    st.info("No calibration file yet (expected later from Court+Homography work).")

st.markdown("---")

# ---- Tracks ----
st.subheader("Tracks (Player Tracking Output)")
if tracks_path.exists():
    tracks = read_json(tracks_path)
    st.write(f"Tracks records: **{len(tracks)}**")
    if len(tracks) == 0:
        st.info("tracks.json is empty (placeholder). This will be populated by Player Detection + Tracking.")
    else:
        # show a preview table (first 50 rows)
        preview = tracks[:50]
        st.write("Preview (first 50 records):")
        st.dataframe(preview)
else:
    st.warning(f"Missing tracks.json: {tracks_path}")

st.markdown("---")

# ---- Report ----
st.subheader("Report (Analytics Output)")
report = None
if report_path.exists():
    report = read_json(report_path)
    st.write(f"Report status: **{report.get('status', '—')}**")
    with st.expander("View full reports/report.json", expanded=False):
        st.json(report)
else:
    st.warning(f"Missing report.json: {report_path}")

st.markdown("---")

# ---- Renders ----
st.subheader("Renders (Heatmaps / Plots / Overlays)")
if renders_dir.exists():
    render_files = sorted([p for p in renders_dir.iterdir() if p.is_file()])
    if not render_files:
        st.info("No renders yet. Later this will include heatmaps, intensity plots, overlay frames/videos.")
    else:
        st.write(f"Found **{len(render_files)}** render file(s):")
        for p in render_files:
            st.write(f"- {p.name}")
            # show images if present
            if p.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                st.image(str(p), caption=p.name, use_container_width=True)
            # show videos if present
            elif p.suffix.lower() in [".mp4", ".mov"]:
                st.video(str(p))
else:
    st.info("No renders folder found (it should exist).")

st.markdown("---")

# ---- Highlights ----
st.subheader("Highlights (Exported Clips)")
exported = []
if report is not None:
    exported = report.get("exported_highlights", [])

if exported:
    st.success(f"Showing **{len(exported)}** exported highlight clip(s)")
    for item in exported:
        filename = item.get("file")
        reason = item.get("reason", "—")
        start = item.get("start", "—")
        end = item.get("end", "—")

        clip_path = highlights_dir / filename if filename else None

        st.markdown(f"**{filename}**  \nReason: `{reason}` | {start}s → {end}s")
        if clip_path and clip_path.exists():
            st.video(str(clip_path))
        else:
            st.warning(f"Missing clip file: {clip_path}")
else:
    # fallback: list mp4 files in highlights folder
    if highlights_dir.exists():
        mp4s = sorted(highlights_dir.glob("*.mp4"))
        if mp4s:
            st.info("Showing highlight clips found in highlights/ folder.")
            for clip_path in mp4s:
                st.caption(clip_path.name)
                st.video(str(clip_path))
        else:
            st.info("No highlight clips yet. Run pipeline highlight export to generate clips.")
    else:
        st.info("No highlights folder found (it should exist).")

st.caption("Phase 1 dashboard = viewer + debugging tool. As tracking/analytics get implemented, this becomes your verification UI.")
