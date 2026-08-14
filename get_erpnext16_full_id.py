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
    "query": "query { docker { containers { id names state status image } } }"
}

req = urllib.request.Request(GQL_URL, data=json.dumps(query).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        containers = data.get('data', {}).get('docker', {}).get('containers', [])
        for c in containers:
            if '/erpnext16' in c.get('names', []):
                print("FOUND ERPNEXT16 CONTAINER:")
                print("Full ID:", c.get('id'))
                print("Names:", c.get('names'))
                print("State:", c.get('state'))
                print("Status:", c.get('status'))
except Exception as e:
    print("Error:", e)

