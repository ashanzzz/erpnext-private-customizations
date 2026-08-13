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
        return {"error": e.code}

def main():
    # 1. Fetch Workspace Settings single doctype if exists
    ws_settings = call_api('/api/resource/Workspace%20Settings')
    print("Workspace Settings:", ws_settings)
    
    # 2. Fetch User Settings for Desk
    # 3. Check Workspace 'Ashan CN Procurement' vs 'Home'
    # Why is 'Buying' shown on sidebar?
    # In Frappe, Workspaces are shown in sidebar if 'public': 1, 'is_hidden': 0 AND 'module' belongs to an installed app!
    # Is 'Ashan CN Procurement' module enabled for the user?
    # Let's check Module Def for 'Ashan CN Procurement'
    mod_res = call_api('/api/resource/Module%20Def/Ashan%20CN%20Procurement')
    print("Module Def:", mod_res.get('data', {}).get('app_name'))

if __name__ == '__main__':
    main()
