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

candidate_roots = [
    "servers", "server", "user", "users", "account", "apps", "plugins", "notifications",
    "system", "settings", "os", "flash", "arrays", "docker", "containers", "terminal",
    "command", "exec", "state", "status", "connect"
]

valid_roots = []
for r in candidate_roots:
    try:
        req = urllib.request.Request(GQL_URL, data=json.dumps({"query": f"query {{ {r} }}"}).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"Root query '{r}': SUCCESS ->", resp.read().decode('utf-8')[:200])
            valid_roots.append(r)
    except urllib.error.HTTPError as e:
        msg = e.read().decode('utf-8')
        if "Field" in msg or "selection of subfields" in msg:
            print(f"Root query '{r}': EXISTS (needs subfields)")
            valid_roots.append(r)

print("\nValid root queries:", valid_roots)

