import os
import json
import urllib.request
import urllib.parse
import http.client

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

UNRAID_IP = "192.168.8.11"
GQL_URL = os.getenv('UNRAID_GRAPHQL_URL', f'http://{UNRAID_IP}/graphql')
OFFICIAL_KEY = os.getenv('UNRAID_OFFICIAL_API_KEY', '')
CLAW_URL = os.getenv('UNRAIDCLAW_URL', f'http://{UNRAID_IP}:9876')
CLAW_KEY = os.getenv('UNRAIDCLAW_API_KEY', '')

print("=== 1. Testing Unraid Official GraphQL API ===")
# Try different header formats for Unraid official API
headers_list = [
    {"x-api-key": OFFICIAL_KEY, "Content-Type": "application/json"},
    {"Authorization": f"Bearer {OFFICIAL_KEY}", "Content-Type": "application/json"},
    {"API-Key": OFFICIAL_KEY, "Content-Type": "application/json"}
]

gql_query = json.dumps({"query": "{ __schema { types { name } } }"})

for idx, hdrs in enumerate(headers_list):
    try:
        req = urllib.request.Request(GQL_URL, data=gql_query.encode('utf-8'), headers=hdrs)
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode('utf-8')
            print(f"GraphQL Header #{idx+1} SUCCESS! Response snippet:", content[:200])
            break
    except Exception as e:
        print(f"GraphQL Header #{idx+1} Error:", e)

print("\n=== 2. Testing UnraidClaw / Gateway Ports on 192.168.8.11 ===")
for port in [9876, 80, 443, 22, 2375, 2376, 8888, 6888, 8000, 9000, 3000]:
    try:
        conn = http.client.HTTPConnection(UNRAID_IP, port, timeout=2)
        conn.request("GET", "/")
        resp = conn.getresponse()
        print(f"Port {port}: HTTP {resp.status} {resp.reason}")
        conn.close()
    except Exception as e:
        pass

print("\n=== 3. Testing UnraidClaw API endpoints ===")
claw_endpoints = ["/containers", "/api/containers", "/api/exec", "/api/v1/containers", "/status", "/health"]
for ep in claw_endpoints:
    try:
        req = urllib.request.Request(f"{CLAW_URL}{ep}", headers={"Authorization": f"Bearer {CLAW_KEY}", "x-api-key": CLAW_KEY})
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"UnraidClaw {ep}: {resp.status} ->", resp.read().decode('utf-8')[:200])
    except Exception as e:
        print(f"UnraidClaw {ep} Error:", e)

