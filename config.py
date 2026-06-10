import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    APP_NAME = "Traffic Violation Monitoring"
    PORT = int(os.getenv("PORT", "5000"))
    HOST = os.getenv("HOST", "0.0.0.0")
    DEBUG = _bool_env("DEBUG", False)
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(150 * 1024 * 1024)))

    STATIC_DIR = Path(os.getenv("STATIC_DIR", BASE_DIR / "frontend" / "dist"))
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
    DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
    DATABASE_PATH = Path(os.getenv("DATABASE_PATH", DATA_DIR / "violations.db"))

    MODEL_PATH = Path(os.getenv("MODEL_PATH", BASE_DIR / "models" / "best.pt"))
    HF_MODEL_REPO = os.getenv("HF_MODEL_REPO", "").strip()
    HF_MODEL_FILENAME = os.getenv("HF_MODEL_FILENAME", "best.pt").strip()
    HF_TOKEN = os.getenv("HF_TOKEN", "").strip() or None
    # "space" is needed when the model file lives in a HuggingFace Space repo
    # (as opposed to a regular model repo). Set to "model" or "dataset" as needed.
    HF_REPO_TYPE = os.getenv("HF_REPO_TYPE", "space").strip()

    YOLO_DEVICE = os.getenv("YOLO_DEVICE", "auto").strip().lower()
    YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.45"))
    VIDEO_FRAME_STRIDE = max(1, int(os.getenv("VIDEO_FRAME_STRIDE", "3")))
    OCR_LANGS = [item.strip() for item in os.getenv("OCR_LANGS", "en").split(",") if item.strip()]

    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "").strip()
    DEFAULT_NOTIFICATION_TO = os.getenv("DEFAULT_NOTIFICATION_TO", "").strip()

    ALLOWED_ORIGINS = [item.strip() for item in os.getenv("ALLOWED_ORIGINS", "*").split(",") if item.strip()]

    @classmethod
    def ensure_directories(cls) -> None:
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
