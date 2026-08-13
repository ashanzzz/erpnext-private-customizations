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
TOKEN = os.getenv('ERPNEXT_TOKEN', 'token 781e6538a0816f3:ebfe8d61c03e289')

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
    # In Frappe 16, updating sidebar for a user is done via user settings
    # Key: "workspace:sidebar" or "Workspace"
    # Let's try calling frappe.model.utils.user_settings.save with user_settings containing pages
    
    pages = [
        {"name": "Home", "title": "Home", "type": "workspace"},
        {"name": "My Business", "title": "我的业务", "type": "workspace"},
        {"name": "Vehicle Management", "title": "车油管理", "type": "workspace", "parent_page": "My Business"},
        {"name": "Compliance Center", "title": "公司合规中心", "type": "workspace", "parent_page": "My Business"},
        {"name": "Reimbursements", "title": "报销申请", "type": "workspace", "parent_page": "My Business"},
        {"name": "Oil Cards", "title": "油卡", "type": "workspace", "parent_page": "My Business"}
    ]
    
    # Save for user_settings
    res = call_api('/api/method/frappe.model.utils.user_settings.save', method='POST', data={
        "doctype": "Workspace",
        "user_settings": json.dumps({"sidebar_items": pages})
    })
    print("Save User Settings result:", res)

if __name__ == '__main__':
    main()
