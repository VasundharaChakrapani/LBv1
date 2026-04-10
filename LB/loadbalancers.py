import numpy as np
import random


class RoundRobinLB:
    def __init__(self):
        self.idx = 0
        self.epsilon = 0.1  # exploration rate for RL

    def route_request(self, env, servers, data_log):
        server = servers[self.idx % len(servers)]
        self.idx += 1
        req_time = random.uniform(1, 3)
        start = env.now
        yield env.process(server.handle_request(req_time))
        data_log.append({
            'time': env.now,
            'server': server.name,
            'cpu': server.cpu,
            'mem': server.mem,
            'connections': server.connections,
            'response_time': env.now - start
        })
        self.epsilon = max(0.01, self.epsilon * 0.999)  # decay exploration

class LeastConnectionsLB:
    def route_request(self, env, servers, data_log):
        server = min(servers, key=lambda s: s.connections)
        req_time = random.uniform(1, 3)
        start = env.now
        yield env.process(server.handle_request(req_time))
        data_log.append({
            'time': env.now,
            'server': server.name,
            'cpu': server.cpu,
            'mem': server.mem,
            'connections': server.connections,
            'response_time': env.now - start
        })

class MLLB:
    def __init__(self, model, cpu_penalty=0.3):
        """
        model: trained RandomForestRegressor
        cpu_penalty: weight for CPU in final score (higher = more balanced)
        """
        self.model = model
        self.cpu_penalty = cpu_penalty

    def route_request(self, env, servers, data_log):
        X = np.array([[s.cpu, s.mem, s.connections] for s in servers])
        preds = self.model.predict(X)

        # Add CPU penalty to predicted response time
        adjusted_scores = [pred + self.cpu_penalty * s.cpu for pred, s in zip(preds, servers)]

        server = servers[np.argmin(adjusted_scores)]
        req_time = np.random.uniform(1, 3)
        start = env.now
        yield env.process(server.handle_request(req_time))

        data_log.append({
            'time': env.now,
            'server': server.name,
            'cpu': server.cpu,
            'mem': server.mem,
            'connections': server.connections,
            'response_time': env.now - start
        })

class RLLB:
    def __init__(self, epsilon=0.1):
        self.q_table = {}  # state -> [Q values for each server]
        self.epsilon = epsilon  # exploration rate

    def get_state(self, servers):
        state = []
        for s in servers:
            cpu_bucket = max(0, min(int(s.cpu / 20), 5))
            conn_bucket = max(0, min(int(s.connections / 5), 5))
            state.append((cpu_bucket, conn_bucket))
            return tuple(state)

    def choose_action(self, state, servers):
        import random

        # Exploration
        if random.random() < self.epsilon:
            return random.randint(0, len(servers)-1)

        # Exploitation
        if state not in self.q_table:
            self.q_table[state] = [0]*len(servers)
        q_values = self.q_table[state]
        max_q = max(q_values)

        best_actions = [i for i, q in enumerate(q_values) if q == max_q]
        return random.choice(best_actions)

    def update_q(self, state, action, reward, next_state):
        alpha = 0.1  # learning rate
        gamma = 0.9  # discount factor

        if state not in self.q_table:
            self.q_table[state] = [0]*3
        if next_state not in self.q_table:
            self.q_table[next_state] = [0]*3

        old_value = self.q_table[state][action]
        next_max = max(self.q_table[next_state])

        # Q-learning update
        self.q_table[state][action] = old_value + alpha * (
            reward + gamma * next_max - old_value
        )

    def route_request(self, env, servers, data_log):
        state = self.get_state(servers)
        if len(self.q_table) < 50:
            action = random.randint(0, len(servers)-1)
        else:
            action = self.choose_action(state, servers)
        server = servers[action]
        req_time = random.uniform(1, 3)
        start = env.now
        yield env.process(server.handle_request(req_time))
        response_time = env.now - start
        avg_cpu = np.mean([s.cpu for s in servers])
        imbalance = abs(server.cpu - avg_cpu)

        reward = -response_time - 0.1 * imbalance
        reward = reward / 10.0  # normalize

        next_state = self.get_state(servers)
        self.update_q(state, action, reward, next_state)

        data_log.append({
        'time': env.now,
        'server': server.name,
        'cpu': server.cpu,
        'mem': server.mem,
        'connections': server.connections,
        'response_time': response_time
    })

        print(f"[RL] State={state}, Action=S{action}, Reward={reward:.2f}")

    # Faster decay
        self.epsilon = max(0.01, self.epsilon * 0.99)

# class RLLB:
#     def __init__(self, epsilon=0.2):
#         self.q_table = {}
#         self.epsilon = epsilon

#     # -----------------------------
#     # FIXED STATE REPRESENTATION
#     # -----------------------------
#     def get_state(self, servers):
#         state = []
#         for s in servers:
#             cpu_bucket = int(s.cpu // 20)
#             conn_bucket = int(s.connections // 3)

#             cpu_bucket = min(cpu_bucket, 5)
#             conn_bucket = min(conn_bucket, 5)

#             state.append((cpu_bucket, conn_bucket))

#         return tuple(state)   # ✅ moved OUTSIDE loop

#     # -----------------------------
#     # ACTION SELECTION
#     # -----------------------------
#     def choose_action(self, state, n_servers):
#         if random.random() < self.epsilon:
#             return random.randint(0, n_servers - 1)

#         if state not in self.q_table:
#             self.q_table[state] = [0] * n_servers

#         q_values = self.q_table[state]
#         max_q = max(q_values)

#         best_actions = [i for i, q in enumerate(q_values) if q == max_q]
#         return random.choice(best_actions)

#     # -----------------------------
#     # Q UPDATE (FIXED)
#     # -----------------------------
#     def update_q(self, state, action, reward, next_state, n_servers):
#         alpha = 0.1
#         gamma = 0.9

#         if state not in self.q_table:
#             self.q_table[state] = [0] * n_servers
#         if next_state not in self.q_table:
#             self.q_table[next_state] = [0] * n_servers

#         old_value = self.q_table[state][action]
#         next_max = max(self.q_table[next_state])

#         self.q_table[state][action] = old_value + alpha * (
#             reward + gamma * next_max - old_value
#         )

#     # -----------------------------
#     # MAIN ROUTING FUNCTION
#     # -----------------------------
#     def route_request(self, env, servers, data_log):
#         n_servers = len(servers)

#         state = self.get_state(servers)

#         # Warmup phase (important)
#         if len(self.q_table) < 50:
#             action = random.randint(0, n_servers - 1)
#         else:
#             action = self.choose_action(state, n_servers)

#         server = servers[action]

#         req_time = random.uniform(1, 3)
#         start = env.now

#         yield env.process(server.handle_request(req_time))

#         response_time = env.now - start

#         # -----------------------------
#         # FIXED REWARD FUNCTION 🔥
#         # -----------------------------
#         avg_cpu = np.mean([s.cpu for s in servers])
#         avg_conn = np.mean([s.connections for s in servers])

#         imbalance = abs(server.cpu - avg_cpu) + abs(server.connections - avg_conn)

#         reward = -(response_time + 0.2 * imbalance)
#         reward = reward / 5.0  # normalize

#         next_state = self.get_state(servers)

#         self.update_q(state, action, reward, next_state, n_servers)

#         data_log.append({
#             'time': env.now,
#             'server': server.name,
#             'cpu': server.cpu,
#             'mem': server.mem,
#             'connections': server.connections,
#             'response_time': response_time
#         })

#         print(f"[RL] State={state}, Action=S{action}, Reward={reward:.2f}")

#         # smoother decay
#         self.epsilon = max(0.05, self.epsilon * 0.995)