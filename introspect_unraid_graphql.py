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

schema_query = {
    "query": """
    query {
        __schema {
            queryType {
                fields {
                    name
                }
            }
            mutationType {
                fields {
                    name
                }
            }
        }
    }
    """
}

req = urllib.request.Request(GQL_URL, data=json.dumps(schema_query).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("=== UNRAID GRAPHQL SCHEMA INTROSPECTION ===")
        queries = [f['name'] for f in res.get('data', {}).get('__schema', {}).get('queryType', {}).get('fields', [])]
        mutations = [f['name'] for f in res.get('data', {}).get('__schema', {}).get('mutationType', {}).get('fields', [])]
        print("Available Queries:", queries)
        print("Available Mutations:", mutations)
except Exception as e:
    print("Introspection error:", e)

