import simpy
import pandas as pd
import pickle

from servers import Server
from traffic import traffic_generator
from loadbalancers import RoundRobinLB, LeastConnectionsLB, MLLB, RLLB


# -----------------------------
# LOAD ML MODEL
# -----------------------------
try:
    with open("rf_model.pkl", "rb") as f:
        rf = pickle.load(f)
except:
    rf = None


# -----------------------------
# 🔧 CORE METRIC CALCULATION
# -----------------------------
def compute_metrics(data_log, duration=100):
    if not data_log:
        return {}

    df = pd.DataFrame(data_log)

    # Only consider successful requests
    df = df[df["status"] == "success"]

    if df.empty:
        return {}

    avg_resp = df["latency"].mean()
    p99_resp = df["latency"].quantile(0.99)

    cpu_var = df.groupby("server")["cpu"].mean().var()
    throughput = len(df) / duration

    failure_rate = 1 - (len(df) / len(data_log))

    return {
        "avg_rt": float(avg_resp),
        "p99": float(p99_resp),
        "cpu_var": float(cpu_var),
        "throughput": float(throughput),
        "failure_rate": float(failure_rate)
    }


# -----------------------------
# SINGLE LB EVALUATION (OLD STYLE)
# -----------------------------
def evaluate_lb(lb_class, model=None, duration=100):
    env = simpy.Environment()

    servers = [
        Server(env, "S0", speed_factor=1.0),
        Server(env, "S1", speed_factor=0.7),
        Server(env, "S2", speed_factor=1.3)
    ]

    data_log = []

    if model is None:
        lb = lb_class()
    else:
        lb = lb_class(model)

    # Request counter for tracking
    request_counter = {"count": 0}

    env.process(
        traffic_generator(
            env,
            servers,
            lb,
            data_log,
            duration=duration,
            request_counter=request_counter
        )
    )

    env.run(until=duration)

    return compute_metrics(data_log, duration)


# -----------------------------
# API FUNCTION (used by Flask)
# -----------------------------
def evaluate_all():
    return {
        "RoundRobin": evaluate_lb(RoundRobinLB),
        "LeastConnections": evaluate_lb(LeastConnectionsLB),
        "MLLB": evaluate_lb(MLLB, rf) if rf else {},
        "RLLB": evaluate_lb(RLLB)
    }


# -----------------------------
# 🔥 REQUEST LOG (for UI streaming)
# -----------------------------
def get_request_log(lb_type="rr", duration=50):
    env = simpy.Environment()

    servers = [
        Server(env, "S0", speed_factor=1.0),
        Server(env, "S1", speed_factor=0.7),
        Server(env, "S2", speed_factor=1.3)
    ]

    data_log = []

    # Request counter
    request_counter = {"count": 0}

    if lb_type == "rr":
        lb = RoundRobinLB()
    elif lb_type == "ml" and rf:
        lb = MLLB(rf)
    elif lb_type == "rl":
        lb = RLLB()
    else:
        lb = LeastConnectionsLB()

    env.process(
        traffic_generator(
            env,
            servers,
            lb,
            data_log,
            duration=duration,
            request_counter=request_counter
        )
    )

    env.run(until=duration)

    return data_log


# -----------------------------
# CLI MODE (optional)
# -----------------------------
if __name__ == "__main__":
    results = evaluate_all()

    for lb, metrics in results.items():
        print(
            f"{lb}: "
            f"Avg RT={metrics.get('avg_rt', 0):.2f}, "
            f"P99={metrics.get('p99', 0):.2f}, "
            f"CPU Var={metrics.get('cpu_var', 0):.2f}, "
            f"Throughput={metrics.get('throughput', 0):.2f}, "
            f"Failure Rate={metrics.get('failure_rate', 0):.2f}"
        )