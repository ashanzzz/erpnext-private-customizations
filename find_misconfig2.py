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

def check_report():
    endpoint = f'/api/resource/Report?fields=["name","ref_doctype","columns"]&limit_page_length=500'
    res = call_api(endpoint)
    if res and 'data' in res:
        for doc in res['data']:
            if doc.get('ref_doctype') == 'Oil Card Refuel Log':
                # check columns or json
                columns = doc.get('columns', '')
                if columns and 'total_amount' in columns:
                    print(f"Report {doc.get('name')} has total_amount in columns")

def check_number_card_all_fields():
    endpoint = '/api/resource/Number%20Card?fields=["*"]&limit_page_length=500'
    res = call_api(endpoint)
    if res and 'data' in res:
        for doc in res['data']:
            if 'total_amount' in json.dumps(doc) and doc.get('document_type') == 'Oil Card Refuel Log':
                print(f"Number Card {doc.get('name')} contains total_amount somehow!")

def check_dashboard_chart_all_fields():
    endpoint = '/api/resource/Dashboard%20Chart?fields=["*"]&limit_page_length=500'
    res = call_api(endpoint)
    if res and 'data' in res:
        for doc in res['data']:
            if 'total_amount' in json.dumps(doc) and doc.get('document_type') == 'Oil Card Refuel Log':
                print(f"Dashboard Chart {doc.get('name')} contains total_amount somehow!")

def main():
    print("Checking...")
    check_report()
    check_number_card_all_fields()
    check_dashboard_chart_all_fields()
    print("Done.")

if __name__ == '__main__':
    main()
