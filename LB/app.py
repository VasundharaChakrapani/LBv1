from flask import Flask, jsonify, render_template, request
from simulation_manager import SimulationManager

app = Flask(__name__)

# -----------------------------
# GLOBAL STATE
# -----------------------------
sim_manager = SimulationManager()

current_strategy = None
latest_index = 0


# -----------------------------
# SORT LOGS BY REQUEST ID
# -----------------------------
def get_sorted_logs(strategy):
    logs = sim_manager.get_logs(strategy)

    return sorted(
        logs,
        key=lambda x: x.get("request_id", 0)
    )


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    return "Load Balancer Dashboard Running 🚀"


@app.route("/dashboard")
def dashboard():
    return render_template("index.html")


# -----------------------------
# BASELINE
# -----------------------------
@app.route("/run/baseline", methods=["POST"])
def run_baseline():
    global current_strategy, latest_index

    traffic_mode = request.json.get("traffic", "mixed")

    sim_manager.run_baseline(traffic_mode)

    current_strategy = "baseline"
    latest_index = 0

    return jsonify({"status": "Baseline simulation completed"})


# -----------------------------
# TRAIN ML
# -----------------------------
@app.route("/train/ml", methods=["POST"])
def train_ml():
    sim_manager.train_ml()
    return jsonify({"status": "ML model trained"})


# -----------------------------
# TRAIN RL
# -----------------------------
@app.route("/train/rl", methods=["POST"])
def train_rl():
    sim_manager.train_rl()
    return jsonify({"status": "RL model trained"})


# -----------------------------
# RUN SMART
# -----------------------------
@app.route("/run/smart", methods=["POST"])
def run_smart():
    global current_strategy, latest_index

    strategy = request.json.get("strategy", "ml")
    traffic_mode = request.json.get("traffic", "mixed")

    sim_manager.run_smart(strategy, traffic_mode)

    current_strategy = strategy
    latest_index = 0

    return jsonify({"status": f"{strategy.upper()} simulation completed"})


# -----------------------------
# METRICS
# -----------------------------
@app.route("/metrics")
def metrics():
    return jsonify(sim_manager.get_metrics())


# -----------------------------
# TRAFFIC STREAM
# -----------------------------
@app.route("/traffic")
def traffic():
    global latest_index, current_strategy

    if current_strategy is None:
        return jsonify({})

    logs = get_sorted_logs(current_strategy)

    if not logs:
        return jsonify({})

    if latest_index >= len(logs):
        latest_index = 0

    req = logs[latest_index]
    latest_index += 1

    return jsonify({
        "strategy": current_strategy.upper(),
        "request_id": req.get("request_id", latest_index),
        "server": req.get("server"),
        "latency": round(req.get("latency", 0), 2),
        "status": req.get("status", "success"),
        "fallback": req.get("fallback_used", False)
    })


# -----------------------------
# RESET
# -----------------------------
@app.route("/reset", methods=["POST"])
def reset():
    global current_strategy, latest_index

    sim_manager.reset()

    current_strategy = None
    latest_index = 0

    return jsonify({"status": "System reset complete"})


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)