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

candidate_fields = [
    "id", "names", "image", "state", "status", "created", "ports", "labels", "mounts", "command"
]

valid_f = []
for f in candidate_fields:
    try:
        q = f"query {{ docker {{ containers {{ {f} }} }} }}"
        req = urllib.request.Request(GQL_URL, data=json.dumps({"query": q}).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            valid_f.append(f)
    except urllib.error.HTTPError:
        pass

print("Valid DockerContainer fields:", valid_f)

query = {
    "query": f"query {{ docker {{ containers {{ {' '.join(valid_f)} }} }} }}"
}

req = urllib.request.Request(GQL_URL, data=json.dumps(query).encode('utf-8'), headers=headers)
with urllib.request.urlopen(req, timeout=5) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    containers = data.get('data', {}).get('docker', {}).get('containers', [])
    for c in containers:
        if '/erpnext16' in c.get('names', []):
            print("ERPNext 16 Container Info:")
            print(json.dumps(c, indent=2, ensure_ascii=False))

