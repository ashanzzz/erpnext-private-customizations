import os
import json
import urllib.request
from http.cookiejar import CookieJar

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
SITE_URL = 'http://192.168.8.11:6888'
USER = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_req = urllib.request.Request(
    f"{SITE_URL}/api/method/login",
    data=json.dumps({'usr': USER, 'pwd': PWD}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
opener.open(login_req)

def call_api(endpoint, method='GET', data=None):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    req_url = f"{SITE_URL.rstrip('/')}{endpoint}"
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    
    req = urllib.request.Request(req_url, data=encoded_data, headers=headers, method=method)
    try:
        with opener.open(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        print(f"API Error {e.code}: {e.read().decode('utf-8')}")
        return None

# Fetch current Navbar Settings
navbar = call_api('/api/resource/Navbar%20Settings/Navbar%20Settings')
if navbar and 'data' in navbar:
    nb_data = navbar['data']
    settings_dropdown = nb_data.get('settings_dropdown', [])
    
    condition_js = "eval: (function() { if (!document.getElementById('ashan-blocker-style')) { var s = document.createElement('style'); s.id = 'ashan-blocker-style'; s.innerHTML = '#ashan-cn-sidebar-container, .ashan-sidebar-wrapper { display: none !important; visibility: hidden !important; height: 0 !important; opacity: 0 !important; pointer-events: none !important; }'; if (document.head) document.head.appendChild(s); } var el = document.getElementById('ashan-cn-sidebar-container'); if (el) el.remove(); var wr = document.querySelectorAll('.ashan-sidebar-wrapper'); wr.forEach(function(w){ w.remove(); }); return false; })()"

    # Update or append custom navbar action
    new_item = {
        "item_label": "Ashan Pure Desk Guard",
        "item_type": "Action",
        "action": "console.log('Pure Desk Guard Active')",
        "hidden": 1,
        "is_standard": 0,
        "condition": condition_js
    }
    
    # Filter out any existing guard item
    filtered = [item for item in settings_dropdown if item.get('item_label') != 'Ashan Pure Desk Guard']
    filtered.append(new_item)
    
    res = call_api('/api/resource/Navbar%20Settings/Navbar%20Settings', method='PUT', data={"settings_dropdown": filtered})
    print("Updated Navbar Settings with pure Desk guard condition:", res is not None)

