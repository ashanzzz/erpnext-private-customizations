import os
import sys
import time
import requests

sys.stdout.reconfigure(encoding='utf-8')

url = "http://192.168.8.11:6888/login"
print("Waiting for site to become healthy...")

for i in range(30):
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            print(f"[OK] Site is up and healthy! (took {i*2}s)")
            break
    except Exception:
        pass
    time.sleep(2)
