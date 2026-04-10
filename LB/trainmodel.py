import simpy
import pandas as pd
from servers import Server
from traffic import traffic_generator
from loadbalancers import RoundRobinLB
from sklearn.ensemble import RandomForestRegressor
import pickle
import random


data_log = []

# Multi-run training with random server speeds
for _ in range(10):
    env = simpy.Environment()
    servers = [
        Server(env, "S0", speed_factor=random.uniform(0.9, 1.1)),
        Server(env, "S1", speed_factor=random.uniform(0.6, 0.8)),
        Server(env, "S2", speed_factor=random.uniform(1.2, 1.4))
    ]
    rr_lb = RoundRobinLB()
    env.process(traffic_generator(env, servers, rr_lb, data_log))
    env.run(until=10000) # longer run for more data- 10000 simulation time units-collects more diverse data

df = pd.DataFrame(data_log)
features = ['cpu', 'mem', 'connections']
target = 'response_time'

rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(df[features], df[target])

with open("rf_model.pkl", "wb") as f:
    pickle.dump(rf, f)

print("Random Forest trained on diverse traffic and saved as rf_model.pkl")