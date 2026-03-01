# Using a custom-trained YOLO model for player detection

CourtFlow uses **person detection** (COCO class 0) for tracking. By default it loads a **pretrained** model (`yolo26n.pt` or `yolov8n.pt`). For better accuracy on padel/court footage you can **train your own YOLO** and use the resulting `best.pt` in CourtFlow.

---

## Where to do the training

**Recommendation: train in a different repo (or Colab/notebook), then bring the weights file into CourtFlow.**

| Approach | Why |
|----------|-----|
| **Separate repo** | Keeps datasets, labels, and training scripts out of the app repo. Different env (e.g. GPU, extra deps). You only deliver a single `best.pt` file. |
| **Colab / notebook** | Good for one-off or small experiments; same idea: train there, download `best.pt`, add it to CourtFlow. |
| **Inside CourtFlow** | Possible (e.g. a `training/` folder and scripts), but mixes app and ML workflows and can bloat the repo with data and run artifacts. |

**Workflow:** Train elsewhere → get `best.pt` (or `yolo_padel_v1.pt`) → either copy it into CourtFlow (e.g. `models/best.pt`) or set `COURTFLOW_DETECTION_MODEL` to its path. CourtFlow only needs the `.pt` file at inference time; it does not need the training code or dataset.

**When someone else trains the model (e.g. a teammate):** Put the `best.pt` file they send into the **`models/`** folder and follow the steps in **[models/README.md](../models/README.md)**. No training setup is required in this repo.

---

## 1. Train a YOLO model (Ultralytics)

Use the [Ultralytics YOLO](https://docs.ultralytics.com/) training pipeline. You can train **YOLO26** (newer, edge-optimized) or **YOLOv8**; both work in CourtFlow.

### Train YOLO26 (recommended if your Ultralytics version supports it)

YOLO26 is supported in recent Ultralytics releases. Fine-tune from the pretrained checkpoint:

```bash
yolo detect train data=path/to/data.yaml model=yolo26n.pt epochs=50 imgsz=640
```

- Use `yolo26n.pt` (nano), `yolo26s.pt`, or `yolo26m.pt` depending on speed/accuracy tradeoff.  
- After training, weights are in `runs/detect/train/weights/best.pt`. Use that `.pt` in CourtFlow with `--detection-model`.

To train from scratch (no pretrained weights):

```bash
yolo detect train data=path/to/data.yaml model=yolo26n.yaml epochs=100 imgsz=640
```

### Train YOLOv8 (same idea)

```bash
yolo detect train data=path/to/data.yaml model=yolov8n.pt epochs=50 imgsz=640
```

Or from scratch: `model=yolov8n.yaml`.

### Dataset and class

- Dataset format: YOLO (one `.txt` per image with `0 x_center y_center w h` normalized), or use a `data.yaml` that points to your images and labels.  
- Annotate **person** as class **0** so the model stays compatible with CourtFlow’s `classes=[0]`.  
- Include frames that look like your match footage (angle, lighting, court type).  
- After training, use the single output file `best.pt` in CourtFlow.

---

## 2. Use your trained weights in CourtFlow

**CLI (run-match)**  
Pass the path to your `.pt` file:

```bash
python3 -m src.app.cli run-match --detection-model path/to/best.pt
```

Or with a path relative to the project root, e.g. `models/best.pt`:

```bash
python3 -m src.app.cli run-match --detection-model models/best.pt
```

**Environment variable**  
Set once so every run uses your model (no CLI flag):

```bash
export COURTFLOW_DETECTION_MODEL=/absolute/path/to/best.pt
python3 -m src.app.cli run-match
```

Or in `.env`:

```
COURTFLOW_DETECTION_MODEL=./models/best.pt
```

**Resolution order**  
1. `--detection-model` (CLI)  
2. `COURTFLOW_DETECTION_MODEL` (env)  
3. Pretrained `yolo26n.pt` / `yolov8n.pt` if neither is set.

---

## 3. Where to put the weights file in CourtFlow

After training (in the other repo or Colab), you only need to point CourtFlow at the **single `.pt` file**:

- **Option A:** Copy `best.pt` into CourtFlow, e.g. `CourtFlow-1/models/best.pt`, and use `--detection-model models/best.pt` or `COURTFLOW_DETECTION_MODEL=./models/best.pt`.
- **Option B:** Keep weights elsewhere (e.g. shared drive or training repo) and set `COURTFLOW_DETECTION_MODEL=/absolute/path/to/best.pt`.

Add `models/*.pt` to `.gitignore` if you don’t want to commit large weight files.

---

## 4. Contract (unchanged)

The custom model is loaded with `YOLO(path)`. CourtFlow still:

- Runs **person only** (`classes=[0]`).  
- Expects the same detection output format (bboxes, optional track IDs).  
- Uses the same tracking (BoT-SORT/ByteTrack) and ROI/ground-point logic.

So any Ultralytics YOLO weights trained for **person (class 0)** will work as a drop-in replacement for the default pretrained model.
