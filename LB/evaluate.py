import simpy
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from servers import Server
from traffic import traffic_generator
from loadbalancers import RoundRobinLB, LeastConnectionsLB, MLLB

# Load ML model
with open("rf_model.pkl", "rb") as f:
    rf = pickle.load(f)

def evaluate_lb(lb_class, model=None):
    env = simpy.Environment()
    servers = [
        Server(env, "S0", speed_factor=1.0),
        Server(env, "S1", speed_factor=0.7),
        Server(env, "S2", speed_factor=1.3)
    ]
    data_log = []
    lb = lb_class() if model is None else lb_class(model)
    env.process(traffic_generator(env, servers, lb, data_log))
    env.run(until=100)
    df = pd.DataFrame(data_log)
    avg_resp = df['response_time'].mean()
    p99_resp = df['response_time'].quantile(0.99)
    cpu_var = df.groupby('server')['cpu'].mean().var()
    throughput = len(df)/100
    return avg_resp, p99_resp, cpu_var, throughput

results = {}
results['RoundRobin'] = evaluate_lb(RoundRobinLB)
results['LeastConnections'] = evaluate_lb(LeastConnectionsLB)
results['MLLB'] = evaluate_lb(MLLB, rf)

# Print results
for lb, metrics in results.items():
    print(f"{lb}: Avg RT={metrics[0]:.2f}, P99 RT={metrics[1]:.2f}, CPU Var={metrics[2]:.2f}, Throughput={metrics[3]:.2f}")

# Dashboard
labels = list(results.keys())
avg_rt = [results[lb][0] for lb in labels]
p99 = [results[lb][1] for lb in labels]
cpu_var = [results[lb][2] for lb in labels]

x = range(len(labels))
plt.figure(figsize=(10,6))
plt.bar([i-0.2 for i in x], avg_rt, 0.2, label='Avg RT')
plt.bar(x, p99, 0.2, label='P99 RT')
plt.bar([i+0.2 for i in x], cpu_var, 0.2, label='CPU Var')
plt.xticks(x, labels)
plt.ylabel('Metric Value')
plt.title('Load Balancer Evaluation')
plt.legend()
plt.show()