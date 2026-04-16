import simpy
import pickle

from servers import Server
from traffic import traffic_generator
from loadbalancers import (
    RoundRobinLB,
    LeastConnectionsLB,
    MLLB,
    RLLB
)
from evaluate import compute_metrics
from trainmodel import train_model


class SimulationManager:
    def __init__(self):
        self.data_logs = {
            "baseline": [],
            "ml": [],
            "rl": []
        }

        self.model = None
        self.rl_agent = None

    # -----------------------------
    # 🔧 CREATE SERVERS
    # -----------------------------
    def _create_servers(self, env):
        return [
            Server(env, "S0", speed_factor=1.0),
            Server(env, "S1", speed_factor=0.7),
            Server(env, "S2", speed_factor=1.3)
        ]

    # -----------------------------
    # ▶️ BASELINE RUN
    # -----------------------------
    def run_baseline(self, traffic_mode="mixed", duration=100):
        env = simpy.Environment()
        servers = self._create_servers(env)

        data_log = []
        request_counter = {"count": 0}

        lb = RoundRobinLB()  # can extend to LeastConnections later

        env.process(
            traffic_generator(
                env,
                servers,
                lb,
                data_log,
                duration=duration,
                traffic_mode=traffic_mode,
                request_counter=request_counter
            )
        )

        env.run(until=duration)

        self.data_logs["baseline"] = data_log

    # -----------------------------
    # 🧠 TRAIN ML
    # -----------------------------
    def train_ml(self):
        self.model = train_model()

    # -----------------------------
    # 🤖 TRAIN RL
    # -----------------------------
    def train_rl(self, duration=200):
        env = simpy.Environment()
        servers = self._create_servers(env)

        request_counter = {"count": 0}
        self.rl_agent = RLLB()

    # No data_log stored
        temp_log = []

        env.process(
            traffic_generator(
            env,
            servers,
            self.rl_agent,
            temp_log,
            duration=duration,
            request_counter=request_counter
        )
    )

        env.run(until=duration)
    # -----------------------------
    # 🚀 RUN SMART
    # -----------------------------
    def run_smart(self, strategy="ml", traffic_mode="mixed", duration=100):
        env = simpy.Environment()
        servers = self._create_servers(env)

        data_log = []
        request_counter = {"count": 0}

        if strategy == "ml":
            if self.model is None:
                # load if not trained in memory
                with open("rf_model.pkl", "rb") as f:
                    self.model = pickle.load(f)

            lb = MLLB(self.model)

        elif strategy == "rl":
            if self.rl_agent is None:
                self.rl_agent = RLLB()

            lb = self.rl_agent

        else:
            raise ValueError("Invalid strategy")

        env.process(
            traffic_generator(
                env,
                servers,
                lb,
                data_log,
                duration=duration,
                traffic_mode=traffic_mode,
                request_counter=request_counter
            )
        )

        env.run(until=duration)

        self.data_logs[strategy] = data_log

    # -----------------------------
    # 📊 GET METRICS
    # -----------------------------
    def get_metrics(self):
        results = {}

        for key, log in self.data_logs.items():
            if log:
                results[key] = compute_metrics(log)
            else:
                results[key] = {}

        return results

    # -----------------------------
    # 📡 GET LOGS (for UI)
    # -----------------------------
    def get_logs(self, strategy="ml"):
        return self.data_logs.get(strategy, [])

    # -----------------------------
    # 🔄 RESET
    # -----------------------------
    def reset(self):
        self.data_logs = {
            "baseline": [],
            "ml": [],
            "rl": []
        }

        self.model = None
        self.rl_agent = None