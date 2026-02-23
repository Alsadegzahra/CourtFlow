## B2 – Storage (DB + Match Outputs)

- **Responsibility**: Persist courts, matches, and artifacts in SQLite and manage the on-disk folder layout for each match.
- **Main code**: `db.py`, `match_store.py`

### Tools / Libraries

- SQLite (via Python `sqlite3`)
- Local filesystem (`pathlib`)

### Models / Intelligence

- _(None — pure persistence and filesystem layout.)_

