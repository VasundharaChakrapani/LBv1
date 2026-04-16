from flask import Flask, jsonify, render_template, request
from evaluate import evaluate_all, get_request_log
from simulation_manager import SimulationManager   # 🔥 NEW

app = Flask(__name__)

# -----------------------------
# GLOBAL SIMULATION MANAGER
# -----------------------------
sim_manager = SimulationManager()

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def home():
    return "Load Balancer Dashboard Running 🚀"


@app.route("/dashboard")
def dashboard():
    return render_template("index.html")


# -----------------------------
# ▶️ RUN BASELINE (RR / LC)
# -----------------------------
@app.route("/run/baseline", methods=["POST"])
def run_baseline():
    traffic_mode = request.json.get("traffic", "mixed")

    sim_manager.run_baseline(traffic_mode)

    return jsonify({"status": "Baseline simulation completed"})


# -----------------------------
# 🧠 TRAIN ML
# -----------------------------
@app.route("/train/ml", methods=["POST"])
def train_ml():
    sim_manager.train_ml()
    return jsonify({"status": "ML model trained"})


# -----------------------------
# 🤖 TRAIN RL
# -----------------------------
@app.route("/train/rl", methods=["POST"])
def train_rl():
    sim_manager.train_rl()
    return jsonify({"status": "RL model trained"})


# -----------------------------
# 🚀 RUN SMART (ML / RL)
# -----------------------------
@app.route("/run/smart", methods=["POST"])
def run_smart():
    strategy = request.json.get("strategy", "ml")  # "ml" or "rl"
    traffic_mode = request.json.get("traffic", "mixed")

    sim_manager.run_smart(strategy, traffic_mode)

    return jsonify({"status": f"{strategy.upper()} simulation completed"})


# -----------------------------
# 📊 METRICS
# -----------------------------
@app.route("/metrics")
def metrics():
    return jsonify(sim_manager.get_metrics())


# -----------------------------
# 📡 TRAFFIC STREAM (REAL-TIME)
# -----------------------------
latest_index = 0

@app.route("/traffic")
def traffic():
    global latest_index

    data = get_request_log("rl")  # can switch dynamically later

    if not data:
        return jsonify({"message": "No data yet"})

    if latest_index >= len(data):
        latest_index = 0

    req = data[latest_index]
    latest_index += 1

    return jsonify({
        "request_id": req.get("request_id"),
        "server": req.get("server"),
        "latency": req.get("latency"),
        "status": req.get("status"),
        "fallback": req.get("fallback_used", False)
    })


# -----------------------------
# 🔄 RESET SYSTEM
# -----------------------------
@app.route("/reset", methods=["POST"])
def reset():
    sim_manager.reset()
    return jsonify({"status": "System reset complete"})


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)