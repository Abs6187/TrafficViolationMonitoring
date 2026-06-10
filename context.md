# Traffic Violation Monitoring — AI Handoff Context

> **For future AI assistants**: Read this file first. It tells you exactly what has been done, what environment variables are needed, and what still needs to happen. Do NOT re-do completed steps.

---

## Project Identity

| Field | Value |
|---|---|
| **GitHub Repo** | https://github.com/Abs6187/TrafficViolationMonitoring |
| **Render Service** | https://dashboard.render.com/web/srv-d8kma0bbc2fs73co7pbg |
| **HF Model Space** | https://huggingface.co/spaces/Abs6187/Helmet-License-Plate-Detection |
| **HF Model File** | `best.pt` inside that Space |
| **Owner / Author** | Abs6187 (all previous references to `nishithamakam` or other owners have been removed) |

---

## What Has Been Done (Completed ✅)

1. **Repo cloned and sanitized** — original `nishithamakam/TrafficVoilationMonitoring` was forked, all commit history from the previous owner was erased, and a clean first commit was pushed to `Abs6187/TrafficViolationMonitoring`.

2. **Hardcoded secrets removed** — Twilio credentials and personal phone/email that were in the old source are gone. All secrets now come from environment variables only.

3. **Architecture unified** — One Flask app (`app.py`) serves both the API and the built React frontend. Legacy `final.py`, `forimage.py`, and the Express `backend/` remain for reference but are not needed for production.

4. **Error handling added** — Every API route in `app.py` has `try/except`. Every critical path in `detection.py` (`detect_image`, `process_video`, `_extract_number_plate`, `_load_model`) has defensive handling so the server never hangs on a bad input or missing model.

5. **GPU-aware device selection** — `detection.py` calls `torch.cuda.is_available()` and selects `cuda:0` or `cpu` automatically. You can override with the `YOLO_DEVICE` env var.

6. **HuggingFace model download** — `detection.py._ensure_model_path()` downloads `best.pt` from the configured HF source at first request if it is not already on disk. The model lives at `https://huggingface.co/spaces/Abs6187/Helmet-License-Plate-Detection/blob/main/best.pt`.

   **IMPORTANT**: The model is in a HF **Space** repository, not a standard HF model repository. The download in `detection.py` uses `huggingface_hub.hf_hub_download` with `repo_type="space"` to handle this correctly.

7. **Docker + render.yaml in place** — `Dockerfile` builds the React frontend, installs Python deps, and starts the app. `render.yaml` declares the web service and env var keys (values must be set in the Render dashboard).

8. **SQLite violation storage** — `storage.py` auto-creates `data/violations.db` with a `violations` table on startup. Schema: `id, numberplate, email, phonenumber, notification_sent, created_at`.

9. **Twilio SMS optional** — `notifications.py` silently skips notification if Twilio vars are absent. Will not crash.

10. **Lightning AI deployment attempted** — The Lightning CLI (`lightning-sdk`) fails on Windows because its REPL dependency does not support Windows terminals. Use Lightning's web UI at https://lightning.ai/ to create a Studio or App manually if GPU inference is needed.

---

## What Still Needs to Happen (TODO ⏳)

- [ ] **Set Render env vars** — In the Render dashboard for service `srv-d8kma0bbc2fs73co7pbg`, set:
  - `HF_MODEL_REPO` = `Abs6187/Helmet-License-Plate-Detection`
  - `HF_MODEL_FILENAME` = `best.pt`
  - `HF_TOKEN` = *(ask the user — format: `hf_...`)*
  - `HF_REPO_TYPE` = `space`
  - (Optional Twilio vars if SMS is desired)
- [ ] **Verify live Render deploy** — After env vars are set, trigger a redeploy and hit `GET /api/health`. `inference.ready` should be `true` after the first detection request downloads the model.
- [ ] **Lightning AI Studio setup** — If GPU inference is needed, create a Studio at https://lightning.ai/ using the credentials the user has. Clone the repo there and run `python app.py`. GPU will be available automatically in a Lightning Studio.
- [ ] **Frontend polish** — The React frontend in `frontend/src/pages/` is functional but was not visually redesigned. If a better UI is wanted, that is the next place to work.

---

## Environment Variables Reference

### Required for model download (Render + local)

| Variable | Example Value | Purpose |
|---|---|---|
| `HF_MODEL_REPO` | `Abs6187/Helmet-License-Plate-Detection` | HuggingFace Space or Model repo ID |
| `HF_MODEL_FILENAME` | `best.pt` | Filename inside the repo |
| `HF_TOKEN` | *(set in Render dashboard only, never in code)* | HF read token |
| `HF_REPO_TYPE` | `space` | Must be `space` for this project's model source |

### Optional — GPU / inference tuning

| Variable | Default | Purpose |
|---|---|---|
| `YOLO_DEVICE` | `auto` | `auto`, `cpu`, `cuda:0` |
| `YOLO_CONFIDENCE` | `0.45` | Detection confidence threshold |
| `VIDEO_FRAME_STRIDE` | `3` | Process every Nth video frame (higher = faster, less accurate) |
| `OCR_LANGS` | `en` | Comma-separated EasyOCR language codes |

### Optional — SMS notifications

| Variable | Default | Purpose |
|---|---|---|
| `ENABLE_TWILIO` | `false` | Set `true` to enable SMS notifications (disabled by default) |
| `TWILIO_ACCOUNT_SID` | `` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | `` | Twilio auth token |
| `TWILIO_FROM_NUMBER` | `` | Twilio sender number |
| `DEFAULT_NOTIFICATION_TO` | `` | Default recipient number |

### Server

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `5000` | Flask/Gunicorn listen port |
| `DEBUG` | `false` | Enable Flask debug mode |
| `MAX_CONTENT_LENGTH` | `157286400` (150 MB) | Max upload size |

---

## Key Files

```
app.py              <- Flask app factory + API routes + static serving
config.py           <- All env var parsing; central Settings class
detection.py        <- YOLO inference + EasyOCR OCR; InferenceService class
storage.py          <- SQLite violation CRUD; auto-creates DB on import
notifications.py    <- Twilio SMS wrapper; silently skips if not configured or disabled
requirements.txt    <- Python deps (Flask, ultralytics, easyocr, torch, etc.)
Dockerfile          <- Multi-stage: Node builds React then Python runs Flask
render.yaml         <- Render Blueprint: Docker web service definition
frontend/           <- React + Vite client app
backend/            <- Legacy Express backend (NOT used in production)
final.py            <- Legacy entrypoint shim (not needed)
forimage.py         <- Legacy image script shim (not needed)
```

---

## Model Details

- **Architecture**: YOLOv11n (ultralytics)
- **Classes** (order matters, indices 0-3):
  - 0: `helmet`
  - 1: `licenseplate`
  - 2: `motorcyclist`
  - 3: `nohelmet`
- **Source file**: `best.pt` at https://huggingface.co/spaces/Abs6187/Helmet-License-Plate-Detection/blob/main/best.pt
- **Download method**: `huggingface_hub.hf_hub_download(repo_id=..., repo_type="space", filename="best.pt", token=...)`

---

## Deployment Platforms

### Render (active)
- Service: `traffic-violation-monitoring` (`srv-d8kma0bbc2fs73co7pbg`)
- Runtime: Docker (builds from root `Dockerfile`)
- Plan: Starter (CPU only — Render has no GPU web service plan as of June 2026)
- Auto-deploy: enabled on push to `main`
- Dashboard: https://dashboard.render.com/web/srv-d8kma0bbc2fs73co7pbg

### Lightning AI (pending manual setup)
- Lightning user ID is stored with the user (not committed here for security)
- CLI broken on Windows — use web UI at https://lightning.ai/
- GPU-capable Studios available — use for real-time inference

---

## Credential Locations

> **IMPORTANT**: No actual secret values are stored in this file. Ask the user for credentials when needed.

| Credential | Where to find it |
|---|---|
| HF Token (`hf_...`) | Ask user or check Render dashboard env vars |
| Render API Key (`rnd_...`) | Ask user — used to call Render API |
| GitHub PAT (`github_pat_...`) | Ask user — needed to push to GitHub |
| Lightning API Key (UUID) | Ask user — needed to use Lightning AI API |
| Lightning User ID (UUID) | Ask user |

---

## Render API — Useful Commands

Replace `$RENDER_API_KEY` with the actual key from the user:

```bash
# Trigger a manual deploy
curl -X POST https://api.render.com/v1/services/srv-d8kma0bbc2fs73co7pbg/deploys \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" -d '{"clearCache": false}'

# Get service info
curl https://api.render.com/v1/services/srv-d8kma0bbc2fs73co7pbg \
  -H "Authorization: Bearer $RENDER_API_KEY"

# List env vars
curl https://api.render.com/v1/services/srv-d8kma0bbc2fs73co7pbg/env-vars \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

---

## GitHub — Push Command

Replace `$GH_PAT` with the actual GitHub PAT from the user:

```bash
git remote set-url origin https://$GH_PAT@github.com/Abs6187/TrafficViolationMonitoring.git
git push origin main
```

---

*Last updated: 2026-06-10 by AI assistant (Gemini 3.5 Flash)*
