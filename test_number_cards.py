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
        return {"error": err_body}

def main():
    # Let's get the exact names of the number cards
    endpoint = '/api/resource/Number%20Card?fields=["name","document_type"]&limit_page_length=500'
    res = call_api(endpoint)
    if 'error' in res:
        print(f"Error fetching cards: {res['error']}")
        return

    cards = res.get('data', [])
    for card in cards:
        name = card['name']
        dt = card['document_type']
        
        # Now fetch the result
        enc_name = urllib.parse.quote(name)
        result_endpoint = f"/api/method/frappe.desk.doctype.number_card.number_card.get_result?doc=%7B%22name%22:%22{enc_name}%22%7D&filters=%5B%5D"
        
        card_res = call_api(result_endpoint)
        if card_res and 'error' in card_res:
            print(f"[{dt}] {name} => ERROR: {card_res['error']}")
        elif card_res and 'message' in card_res:
            print(f"[{dt}] {name} => {card_res['message']}")
        else:
            print(f"[{dt}] {name} => NO DATA")

if __name__ == '__main__':
    main()
