import simpy
import random


class Server:
    def __init__(self, env, name, speed_factor=1.0):
        self.env = env
        self.name = name
        self.speed_factor = speed_factor  # >1 = faster, <1 = slower
        self.cpu = 0
        self.mem = 0
        self.connections = 0
        self.requests = 0

    def handle_request(self, req_time):
        self.connections += 1
        self.cpu += random.uniform(5, 15)
        self.mem += random.uniform(1, 5)
        adjusted_time = req_time / self.speed_factor  # slower/faster server
        yield self.env.timeout(adjusted_time)
        self.cpu -= random.uniform(5, 15)
        self.mem -= random.uniform(1, 5)
        self.connections -= 1
        self.requests += 1