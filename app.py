"""
Knight Tamagotchi — local Flask server.
Replaces the lovable.app backend. Stores state in state.json next to this file.
Run:  python app.py
Then open http://localhost:5000
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json, os, threading
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, "state.json")
STATIC_DIR = os.path.join(HERE, "static")

DEFAULT_STATE = {
    "hunger": 50,
    "happiness": 50,
    "health": 100,
    "tiredness": 30,
    "animation": "idle",
    "outside": False,
    "food_pending": 0,
    "updated_at": datetime.utcnow().isoformat() + "Z",
}

_lock = threading.Lock()

def load_state():
    if not os.path.exists(STATE_FILE):
        save_state(DEFAULT_STATE)
        return dict(DEFAULT_STATE)
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(s):
    with open(STATE_FILE, "w") as f:
        json.dump(s, f, indent=2)

app = Flask(__name__, static_folder=None)
CORS(app)  # allow Pi/browser from anywhere on your LAN

# ---------- static frontend ----------
@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/play")
def play():
    return send_from_directory(STATIC_DIR, "play.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(STATIC_DIR, path)

# ---------- API ----------
@app.route("/api/public/state", methods=["GET"])
def get_state():
    with _lock:
        return jsonify(load_state())

@app.route("/api/public/is_outside", methods=["GET"])
def is_outside():
    with _lock:
        s = load_state()
        return jsonify({"outside": s["outside"], "food_pending": s["food_pending"]})

@app.route("/api/public/go_outside", methods=["POST"])
def go_outside():
    with _lock:
        s = load_state()
        if s["outside"]:
            return jsonify({"ok": False, "reason": "already_outside"}), 409
        s["outside"] = True
        s["updated_at"] = datetime.utcnow().isoformat() + "Z"
        save_state(s)
        return jsonify({"ok": True})

@app.route("/api/public/return", methods=["POST"])
def return_home():
    body = request.get_json(silent=True) or {}
    food = int(body.get("food_collected", 0))
    if food < 0 or food > 999:
        return jsonify({"error": "food_collected out of range"}), 400
    with _lock:
        s = load_state()
        s["outside"] = False
        s["food_pending"] = s.get("food_pending", 0) + food
        s["updated_at"] = datetime.utcnow().isoformat() + "Z"
        save_state(s)
        return jsonify({"ok": True, "food_pending": s["food_pending"]})

@app.route("/api/public/push", methods=["POST"])
def push():
    body = request.get_json(silent=True) or {}
    required = ["hunger", "happiness", "health", "tiredness", "animation"]
    for k in required:
        if k not in body:
            return jsonify({"error": f"missing {k}"}), 400
    with _lock:
        s = load_state()
        for k in ["hunger", "happiness", "health", "tiredness"]:
            v = float(body[k])
            if v < 0 or v > 100:
                return jsonify({"error": f"{k} out of range"}), 400
            s[k] = v
        s["animation"] = str(body["animation"])[:32]
        s["updated_at"] = datetime.utcnow().isoformat() + "Z"
        save_state(s)
        return jsonify({"ok": True})

# Consume pending food (Pi calls this to feed the knight from outside-trip food)
@app.route("/api/public/consume_food", methods=["POST"])
def consume_food():
    with _lock:
        s = load_state()
        eaten = s.get("food_pending", 0)
        if eaten > 0:
            s["hunger"] = min(100, s["hunger"] + eaten * 10)
            s["happiness"] = min(100, s["happiness"] + eaten * 5)
            s["food_pending"] = 0
            s["updated_at"] = datetime.utcnow().isoformat() + "Z"
            save_state(s)
        return jsonify({"ok": True, "eaten": eaten})


if __name__ == "__main__":
    # host=0.0.0.0 so the Raspberry Pi on your LAN can reach it too
    app.run(host="0.0.0.0", port=5000, debug=True)
