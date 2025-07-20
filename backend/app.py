import os
import threading
import logging
from typing import Any, Dict

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Re-use existing fuzzer & model code -----------------------------------------
from Webfuzzer import WebFuzzer
# NOTE: model_training contains heavy dependencies. Import lazily in endpoints.

###############################################################################
# App & real-time infrastructure
###############################################################################
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret-key")
CORS(app, supports_credentials=True)

# Socket.IO for live updates
socketio = SocketIO(app, cors_allowed_origins="*")

###############################################################################
# Helper – pipe Python logging -> Socket.IO
###############################################################################
class SocketIOHandler(logging.Handler):
    """Emit log records to the frontend via Socket.IO."""

    def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
        socketio.emit("log", {"level": record.levelname, "msg": self.format(record)})

# Attach handler to root logger once
_logging_configured = False
if not _logging_configured:
    handler = SocketIOHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logging.getLogger().addHandler(handler)
    _logging_configured = True

###############################################################################
# Background tasks
###############################################################################

def _run_fuzzer(target_url: str, wordlist_file: str, headless: bool = True) -> None:
    """Start the WebFuzzer in the current thread."""
    fuzzer = WebFuzzer(target_url, wordlist_file)
    # Monkey-patch headless flag
    fuzzer.start_browser = lambda headless=headless, _orig=fuzzer.start_browser: _orig(headless=headless)  # type: ignore
    fuzzer.start_fuzzing()

###############################################################################
# API routes
###############################################################################

@app.route("/api/fuzz", methods=["POST"])
def start_fuzz() -> Any:
    """Launch a fuzzing session in a background thread.

    Expected JSON body: {"target_url": str, "wordlist_file": str, "headless": bool}
    """
    data: Dict[str, Any] = request.get_json(force=True)  # type: ignore
    target_url = data.get("target_url")
    wordlist_file = data.get("wordlist_file")
    headless = bool(data.get("headless", True))

    if not target_url or not wordlist_file:
        return jsonify({"error": "'target_url' and 'wordlist_file' required"}), 400

    # Spawn fuzzer thread
    threading.Thread(target=_run_fuzzer, args=(target_url, wordlist_file, headless), daemon=True).start()
    return jsonify({"status": "fuzzer_started"})

@app.route("/api/train", methods=["POST"])
def train_models() -> Any:
    """Trigger ML model (re)training.

    Optionally accepts JSON body with dataset path or hyper-parameters.
    Streams progress via Socket.IO channel 'train_log'.
    """
    import importlib

    model_training = importlib.import_module("model_training")  # heavy import – lazy load

    def _task() -> None:
        socketio.emit("train_log", {"msg": "Starting training…"})
        try:
            model_training.main()  # type: ignore[attr-defined]
            socketio.emit("train_log", {"msg": "Training completed"})
        except Exception as e:
            socketio.emit("train_log", {"msg": f"Training failed: {e}"})
            app.logger.exception("Training failed")

    threading.Thread(target=_task, daemon=True).start()
    return jsonify({"status": "training_started"})

@app.route("/api/predict", methods=["POST"])
def predict() -> Any:
    """Return ML prediction for a supplied payload."""
    data = request.get_json(force=True)  # type: ignore
    payload = data.get("payload")
    if not payload:
        return jsonify({"error": "'payload' required"}), 400

    # Placeholder – load models & predict
    try:
        from joblib import load

        iso = load("anomaly_model.pkl")  # IsolationForest
        clf = load("classifier_model.pkl")  # RandomForest
        # TODO: preprocess payload properly
        features = [len(payload)]  # Dummy feature
        anomaly_score = iso.decision_function([features])[0]
        cls = clf.predict([features])[0]
        return jsonify({"classification": cls, "anomaly_score": anomaly_score})
    except Exception as e:
        app.logger.error("Prediction failed: %s", e)
        return jsonify({"error": "prediction_failed", "details": str(e)}), 500

###############################################################################
# Entry-point
###############################################################################

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)