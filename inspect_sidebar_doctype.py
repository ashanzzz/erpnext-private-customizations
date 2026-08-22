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

# Inspect Workspace Sidebar Items DocType
try:
    resp = opener.open(urllib.request.Request(f"{SITE_URL}/api/resource/DocType/Workspace%20Sidebar%20Item"))
    dt_item = json.loads(resp.read().decode('utf-8'))['data']
    print("=== WORKSPACE SIDEBAR ITEM FIELDS ===")
    for field in dt_item.get('fields', []):
        print(f"Fieldname: {field.get('fieldname'):<20} | Type: {field.get('fieldtype'):<15} | Label: {field.get('label')}")
except Exception as e:
    print(f"Error fetching Workspace Sidebar Item: {e}")

# Fetch Workspace Sidebar documents
try:
    resp2 = opener.open(urllib.request.Request(f"{SITE_URL}/api/resource/Workspace%20Sidebar?fields=[\"*\"]"))
    sidebars = json.loads(resp2.read().decode('utf-8'))['data']
    print(f"\n=== WORKSPACE SIDEBAR DOCS ({len(sidebars)} found) ===")
    for sb in sidebars:
        print(f"- Name: {sb.get('name')} | Title: {sb.get('title')} | App: {sb.get('app')}")
except Exception as e:
    print(f"Error fetching Workspace Sidebar list: {e}")

