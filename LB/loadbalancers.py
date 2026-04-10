import numpy as np
import random


class RoundRobinLB:
    def __init__(self):
        self.idx = 0

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