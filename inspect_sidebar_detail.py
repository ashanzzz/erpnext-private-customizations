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

# Fetch all Workspace Sidebar items across sidebars to see if any have child=1 or collapsible items
resp = opener.open(urllib.request.Request(f"{SITE_URL}/api/resource/Workspace%20Sidebar?fields=[\"name\"]&limit_page_length=100"))
sidebars = json.loads(resp.read().decode('utf-8'))['data']

for sb in sidebars:
    name = sb['name']
    url = f"{SITE_URL}/api/resource/Workspace%20Sidebar/{urllib.parse.quote(name)}"
    r = opener.open(urllib.request.Request(url))
    doc = json.loads(r.read().decode('utf-8'))['data']
    items = doc.get('items', [])
    child_items = [it for it in items if it.get('child')]
    collapsibles = [it for it in items if it.get('collapsible')]
    print(f"Sidebar: {name:<25} | Total Items: {len(items):<3} | Child items: {len(child_items):<3} | Collapsible: {len(collapsibles)}")
    if child_items:
        for ci in child_items:
            print(f"   └── CHILD ITEM -> Label: {ci.get('label')}, Type: {ci.get('type')}, Link: {ci.get('link_to')}, Indent: {ci.get('indent')}")

