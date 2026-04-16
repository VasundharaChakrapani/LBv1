import simpy
import random


class Server:
    def __init__(self, env, name, speed_factor=1.0, failure_rate=0.05):
        self.env = env
        self.name = name
        self.speed_factor = speed_factor  # >1 = faster, <1 = slower
        self.failure_rate = failure_rate  # probability of failure

        # Resource stats
        self.cpu = 0
        self.mem = 0
        self.connections = 0
        self.requests = 0

        self.is_alive = True  # for failure simulation

    def handle_request(self, req_time, request_id=None):
        start_time = self.env.now

        # 🔴 Simulate random failure
        if random.random() < self.failure_rate:
            self.is_alive = False
            return {
                "request_id": request_id,
                "server": self.name,
                "latency": None,
                "cpu": self.cpu,
                "mem": self.mem,
                "connections": self.connections,
                "status": "failed"
            }

        # 🟢 Process request
        self.connections += 1

        cpu_increase = random.uniform(5, 15)
        mem_increase = random.uniform(1, 5)

        self.cpu += cpu_increase
        self.mem += mem_increase

        # Load affects latency
        load_factor = 1 + (self.connections * 0.1)
        adjusted_time = (req_time * load_factor) / self.speed_factor

        # Simulate processing time
        yield self.env.timeout(adjusted_time)

        # Release resources safely
        self.cpu = max(0, self.cpu - cpu_increase)
        self.mem = max(0, self.mem - mem_increase)
        self.connections -= 1
        self.requests += 1

        end_time = self.env.now
        latency = end_time - start_time

        return {
            "request_id": request_id,
            "server": self.name,
            "latency": latency,
            "cpu": self.cpu,
            "mem": self.mem,
            "connections": self.connections,
            "status": "success"
        }

    def get_state(self):
        """Used by ML/RL/UI to check current server status"""
        return {
            "server": self.name,
            "cpu": self.cpu,
            "mem": self.mem,
            "connections": self.connections,
            "alive": self.is_alive
        }