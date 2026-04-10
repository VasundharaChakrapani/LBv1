import random


def traffic_generator(env, servers, lb, data_log, duration=100):
    while env.now < duration:
        # Burst traffic periods
        if 20 < env.now < 50 or 70 < env.now < 90:
            interarrival = random.expovariate(1/0.2)  # heavy bursts
        else:
            interarrival = random.expovariate(1/1.5)  # normal traffic
        env.process(lb.route_request(env, servers, data_log))
        yield env.timeout(interarrival)