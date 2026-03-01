# Custom detection weights (optional)

Default is pretrained YOLO (YOLO26n / YOLOv8n). To use a trained model (e.g. from a teammate):

1. **Put `best.pt` in this folder** (e.g. `models/best.pt`). It’s gitignored.
2. **Run:** `python3 -m src.app.cli run-match --detection-model models/best.pt`  
   Or set in `.env`: `COURTFLOW_DETECTION_MODEL=./models/best.pt`
3. **Back to default:** Unset the env and run without `--detection-model`.

**Requirements:** Ultralytics `.pt`, **person/player as class 0**.  
Training: [docs/DETECTION_TRAINING.md](../docs/DETECTION_TRAINING.md).
