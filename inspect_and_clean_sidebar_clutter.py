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
SITE_URL = os.getenv('ERPNEXT_SITE_URL_LOCAL', 'http://192.168.8.11:6888')
USER = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
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

# Check all Workspaces with module Ashan CN Procurement
ws_list = call_api('/api/resource/Workspace?limit_page_length=100&fields=["name","title","module","parent_page","public","is_hidden"]')
print("=== ASHAN CN PROCUREMENT WORKSPACES ===")
if ws_list and 'data' in ws_list:
    for w in ws_list['data']:
        if w.get('module') == 'Ashan CN Procurement':
            print(f"- {w.get('name')} | Title: {w.get('title')} | Parent: '{w.get('parent_page')}' | Public: {w.get('public')} | Hidden: {w.get('is_hidden')}")

# Check why loose doctypes and reports appear
# In Frappe, DocTypes with module 'Ashan CN Procurement' show up if the workspace matches module.
# Let's inspect DocTypes with module Ashan CN Procurement
dt_list = call_api('/api/resource/DocType?filters=[["module","=","Ashan CN Procurement"]]&fields=["name","module","custom","issingle"]')
print("\n=== DOCTYPES IN ASHAN CN PROCUREMENT ===")
if dt_list and 'data' in dt_list:
    for dt in dt_list['data']:
        print(f"- {dt.get('name')}")

