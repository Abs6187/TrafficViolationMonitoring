import base64
import io
import math
import os
import tempfile
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
from ultralytics import YOLO

from config import Settings

try:
    import easyocr
except Exception:  # pragma: no cover - optional during local static checks
    easyocr = None

try:
    from huggingface_hub import hf_hub_download
except Exception:  # pragma: no cover - optional during local static checks
    hf_hub_download = None


@dataclass
class DetectionSummary:
    annotated_base64: str
    number_plate_text: str
    violation_detected: bool
    detections: List[Dict]


class InferenceService:
    CLASS_NAMES = ["with helmet", "without helmet", "rider", "number plate"]

    def __init__(self) -> None:
        self._model = None
        self._reader = None
        self._lock = threading.Lock()
        self._last_error = ""

    def _resolve_device(self) -> str:
        if Settings.YOLO_DEVICE != "auto":
            return Settings.YOLO_DEVICE
        return "cuda:0" if torch.cuda.is_available() else "cpu"

    def _ensure_model_path(self) -> None:
        if Settings.MODEL_PATH.exists():
            return
        if not Settings.HF_MODEL_REPO:
            raise FileNotFoundError(
                f"Model not found at {Settings.MODEL_PATH}. Set MODEL_PATH or configure HF_MODEL_REPO/HF_MODEL_FILENAME."
            )
        if hf_hub_download is None:
            raise RuntimeError("huggingface_hub is required to download models automatically")

        downloaded_path = hf_hub_download(
            repo_id=Settings.HF_MODEL_REPO,
            filename=Settings.HF_MODEL_FILENAME,
            token=Settings.HF_TOKEN,
        )
        os.replace(downloaded_path, Settings.MODEL_PATH)

    def _load_model(self) -> YOLO:
        with self._lock:
            if self._model is not None:
                return self._model
            self._ensure_model_path()
            self._model = YOLO(str(Settings.MODEL_PATH))
            return self._model

    def _load_reader(self):
        with self._lock:
            if self._reader is not None:
                return self._reader
            if easyocr is None:
                raise RuntimeError("easyocr is not installed")
            self._reader = easyocr.Reader(Settings.OCR_LANGS, gpu=torch.cuda.is_available())
            return self._reader

    def status(self) -> Dict:
        try:
            model_exists = Settings.MODEL_PATH.exists()
            return {
                "ready": model_exists,
                "model_path": str(Settings.MODEL_PATH),
                "device": self._resolve_device(),
                "gpu_available": torch.cuda.is_available(),
                "last_error": self._last_error,
            }
        except Exception as exc:
            return {
                "ready": False,
                "model_path": str(Settings.MODEL_PATH),
                "device": "unknown",
                "gpu_available": False,
                "last_error": str(exc),
            }

    def _run_model(self, frame: np.ndarray):
        model = self._load_model()
        device = self._resolve_device()
        return model.predict(frame, conf=Settings.YOLO_CONFIDENCE, device=device, verbose=False)

    def _annotate_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict], str, bool]:
        results = self._run_model(frame)
        detections: List[Dict] = []
        rider_detected = False
        violation_detected = False
        number_plate_text = ""
        annotated = frame.copy()

        for result in results:
            boxes = result.boxes
            xy = boxes.xyxy
            confidences = boxes.conf
            classes = boxes.cls
            packed = torch.cat((xy, confidences.unsqueeze(1), classes.unsqueeze(1)), 1)

            for box in packed:
                x1, y1, x2, y2 = [int(value) for value in box[:4]]
                conf = math.ceil((float(box[4]) * 100)) / 100
                cls = int(box[5])
                label = self.CLASS_NAMES[cls] if cls < len(self.CLASS_NAMES) else f"class-{cls}"
                color = (0, 0, 255) if label in {"without helmet", "number plate"} else (255, 0, 0)

                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    annotated,
                    f"{label} {conf:.2f}",
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2,
                )

                detections.append(
                    {
                        "label": label,
                        "confidence": conf,
                        "bbox": [x1, y1, x2, y2],
                    }
                )

                if label == "rider":
                    rider_detected = True
                if label == "without helmet":
                    violation_detected = True
                if label == "number plate" and rider_detected:
                    cropped = annotated[max(y1, 0):max(y2, 0), max(x1, 0):max(x2, 0)]
                    if cropped.size != 0:
                        number_plate_text = self._extract_number_plate(cropped) or number_plate_text

        return annotated, detections, number_plate_text, violation_detected

    def _extract_number_plate(self, cropped_plate: np.ndarray) -> str:
        try:
            reader = self._load_reader()
            output = reader.readtext(cropped_plate)
            extracted = "".join(item[1] for item in output).replace(" ", "")
            return extracted.strip()
        except Exception as exc:
            self._last_error = str(exc)
            return ""

    def detect_image(self, image_bytes: bytes) -> DetectionSummary:
        try:
            np_bytes = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Unable to decode image bytes")

            annotated, detections, number_plate_text, violation_detected = self._annotate_frame(image)
            ok, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if not ok:
                raise RuntimeError("Failed to encode processed image")

            return DetectionSummary(
                annotated_base64=base64.b64encode(buffer).decode("utf-8"),
                number_plate_text=number_plate_text or "No number plate detected",
                violation_detected=violation_detected,
                detections=detections,
            )
        except Exception as exc:
            self._last_error = str(exc)
            raise

    def process_video(self, video_bytes: bytes) -> Tuple[bytes, Dict]:
        source_file = None
        output_file = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as src:
                src.write(video_bytes)
                source_file = src.name

            capture = cv2.VideoCapture(source_file)
            if not capture.isOpened():
                raise RuntimeError("Unable to open uploaded video")

            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
            fps = capture.get(cv2.CAP_PROP_FPS) or 20.0

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as dst:
                output_file = dst.name

            writer = cv2.VideoWriter(
                output_file,
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                (width, height),
            )
            if not writer.isOpened():
                raise RuntimeError("Unable to initialize output video writer")

            frame_index = 0
            violations = 0
            plates = set()

            while True:
                success, frame = capture.read()
                if not success:
                    break

                if frame_index % Settings.VIDEO_FRAME_STRIDE == 0:
                    annotated, _, plate_text, violation_detected = self._annotate_frame(frame)
                else:
                    annotated = frame
                    plate_text = ""
                    violation_detected = False

                if violation_detected:
                    violations += 1
                if plate_text:
                    plates.add(plate_text)

                writer.write(annotated)
                frame_index += 1

            capture.release()
            writer.release()

            with open(output_file, "rb") as handle:
                payload = handle.read()

            return payload, {
                "frames_processed": frame_index,
                "violations": violations,
                "number_plates": sorted(plates),
            }
        except Exception as exc:
            self._last_error = str(exc)
            raise
        finally:
            for path in [source_file, output_file]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
