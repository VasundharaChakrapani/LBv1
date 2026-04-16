import random


def traffic_generator(
    env,
    servers,
    lb,
    data_log,
    duration=100,
    traffic_mode="mixed",   # "normal", "burst", "mixed"
    request_counter=None
):
    """
    Generates traffic and sends requests to load balancer

    traffic_mode:
        - normal: steady traffic
        - burst: heavy traffic
        - mixed: real-world pattern (default)
    """

    while env.now < duration:

        # -----------------------------
        # 📊 Traffic Pattern Control
        # -----------------------------
        if traffic_mode == "normal":
            interarrival = random.expovariate(1 / 1.5)

        elif traffic_mode == "burst":
            interarrival = random.expovariate(1 / 0.2)

        else:  # mixed
            if 20 < env.now < 50 or 70 < env.now < 90:
                interarrival = random.expovariate(1 / 0.2)
            else:
                interarrival = random.expovariate(1 / 1.5)

        # -----------------------------
        # 🆔 Assign Request ID
        # -----------------------------
        if request_counter is not None:
            request_id = request_counter["count"]
            request_counter["count"] += 1
        else:
            request_id = None

        # -----------------------------
        # 🚀 Send request to LB
        # -----------------------------
        env.process(
            lb.route_request(
                env,
                servers,
                data_log,
                request_id   # ✅ NEW
            )
        )

        # -----------------------------
        # ⏱ Wait before next request
        # -----------------------------
        yield env.timeout(interarrival)