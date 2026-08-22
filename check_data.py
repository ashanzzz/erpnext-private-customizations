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
        err_body = e.read().decode('utf-8')
        print(f"Error {e.code} on {endpoint}: {err_body}")
        return None

def get_count(dt):
    encoded = urllib.parse.quote(dt)
    res = call_api(f'/api/resource/{encoded}?limit_page_length=0')
    if res and 'data' in res:
        return len(res['data'])
    return 0

def get_number_cards():
    endpoint = '/api/resource/Number%20Card?fields=["name","document_type","function","aggregate_function_based_on","filters_json","dynamic_filters_json","report_function","is_public"]&limit_page_length=100'
    res = call_api(endpoint)
    return res.get('data', []) if res else []

def main():
    print("Record counts:")
    for dt in ['Oil Card Refuel Log', 'Purchase Order', 'Reimbursement Request', 'Oil Card']:
        print(f"{dt}: {get_count(dt)}")
        
    print("\nDetailed Number Card check:")
    cards = get_number_cards()
    for card in cards:
        if card.get('document_type') == 'Oil Card Refuel Log':
            print(json.dumps(card, ensure_ascii=False))

if __name__ == '__main__':
    main()
