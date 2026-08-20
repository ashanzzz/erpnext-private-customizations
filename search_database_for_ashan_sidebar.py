import os
import json
import urllib.request
import urllib.parse
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
PWD = os.getenv('ERPNEXT_PASSWORD', '')

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

# Check Client Script
cs_list = call_api('/api/resource/Client%20Script?fields=["name","dt","view","enabled"]')
print("Client Scripts in DB:", json.dumps(cs_list, indent=2, ensure_ascii=False))

# Check Custom HTML Block
chb_list = call_api('/api/resource/Custom%20HTML%20Block?fields=["name"]')
print("Custom HTML Blocks in DB:", json.dumps(chb_list, indent=2, ensure_ascii=False))

# Check Workspace Customizations
ws_list = call_api('/api/resource/Workspace?fields=["name","title","is_standard","public","module"]')
print("Total Workspaces in DB:", len(ws_list.get('data', [])))

# Check Property Setters
ps_list = call_api('/api/resource/Property%20Setter?limit_page_length=100&fields=["name","doc_type","property","value"]')
print("Total Property Setters:", len(ps_list.get('data', [])))
for ps in ps_list.get('data', []):
    if 'sidebar' in str(ps).lower() or 'script' in str(ps).lower():
        print("Matching PS:", ps)

