# Custom detection weights (optional)

CourtFlow uses **pretrained** YOLO (YOLO26n / YOLOv8n) by default. For better player detection on padel footage, you can use a **custom-trained** model here.

## When you receive `best.pt`

1. **Put the file in this folder**  
   Copy the trained weights file (e.g. `best.pt`) into `models/`:
   ```
   CourtFlow-1/models/best.pt
   ```
   (The file is not committed to git because `*.pt` is in `.gitignore`.)

2. **Run the pipeline with that model**  
   Either pass the path on the CLI:
   ```bash
   python3 -m src.app.cli run-match --detection-model models/best.pt
   ```
   Or set it once in your environment (e.g. in `.env`):
   ```
   COURTFLOW_DETECTION_MODEL=./models/best.pt
   ```
   Then every `run-match` will use it.

3. **To switch back to the default (pretrained YOLO26)**  
   Omit `--detection-model` and unset the env:
   ```bash
   unset COURTFLOW_DETECTION_MODEL
   python3 -m src.app.cli run-match
   ```

## Requirements for the weights file

- Ultralytics YOLO format (`.pt`).
- **Person/player as class 0** so CourtFlow’s `classes=[0]` filter works.
- Trained for detection (bounding boxes). Pose models that also output boxes are fine.

See **[docs/DETECTION_TRAINING.md](../docs/DETECTION_TRAINING.md)** for how the model is trained (e.g. YOLO26 on a padel dataset) and more options.
