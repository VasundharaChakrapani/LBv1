import simpy
import pandas as pd
import random
import pickle

from servers import Server
from traffic import traffic_generator
from loadbalancers import RoundRobinLB
from sklearn.ensemble import RandomForestRegressor


# -----------------------------
# 🧠 TRAIN ML MODEL
# -----------------------------
def train_model(runs=10, duration=5000):
    data_log = []

    for _ in range(runs):
        env = simpy.Environment()

        # Randomize server speeds (diverse training data)
        servers = [
            Server(env, "S0", speed_factor=random.uniform(0.9, 1.1)),
            Server(env, "S1", speed_factor=random.uniform(0.6, 0.8)),
            Server(env, "S2", speed_factor=random.uniform(1.2, 1.4))
        ]

        rr_lb = RoundRobinLB()

        # Request counter
        request_counter = {"count": 0}

        env.process(
            traffic_generator(
                env,
                servers,
                rr_lb,
                data_log,
                duration=duration,
                request_counter=request_counter
            )
        )

        env.run(until=duration)

    # -----------------------------
    # 📊 Prepare Data
    # -----------------------------
    df = pd.DataFrame(data_log)

    # Keep only successful requests
    df = df[df["status"] == "success"]

    if df.empty:
        raise ValueError("No valid training data collected!")

    features = ['cpu', 'mem', 'connections']
    target = 'latency'

    # -----------------------------
    # 🌲 Train Model
    # -----------------------------
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(df[features], df[target])

    # -----------------------------
    # 💾 Save Model
    # -----------------------------
    with open("rf_model.pkl", "wb") as f:
        pickle.dump(rf, f)

    print("✅ Random Forest trained and saved as rf_model.pkl")

    return rf


# -----------------------------
# CLI RUN
# -----------------------------
if __name__ == "__main__":
    train_model()