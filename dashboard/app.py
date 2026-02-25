from __future__ import annotations

from pathlib import Path
import streamlit as st

from src.storage.match_db import list_matches, get_match, list_artifacts
from src.config.settings import PROJECT_ROOT, DATA_DIR
from src.utils.io import read_json

def safe_exists(p: Path) -> bool:
    try:
        return p.exists()
    except Exception:
        return False


st.set_page_config(page_title="CourtFlow Dashboard", layout="wide")

# ---- User entry: Court ID + Match ID ----
if "user_match_id" not in st.session_state:
    st.session_state["user_match_id"] = ""
if "user_court_id" not in st.session_state:
    st.session_state["user_court_id"] = ""

st.sidebar.markdown("### View a match")
court_id_input = st.sidebar.text_input(
    "Court ID (optional)",
    value=st.session_state["user_court_id"],
    placeholder="e.g. court_01",
    key="court_id_input",
)
match_id_input = st.sidebar.text_input(
    "Match ID",
    value=st.session_state["user_match_id"],
    placeholder="e.g. match_2026_02_25_022906",
    key="match_id_input",
)
col_go, col_clear = st.sidebar.columns(2)
if col_go.button("View dashboard", type="primary"):
    if (match_id_input or "").strip():
        st.session_state["user_match_id"] = match_id_input.strip()
        st.session_state["user_court_id"] = (court_id_input or "").strip()
        st.rerun()
if col_clear.button("Clear"):
    st.session_state["user_match_id"] = ""
    st.session_state["user_court_id"] = ""
    st.rerun()

st.sidebar.markdown("---")

# ---- Resolve which match to show ----
matches = list_matches(limit=200)
match_ids = [m["match_id"] for m in matches]

# Prefer user-entered ID; otherwise use dropdown if we have matches
if st.session_state.get("user_match_id"):
    selected_match_id = st.session_state["user_match_id"]
elif matches:
    selected_match_id = st.sidebar.selectbox("Or select from list (ops)", match_ids, key="select_match")
else:
    st.title("CourtFlow — User Dashboard")
    st.info("Enter a **Match ID** in the sidebar and click **View dashboard** to open that match.")
    st.caption("Example: `match_2026_02_25_022906`")
    st.stop()

st.title("CourtFlow — MVP Dashboard (DB + Outputs Viewer)")
st.caption(f"Project root: {PROJECT_ROOT}")
st.caption(f"Data dir: {DATA_DIR}")

match = get_match(selected_match_id)
if not match:
    st.error(f"Match not found: **{selected_match_id}**. Check the ID or select from the list.")
    if matches:
        st.sidebar.selectbox("Or select from list (ops)", match_ids, key="select_match_fallback")
    st.stop()

# If user set a court ID, check the match belongs to that court
user_court = (st.session_state.get("user_court_id") or "").strip()
if user_court and match.get("court_id") != user_court:
    st.warning(f"This match belongs to court **{match.get('court_id')}**, not **{user_court}**.")

output_dir = Path(match["output_dir"])
source_uri = Path(match["source_uri"]) if match["source_type"] == "FILE" else None

st.sidebar.markdown("---")
st.sidebar.caption(f"Viewing: **{selected_match_id}**")
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

# ---- Cloud (R2) ----
st.subheader("Cloud (R2)")
import os
import urllib.request
import json as _json

_api_url = os.getenv("COURTFLOW_API_URL", "http://127.0.0.1:8000").rstrip("/")

def _api_get(path: str) -> tuple[dict | None, int, str]:
    try:
        req = urllib.request.Request(f"{_api_url}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=10) as r:
            return _json.loads(r.read().decode()), r.status, ""
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()
            return None, e.code, body
        except Exception:
            return None, e.code, str(e)
    except Exception as e:
        return None, 0, str(e)

def _api_post(path: str) -> tuple[dict | None, int, str]:
    try:
        req = urllib.request.Request(
            f"{_api_url}{path}",
            data=b"",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return _json.loads(r.read().decode()), r.status, ""
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()
            return None, e.code, body
        except Exception:
            return None, e.code, str(e)
    except Exception as e:
        return None, 0, str(e)

if st.button("Upload to R2", key="cloud_upload"):
    data, code, err = _api_post(f"/matches/{selected_match_id}/cloud/upload")
    if code == 200 and data:
        st.success("Uploaded to R2.")
        if data.get("keys"):
            st.code("\n".join(data["keys"]))
        if data.get("urls"):
            for k, u in data["urls"].items():
                if u:
                    st.markdown(f"**{k}**: [Open link]({u})")
    elif code == 503:
        st.error("R2 not configured. Set R2_* in .env (see README) and restart the API.")
    else:
        st.error(f"Upload failed: {code} {err}")

if st.button("Get cloud links (1h)", key="cloud_urls"):
    data, code, err = _api_get(f"/matches/{selected_match_id}/cloud/urls?expires_seconds=3600")
    if code == 200 and data:
        if data.get("highlights_url"):
            st.markdown(f"**Highlights (cloud)**: [Watch highlights]({data['highlights_url']})")
            st.video(data["highlights_url"])
        else:
            st.info("No highlights URL (upload first or check R2).")
        if data.get("report_url"):
            st.markdown(f"**Report (cloud)**: [Download report]({data['report_url']})")
    elif code == 503:
        st.warning("R2 not configured. Set R2_* in .env and restart the API.")
    else:
        st.error(f"Could not get URLs: {code} {err}")

st.caption("API must be running: python3 -m uvicorn src.app.api:app --reload. Set COURTFLOW_API_URL if different.")

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