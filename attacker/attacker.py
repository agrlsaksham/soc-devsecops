import requests
import time
import random

URL = "http://127.0.0.1:5000/"   # 🔥 use 127.0.0.1 (more stable than localhost)

fake_ips = ["192.168.1.1", "10.0.0.2", "172.16.0.3"]

for i in range(20):
    data = {
        "username": "admin",
        "password": "wrong",
        "ip": random.choice(fake_ips)   # simulate different IPs
    }

    try:
        r = requests.post(URL, data=data, timeout=5)
        print(f"[{i}] OK {r.status_code}")

    except Exception as e:
        print(f"[{i}] ERROR:", e)

    time.sleep(1.2)   # 🔥 VERY IMPORTANT (prevent crash)