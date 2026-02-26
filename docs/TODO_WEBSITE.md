# CourtFlow – Website / dashboard todo

What’s implemented vs what’s left for the **user-facing website** (landing + view + API) and the **ops dashboard** (Streamlit). Docs are out of scope here.

---

## Currently implemented

**User site**
- **Landing** (`/` → `landing.html`): Match ID input → redirect to `/view?match_id=xxx`.
- **View** (`/view` → `view.html`): Match header; match structure (duration, track points, players, distance, etc.); positional intelligence (heatmap image + per-player table); physical load; padel block (wall/ground bounces, player stats sample); highlights (video from cloud URL or local API + segment list); technical details (raw report JSON).
- **API**: `/health`, `/matches`, `/matches/{id}`, `/matches/{id}/report`, `/matches/{id}/report/heatmap`, `/matches/{id}/highlights/video`, `/matches/{id}/meta`, `/matches/{id}/cloud/urls`, `POST /matches/{id}/cloud/upload`. Report and match resolution work with R2 when deployed (no local DB).

**Ops dashboard (Streamlit)**
- Court ID + Match ID (or list); match meta; report; heatmap; tracks; source video; calibration; renders; highlights; cloud upload; artifacts.

---

## To implement (website)

### 1. Landing page

| Item | Priority | Notes |
|------|----------|--------|
| **Match list** | High | Call `GET /matches`, show recent matches as links to `/view?match_id=xxx` so users don’t need to know the ID. |
| **Optional: search/filter** | Low | Filter list by court ID or date if useful. |

### 2. View page (view.html)

| Item | Priority | Notes |
|------|----------|--------|
| **Loading state** | Medium | Spinner or skeleton while fetching report/match; avoid blank screen. |
| **Error handling** | Medium | Clear messages for 404 (match/report not found), 5xx, network errors; optional retry button. |
| **Share link** | Low | “Copy link” for current URL so users can share the report. |
| **Units** | Low | Show units (e.g. m, km/h) consistently; physical load already has some; ensure summary and report match. |
| **Heatmap when deployed** | High | Heatmap is only served from local file today. When using R2 only, `/report/heatmap` 404s. Need: upload `heatmap.png` to R2, add `heatmap_url` to `GET /matches/{id}/cloud/urls`, and in view use `heatmap_url` when present (e.g. `img src = heatmap_url` from cloud/urls). |
| **Highlights fallback** | Low | If video fails (CORS, 404), show message and keep segment list if available. |
| **Mobile / responsive** | Low | Tweak cards and layout for small screens if needed. |
| **Padel when ball exists** | Later | When ball tracking and padel metrics exist, show rally/shot/wall in a clearer way (report/dashboard already have placeholders). |

### 3. API (for website)

| Item | Priority | Notes |
|------|----------|--------|
| **Heatmap for R2-only** | High | Upload `reports/heatmap.png` in `upload_match_artifacts`; add `heatmap_url` (signed URL) to `GET /matches/{id}/cloud/urls`; view uses it so heatmap works when deployed without local files. |
| **Serve heatmap from R2 when local missing** | High | Optional: `GET /matches/{id}/report/heatmap` could redirect to signed R2 URL or proxy when `output_dir` not available and R2 has heatmap (keeps single URL for view). |
| **CORS** | Low | If the frontend is ever served from another origin, add CORS headers to the API. |

### 4. Ops dashboard (Streamlit)

| Item | Priority | Notes |
|------|----------|--------|
| **Re-run pipeline** | Low | Button to trigger `run-match` for selected match (e.g. subprocess or internal call). |
| **Bulk upload to R2** | Low | “Upload all” or select multiple matches and upload. |
| **Calibration status** | Low | Per-court summary (e.g. last calibration, OK/fail). |

---

## Suggested order

1. **Heatmap when deployed** – Upload heatmap to R2, add `heatmap_url` to cloud/urls, view uses it.
2. **Match list on landing** – `GET /matches` and show links to `/view?match_id=...`.
3. **View: loading + errors** – Spinner/skeleton and clear error messages + optional retry.
4. **Share link + units + highlights fallback** – Small UX improvements.
5. **Streamlit / CORS / mobile** – As needed.

---

*Update this file as you complete or reprioritize.*
