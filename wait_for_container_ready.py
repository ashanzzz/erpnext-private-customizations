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

print("Checking container status...")
for i in range(15):
    query = {
        "query": "query { docker { containers { id names state status } } }"
    }
    try:
        req = urllib.request.Request(GQL_URL, data=json.dumps(query).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            containers = data.get('data', {}).get('docker', {}).get('containers', [])
            for c in containers:
                if '/erpnext16' in c.get('names', []):
                    print(f"[{i+1}] ERPNext 16 State: {c.get('state')} | Status: {c.get('status')}")
                    if "healthy" in c.get('status', '').lower() or "up" in c.get('status', '').lower():
                        # Try pinging port 6888
                        try:
                            with urllib.request.urlopen("http://192.168.8.11:6888/login", timeout=2) as hresp:
                                print(f"ERPNext 16 HTTP Response: {hresp.status} OK!")
                                exit(0)
                        except Exception as he:
                            print(f"HTTP port not ready yet: {he}")
    except Exception as e:
        print("Error checking:", e)
    time.sleep(3)

