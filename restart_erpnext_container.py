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
GRAPHQL_URL = os.getenv('UNRAID_GRAPHQL_URL', 'http://192.168.8.11/graphql')
API_KEY = os.getenv('UNRAID_OFFICIAL_API_KEY', '')

print("Attempting container restart via Unraid GraphQL API...")

query = """
mutation RestartContainer($id: ID!) {
  dockerContainerRestart(id: $id)
}
"""

req_data = {
    "query": query,
    "variables": {"id": "erpnext16"}
}

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

req = urllib.request.Request(GRAPHQL_URL, data=json.dumps(req_data).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Unraid GraphQL Response:", res)
except Exception as e:
    print("GraphQL request error:", e)

