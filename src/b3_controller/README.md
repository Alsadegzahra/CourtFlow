## B3 – Controller (Match Orchestration)

- **Responsibility**: Watch the DB for `FINALIZED` matches and invoke the core pipeline for each one.
- **Main code**: `controller.py`

### Tools / Libraries

- SQLite (through `b2_storage.db`)
- Python standard library (`time`)

### Models / Intelligence

- _(None — orchestration only.)_

