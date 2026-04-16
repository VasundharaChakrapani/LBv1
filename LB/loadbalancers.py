import numpy as np
import random


# -----------------------------
# 🔧 HELPER: fallback mechanism
# -----------------------------
def try_servers(env, servers, primary_idx, req_time, request_id):
    """Try primary server, fallback if failed"""
    order = list(range(len(servers)))

    # Put chosen server first
    order.remove(primary_idx)
    order.insert(0, primary_idx)

    for idx in order:
        server = servers[idx]

        result = yield env.process(server.handle_request(req_time, request_id))

        if result["status"] == "success":
            result["fallback_used"] = (idx != primary_idx)
            return result

    # If all servers fail
    return {
        "request_id": request_id,
        "server": None,
        "latency": None,
        "status": "all_failed",
        "fallback_used": True
    }


# -----------------------------
# ROUND ROBIN
# -----------------------------
class RoundRobinLB:
    def __init__(self):
        self.idx = 0

    def route_request(self, env, servers, data_log, request_id):
        primary_idx = self.idx % len(servers)
        self.idx += 1

        req_time = random.uniform(1, 3)

        result = yield env.process(
            try_servers(env, servers, primary_idx, req_time, request_id)
        )

        data_log.append(result)


# -----------------------------
# LEAST CONNECTIONS
# -----------------------------
class LeastConnectionsLB:
    def route_request(self, env, servers, data_log, request_id):
        primary_idx = min(range(len(servers)), key=lambda i: servers[i].connections)

        req_time = random.uniform(1, 3)

        result = yield env.process(
            try_servers(env, servers, primary_idx, req_time, request_id)
        )

        data_log.append(result)


# -----------------------------
# ML LOAD BALANCER
# -----------------------------
class MLLB:
    def __init__(self, model, cpu_penalty=0.3):
        self.model = model
        self.cpu_penalty = cpu_penalty

    def route_request(self, env, servers, data_log, request_id):
        X = np.array([[s.cpu, s.mem, s.connections] for s in servers])
        preds = self.model.predict(X)

        adjusted_scores = [
            pred + self.cpu_penalty * s.cpu
            for pred, s in zip(preds, servers)
        ]

        primary_idx = int(np.argmin(adjusted_scores))

        req_time = np.random.uniform(1, 3)

        result = yield env.process(
            try_servers(env, servers, primary_idx, req_time, request_id)
        )

        # Add explainability (🔥 UI feature)
        result["ml_info"] = {
            "predictions": preds.tolist(),
            "chosen_server": servers[primary_idx].name
        }

        data_log.append(result)


# -----------------------------
# RL LOAD BALANCER
# -----------------------------
class RLLB:
    def __init__(self, epsilon=0.1):
        self.q_table = {}
        self.epsilon = epsilon

    def get_state(self, servers):
        state = []
        for s in servers:
            cpu_bucket = max(0, min(int(s.cpu / 20), 5))
            conn_bucket = max(0, min(int(s.connections / 5), 5))
            state.append((cpu_bucket, conn_bucket))

        return tuple(state)   # ✅ FIXED (outside loop)

    def choose_action(self, state, n_servers):
        if random.random() < self.epsilon:
            return random.randint(0, n_servers - 1)

        if state not in self.q_table:
            self.q_table[state] = [0] * n_servers

        q_values = self.q_table[state]
        max_q = max(q_values)

        best_actions = [i for i, q in enumerate(q_values) if q == max_q]
        return random.choice(best_actions)

    def update_q(self, state, action, reward, next_state, n_servers):
        alpha = 0.1
        gamma = 0.9

        if state not in self.q_table:
            self.q_table[state] = [0] * n_servers
        if next_state not in self.q_table:
            self.q_table[next_state] = [0] * n_servers

        old_value = self.q_table[state][action]
        next_max = max(self.q_table[next_state])

        self.q_table[state][action] = old_value + alpha * (
            reward + gamma * next_max - old_value
        )

    def route_request(self, env, servers, data_log, request_id):
        n_servers = len(servers)

        state = self.get_state(servers)

        # Warmup
        if len(self.q_table) < 50:
            action = random.randint(0, n_servers - 1)
        else:
            action = self.choose_action(state, n_servers)

        req_time = random.uniform(1, 3)

        result = yield env.process(
            try_servers(env, servers, action, req_time, request_id)
        )

        # Compute reward ONLY if success
        if result["status"] == "success":
            response_time = result["latency"]

            avg_cpu = np.mean([s.cpu for s in servers])
            imbalance = abs(servers[action].cpu - avg_cpu)

            reward = -(response_time + 0.1 * imbalance) / 10.0

            next_state = self.get_state(servers)
            self.update_q(state, action, reward, next_state, n_servers)

            result["rl_info"] = {
                "state": state,
                "action": action,
                "reward": reward
            }

        data_log.append(result)

        # decay epsilon
        self.epsilon = max(0.01, self.epsilon * 0.99)