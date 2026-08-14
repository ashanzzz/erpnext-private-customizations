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

# Test fields on Container type
candidate_container_fields = ["id", "names", "name", "state", "status", "image", "created"]

# Let's probe subfields
for cf in candidate_container_fields:
    try:
        q = f"query {{ docker {{ containers {{ {cf} }} }} }}"
        req = urllib.request.Request(GQL_URL, data=json.dumps({"query": q}).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"Container field '{cf}': SUCCESS -> {len(data.get('data',{}).get('docker',{}).get('containers',[]))} items")
    except urllib.error.HTTPError as e:
        print(f"Container field '{cf}': Error ->", e.read().decode('utf-8')[:120])

