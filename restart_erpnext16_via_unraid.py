import os
import json
import time
import urllib.request

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
GQL_URL = os.getenv('UNRAID_GRAPHQL_URL', 'http://192.168.8.11/graphql')
API_KEY = os.getenv('UNRAID_OFFICIAL_API_KEY', '')

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

CONTAINER_ID = "a9f5cca8989477b947e14fb0382850d22f032321ad8ce096f7fa14b234454cfa"

print("1. Stopping container erpnext16 via Unraid GraphQL...")
stop_query = {
    "query": f'mutation {{ docker {{ stop(id: "{CONTAINER_ID}") {{ id state status }} }} }}'
}
req = urllib.request.Request(GQL_URL, data=json.dumps(stop_query).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print("Stop Response:", resp.read().decode('utf-8'))
except Exception as e:
    print("Stop error:", e)

time.sleep(3)

print("2. Starting container erpnext16 via Unraid GraphQL...")
start_query = {
    "query": f'mutation {{ docker {{ start(id: "{CONTAINER_ID}") {{ id state status }} }} }}'
}
req = urllib.request.Request(GQL_URL, data=json.dumps(start_query).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print("Start Response:", resp.read().decode('utf-8'))
except Exception as e:
    print("Start error:", e)

