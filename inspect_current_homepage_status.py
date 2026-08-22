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

login_req = urllib.request.Request(
    f"{SITE_URL}/api/method/login",
    data=json.dumps({'usr': USER, 'pwd': PWD}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
opener.open(login_req)

# Check Client Scripts & Server Scripts
cs_url = f"{SITE_URL}/api/resource/Client%20Script?fields=[\"name\",\"dt\",\"enabled\"]"
try:
    cs_resp = opener.open(urllib.request.Request(cs_url))
    cs_list = json.loads(cs_resp.read().decode('utf-8'))['data']
    print("=== CLIENT SCRIPTS ===")
    for cs in cs_list:
        print(f"- {cs.get('name')} (DocType: {cs.get('dt')}, Enabled: {cs.get('enabled')})")
except Exception as e:
    print("Client Script check error:", e)

# Check Custom HTML Blocks
cb_url = f"{SITE_URL}/api/resource/Custom%20HTML%20Block?fields=[\"name\",\"label\",\"private\"]"
try:
    cb_resp = opener.open(urllib.request.Request(cb_url))
    cb_list = json.loads(cb_resp.read().decode('utf-8'))['data']
    print("\n=== CUSTOM HTML BLOCKS ===")
    for cb in cb_list:
        print(f"- {cb.get('name')} | Label: {cb.get('label')}")
except Exception as e:
    print("Custom HTML Block check error:", e)

# Check current user's workspace settings or hidden workspaces
ws_setting_url = f"{SITE_URL}/api/resource/Workspace%20Settings/Workspace%20Settings"
try:
    ws_set_resp = opener.open(urllib.request.Request(ws_setting_url))
    ws_set = json.loads(ws_set_resp.read().decode('utf-8'))['data']
    print("\n=== WORKSPACE SETTINGS ===")
    print("Workspace Setup completed:", ws_set.get('workspace_setup_completed'))
    print("Workspace Sidebars count:", len(ws_set.get('workspace_sidebars', [])))
    for sb in ws_set.get('workspace_sidebars', []):
        print(f"   Sidebar item: {sb}")
except Exception as e:
    print("Workspace Settings error:", e)
