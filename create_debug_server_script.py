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
        print(f"Error {e.code}: {err_body}")
        return {"error": err_body}

def main():
    script_name = "get_sidebar_debug"
    
    # Server script python code
    py_code = """
import frappe

# Let's inspect Workspaces and how sidebar items are fetched
workspaces = frappe.get_all("Workspace", fields=["name", "title", "parent_page", "public", "is_hidden", "sequence_id", "for_user", "is_standard"])

# Check User Settings for current user
user_settings = frappe.db.get_value("User", frappe.session.user, "user_type")

frappe.response['workspaces'] = workspaces
"""

    payload = {
        "doctype": "Server Script",
        "name": script_name,
        "script_type": "API",
        "api_method": script_name,
        "allow_guest": 0,
        "script": py_code,
        "disabled": 0
    }
    
    enc_name = urllib.parse.quote(script_name)
    existing = call_api(f'/api/resource/Server%20Script/{enc_name}')
    if existing and 'data' in existing:
        call_api(f'/api/resource/Server%20Script/{enc_name}', method='PUT', data=payload)
    else:
        call_api('/api/resource/Server%20Script', method='POST', data=payload)
        
    # Call the API
    res = call_api(f'/api/method/{script_name}')
    print("API output:", json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
