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

# Test Unraid Connect GraphQL API
headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

test_queries = [
    {"query": "query { getServers { name } }"},
    {"query": "query { server { name state } }"},
    {"query": "query { dockerContainers { id name status } }"},
    {"query": "query { info { osVersion } }"}
]

for q in test_queries:
    try:
        req = urllib.request.Request(GQL_URL, data=json.dumps(q).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            print("GraphQL Query Success:", q['query'], "->", resp.read().decode('utf-8')[:300])
    except urllib.error.HTTPError as e:
        print(f"GraphQL Query {q['query']} Error {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"GraphQL Query {q['query']} Exception:", e)

