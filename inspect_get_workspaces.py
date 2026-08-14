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

req = urllib.request.Request(f"{SITE_URL}/api/method/frappe.desk.doctype.workspace.workspace.get_workspaces")
resp = opener.open(req)
data = json.loads(resp.read().decode('utf-8'))['message']

print("=== GET_WORKSPACES KEYS ===")
print(data.keys())

print("\n=== GET_WORKSPACES PAGES ===")
pages = data.get('pages', [])
print(f"Total pages: {len(pages)}")

for p in pages:
    print(f"Name: {p.get('name'):<30} | Title: {p.get('title'):<25} | Parent Page: {p.get('parent_page')}")

if 'has_access' in data:
    print("\n=== HAS ACCESS ===")
    print(data['has_access'])

