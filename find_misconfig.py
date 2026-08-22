import os
import json
import urllib.request
import urllib.parse

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
TOKEN = os.getenv('ERPNEXT_TOKEN', '')

def call_api(endpoint, method='GET', data=None):
    headers = {
        'Authorization': TOKEN,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    req_url = f"{SITE_URL.rstrip('/')}{endpoint}"
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    
    req = urllib.request.Request(req_url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        return None

def check_doc(dt):
    endpoint = f'/api/resource/{urllib.parse.quote(dt)}?fields=["*"]&limit_page_length=500'
    res = call_api(endpoint)
    if res and 'data' in res:
        for doc in res['data']:
            if doc.get('document_type') == 'Oil Card Refuel Log':
                if doc.get('aggregate_function_based_on') == 'total_amount':
                    print(f"[{dt}] MISCONFIGURED {doc.get('name')}: using total_amount on Oil Card Refuel Log")
                
                # Check for value_based_on in Dashboard Chart
                if doc.get('value_based_on') == 'total_amount':
                    print(f"[{dt}] MISCONFIGURED {doc.get('name')}: using total_amount on Oil Card Refuel Log")

def main():
    print("Checking Number Cards...")
    check_doc('Number Card')
    print("Checking Dashboard Charts...")
    check_doc('Dashboard Chart')

if __name__ == '__main__':
    main()
