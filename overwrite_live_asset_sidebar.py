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
USER = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
PWD = os.getenv('ERPNEXT_PASSWORD', '')

# 1. Remove legacy JSON files in local custom/client_script directory
legacy_jsons = [
    r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\custom\client_script\global_desk_sidebar_menu_for_doctype.json",
    r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\custom\client_script\global_desk_sidebar_menu_for_user.json",
    r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\custom\client_script\global_desk_sidebar_menu_for_workspace.json",
    r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\custom\client_script\global_desk_two_level_sidebar.json"
]

for lj in legacy_jsons:
    if os.path.exists(lj):
        print("Removing legacy client script JSON:", lj)
        os.remove(lj)

# 2. Login to site API
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

# 3. Clean up Client Scripts in DB
res = call_api('/api/resource/Client%20Script?fields=["name"]')
if res and 'data' in res:
    for cs in res['data']:
        name = cs['name']
        print(f"Deleting Client Script from DB: {name}")
        call_api(f'/api/resource/Client%20Script/{urllib.parse.quote(name)}', method='DELETE')

print("Cleanup completed successfully!")

