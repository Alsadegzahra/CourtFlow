## B6 – Movement Metrics & Analytics

- **Responsibility**: Turn calibrated tracks + time info into the Phase 1 movement and spatial metrics, populating `Phase1Report` (summary, players, team, renders, highlights).
- **Main code**: `analytics.py`

### Tools / Libraries

- Python numerical stack (e.g., NumPy / Pandas) — _to be confirmed by the B6 team_

### Models / Intelligence

- Movement + spatial metrics listed in the Phase 1 docs:
  - Positional intelligence (heatmaps, zone coverage, net vs baseline, spacing, coverage gaps, drift, transitions, efficiency score)
  - Physical load metrics (distance, speed, sprints, accel/decel, lateral %, intensity timeline, load distribution, fatigue / intensity drop-off)
  - Motion-based highlight selection logic

