# run-match: why it takes long, how to speed up, where to see results

## Why it can take a long time

The pipeline runs six stages. The slow part is usually **stage 02 (player detection + tracking)**:

- The video is read frame by frame. Every **N**th frame (default `--sample_every 5`) is run through YOLO + tracker.
- A 10‑minute video at 30 fps has ~18,000 frames; with `sample_every=5` that’s ~3,600 inference steps. On CPU, each step can take a few hundred ms, so the whole stage can take **many minutes** (or more for long videos or heavy models).
- Stages 03–06 (mapping, report, overlays, highlights) are usually faster but add more time.

So yes, **it’s normal for run-match to take a long time**, especially with a custom/pose model or on CPU. You should see progress lines like:

```text
[02] Player detection + tracking
   ... tracking frame 3600/18000 (20%)
   ... tracking frame 7200/18000 (40%)
   ...
   ✓ Tracked 12345 points from 3600 frames (4 players).
```

If you don’t see any output for a long time, the process is still working on the first batch of frames (or loading the model). Once progress appears, it will continue until the end.

---

## How to speed it up

1. **Sample fewer frames**  
   `--sample_every 10` or `15` processes fewer frames (faster, slightly less smooth tracks).
2. **Use the default pretrained YOLO (YOLO26)**  
   Don’t pass `--detection-model` and don’t set `COURTFLOW_DETECTION_MODEL`. Then CourtFlow uses **yolo26n.pt** (or yolov8n.pt), which is smaller and faster than a custom pose model.
3. **Use a GPU**  
   If you have CUDA, install the GPU build of PyTorch/Ultralytics so YOLO runs on GPU; this greatly reduces stage 02 time.
4. **Shorter video for testing**  
   Ingest a short clip (e.g. 1–2 minutes) to confirm the pipeline and check results quickly.

---

## Where to check results

After `run-match` finishes successfully:

| What | Where |
|------|--------|
| **Tracks (raw)** | `data/matches/<match_id>/tracks/tracks.json` |
| **Report (stats, heatmap data)** | `data/matches/<match_id>/reports/report.json` |
| **Heatmap image** | `data/matches/<match_id>/reports/heatmap.png` |
| **Highlights video** | `data/matches/<match_id>/highlights/highlights.mp4` |
| **Overlay preview** | `data/matches/<match_id>/renders/track_overlay_preview.mp4` |

**In the app:**

- **User dashboard:** With the API running, open  
  `http://127.0.0.1:8000/view?match_id=<match_id>`  
  to see the report, heatmap, and highlights.
- **Ops dashboard (Streamlit):**  
  `python3 -m streamlit run dashboard/app.py`  
  Enter the match ID and use “View dashboard” to see full details, tracks, and artifacts.

---

## Using YOLO26 (pretrained) vs custom model

- **By default** (no `--detection-model`, no `COURTFLOW_DETECTION_MODEL`), CourtFlow already uses **YOLO26**: it loads **yolo26n.pt** and falls back to **yolov8n.pt** if YOLO26 isn’t available in your Ultralytics version. So “use YOLO26 for all” is already the default when you don’t pass a custom model.
- **Custom model** (e.g. your friend’s `best.pt`): use `--detection-model path/to/best.pt` or set `COURTFLOW_DETECTION_MODEL`. That model may be more accurate for padel but slower (e.g. pose model, larger file).
- **Force pretrained YOLO26** even if you had set a custom model before:  
  - Unset the env: `unset COURTFLOW_DETECTION_MODEL`  
  - Or run: `python3 -m src.app.cli run-match --detection-model yolo26n.pt`  
  (If `yolo26n.pt` isn’t a path to a file on disk, the code treats it as a pretrained name and downloads it.)

So: **yes, we already use YOLO26 by default**; custom models are opt-in for better detection at the cost of speed.
