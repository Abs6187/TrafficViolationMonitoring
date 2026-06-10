from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from config import Settings
from detection import InferenceService
from notifications import send_violation_sms
from storage import init_db, save_violation


Settings.ensure_directories()
init_db()
inference_service = InferenceService()


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(Settings.STATIC_DIR), static_url_path="")
    app.config["MAX_CONTENT_LENGTH"] = Settings.MAX_CONTENT_LENGTH
    CORS(app, resources={r"/api/*": {"origins": Settings.ALLOWED_ORIGINS}})

    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "app": Settings.APP_NAME,
                "inference": inference_service.status(),
                "twilio_enabled": Settings.ENABLE_TWILIO,
            }
        )

    @app.get("/api/model-status")
    def model_status():
        return jsonify(inference_service.status())

    @app.post("/api/detect/image")
    def detect_image():
        try:
            image_file = request.files.get("image")
            if image_file is None:
                return jsonify({"error": "image file is required"}), 400

            summary = inference_service.detect_image(image_file.read())
            return jsonify(
                {
                    "image": summary.annotated_base64,
                    "number_plate_text": summary.number_plate_text,
                    "violation_detected": summary.violation_detected,
                    "detections": summary.detections,
                }
            )
        except FileNotFoundError as exc:
            return jsonify({"error": str(exc)}), 503
        except Exception as exc:
            return jsonify({"error": f"image detection failed: {exc}"}), 500

    @app.post("/api/detect/video")
    def detect_video():
        try:
            video_file = request.files.get("video")
            if video_file is None:
                return jsonify({"error": "video file is required"}), 400

            processed_video, metadata = inference_service.process_video(video_file.read())
            output_path = Settings.UPLOAD_DIR / "processed-video.mp4"
            output_path.write_bytes(processed_video)
            response = send_file(
                output_path,
                mimetype="video/mp4",
                as_attachment=False,
                download_name="processed-video.mp4",
            )
            response.headers["X-Detection-Metadata"] = str(metadata)
            return response
        except FileNotFoundError as exc:
            return jsonify({"error": str(exc)}), 503
        except Exception as exc:
            return jsonify({"error": f"video detection failed: {exc}"}), 500

    @app.post("/api/violations")
    def create_violation():
        try:
            payload = request.get_json(force=True, silent=False) or {}
            numberplate = str(payload.get("numberplate", "")).strip()
            email = str(payload.get("email", "")).strip()
            phonenumber = str(payload.get("phonenumber", "")).strip()

            if not numberplate or numberplate == "No number plate detected":
                return jsonify({"error": "a valid number plate is required"}), 400

            notification_sent, notification_message = send_violation_sms(numberplate, phonenumber)
            result = save_violation(
                numberplate=numberplate,
                email=email,
                phonenumber=phonenumber,
                notification_sent=notification_sent,
            )

            message = "Violation recorded successfully" if result["created"] else "Violation already exists"
            return jsonify(
                {
                    "msg": message,
                    "created": result["created"],
                    "notification_sent": notification_sent,
                    "notification_message": notification_message,
                    "record": result["record"],
                }
            )
        except Exception as exc:
            return jsonify({"error": f"unable to record violation: {exc}"}), 500

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def serve_frontend(path: str):
        static_dir = Path(app.static_folder)
        requested = static_dir / path
        if path and requested.exists() and requested.is_file():
            return send_from_directory(app.static_folder, path)
        index_file = static_dir / "index.html"
        if index_file.exists():
            return send_from_directory(app.static_folder, "index.html")
        return jsonify(
            {
                "message": "Frontend build not found. Run the frontend build or deploy with Docker.",
                "health": "/api/health",
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
