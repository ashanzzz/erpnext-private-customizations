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

candidate_mutations = [
    "restartContainer", "startContainer", "stopContainer", "dockerRestart", "restartDockerContainer",
    "containerRestart", "dockerAction", "mutateContainer", "executeCommand"
]

for m in candidate_mutations:
    try:
        req = urllib.request.Request(GQL_URL, data=json.dumps({"query": f"mutation {{ {m} }}"}).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"Mutation '{m}' SUCCESS:", resp.read().decode('utf-8')[:300])
    except urllib.error.HTTPError as e:
        msg = e.read().decode('utf-8')
        if "Field" in msg or "selection of subfields" in msg or "argument" in msg:
            print(f"Mutation '{m}' EXISTS! ->", msg[:150])

