# Traffic Violation Monitoring

This repository contains a helmet-detection and ANPR workflow for detecting riders without helmets, extracting number plates, and generating e-challan records.

## Current Architecture

The repository originally mixed a React frontend, a Node/Express backend, and standalone Python scripts. It has been updated into a deployment-friendly layout centered on a single Flask service:

- `app.py`: production entrypoint that serves both API routes and the built frontend
- `detection.py`: GPU-aware YOLO + EasyOCR inference with image and video support
- `storage.py`: SQLite-backed violation storage
- `notifications.py`: optional Twilio SMS integration
- `frontend/`: React + Vite client
- `backend/`: legacy Express backend retained for reference, with secrets removed
- `final.py` and `forimage.py`: legacy entrypoints redirected to the new Flask app

## What Was Fixed

- Removed hardcoded Twilio credentials and personal contact data from runtime code
- Replaced localhost-only frontend API calls with configurable API URLs
- Added defensive error handling so missing files, missing models, OCR failures, and video processing errors return clear responses instead of hanging the app
- Added automatic Hugging Face model download support when the YOLO weights are not bundled locally
- Added Docker and `render.yaml` configuration for Render deployment
- Added GPU auto-detection so the same code can use CUDA where it is available and fall back to CPU where it is not

## Detection Flow

1. Upload an image or video from the web UI.
2. The Flask API sends the media through YOLO inference.
3. Number plates are read with EasyOCR when the pipeline identifies relevant detections.
4. Violations are stored locally in SQLite.
5. If Twilio is configured, the service can send an SMS notification automatically.

## Local Setup

### 1. Install Python dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install frontend dependencies

```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Configure environment variables

Copy `.env.example` into `.env` and fill in the values you need.

Minimum recommended configuration:

```env
MODEL_PATH=./models/best.pt
YOLO_DEVICE=auto
VITE_API_BASE_URL=/api
```

Optional automatic model download from Hugging Face:

```env
HF_MODEL_REPO=your-org/your-model-repo
HF_MODEL_FILENAME=best.pt
HF_TOKEN=hf_xxx
```

### 4. Run the application

```bash
python app.py
```

Then open `http://localhost:5000`.

## API Endpoints

- `GET /api/health`: service and inference readiness
- `GET /api/model-status`: model path, device, and readiness
- `POST /api/detect/image`: image detection
- `POST /api/detect/video`: video detection
- `POST /api/violations`: create a stored e-challan record

## Render Deployment

This repo includes a root `Dockerfile` and `render.yaml` for a single Docker-based web service on Render.

### Important note about GPU on Render

The application code is GPU-compatible and automatically uses CUDA when the host provides it. Render does not currently provide native GPU instances for general web services, so a Render deployment will run in CPU mode unless you move inference to an external GPU provider and call it remotely.

### Deploy steps

1. Push this repository to GitHub.
2. In Render, create a new Blueprint or Web Service from the Git repository.
3. Use the included `render.yaml` or point Render at the root `Dockerfile`.
4. Set the required environment variables in the Render dashboard:
   - `HF_MODEL_REPO`, `HF_MODEL_FILENAME`, `HF_TOKEN` if the model should be downloaded at deploy/runtime
   - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `DEFAULT_NOTIFICATION_TO` for SMS
5. After the deploy finishes, verify `GET /api/health`.

## Known Requirement

The repository does not include trained model weights such as `best.pt`. You must provide them through one of these paths:

- commit or mount the model under `./models/best.pt`
- set `MODEL_PATH` to a valid model file
- configure Hugging Face download variables so the service can fetch the model automatically

## Legacy Notes

The old Node backend and Python scripts are still present so earlier development work remains inspectable, but the recommended runtime path for deployment is the Flask service in `app.py`.
