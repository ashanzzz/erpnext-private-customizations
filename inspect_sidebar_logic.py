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
    res = call_api('/api/method/frappe.desk.doctype.workspace.workspace.get_workspace_sidebar_items')
    print("--- get_workspace_sidebar_items ---")
    if res and 'message' in res:
        pages = res['message'].get('pages', [])
        print(f"Total sidebar pages returned: {len(pages)}")
        for page in pages:
            print(f"  * Name: {page.get('name')}, Title: {page.get('title')}, Parent: {page.get('parent_page')}, Public: {page.get('public')}")
    else:
        print("API Response/Error:", res)

if __name__ == '__main__':
    main()
