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

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
login_req = urllib.request.Request(
    f"{SITE_URL}/api/method/login",
    data=json.dumps({'usr': USER, 'pwd': PWD}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
opener.open(login_req)

# Get Workspaces
ws_url = f"{SITE_URL}/api/resource/Workspace?fields=[\"name\",\"title\",\"module\",\"parent_page\",\"public\",\"is_hidden\",\"sequence_id\"]&limit_page_length=200"
resp = opener.open(urllib.request.Request(ws_url))
data = json.loads(resp.read().decode('utf-8'))['data']

print("=== ALL PUBLIC & NON-HIDDEN WORKSPACES ===")
tree = {}
for ws in data:
    if ws.get('public') and not ws.get('is_hidden'):
        parent = ws.get('parent_page') or "Root (No Parent)"
        tree.setdefault(parent, []).append(ws)

for parent, children in tree.items():
    print(f"\nParent: [{parent}]")
    for child in children:
        print(f"   └── Name: {child['name']} | Title: {child['title']}")

# Also fetch desktop / sidebar settings method if available
try:
    sidebar_req = urllib.request.Request(f"{SITE_URL}/api/method/frappe.desk.desktop.get_workspace_sidebar_items")
    sidebar_resp = opener.open(sidebar_req)
    sidebar_data = json.loads(sidebar_resp.read().decode('utf-8'))
    print("\n=== NATIVE SIDEBAR API RESPONSE (`get_workspace_sidebar_items`) ===")
    print(json.dumps(sidebar_data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"\nCould not fetch sidebar items api: {e}")
