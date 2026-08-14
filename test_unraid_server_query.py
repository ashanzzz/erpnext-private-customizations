import os
import json
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

query = {
    "query": "query { server { name status } }"
}

req = urllib.request.Request(GQL_URL, data=json.dumps(query).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        print("Unraid Server info:", resp.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)

