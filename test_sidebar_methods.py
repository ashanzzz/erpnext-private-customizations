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

methods_to_test = [
    "frappe.desk.desktop.get_workspace_sidebar_items",
    "frappe.desk.doctype.workspace_sidebar.workspace_sidebar.get_workspace_sidebar_items",
    "frappe.desk.doctype.workspace_sidebar.workspace_sidebar.get_sidebar_items",
    "frappe.desk.doctype.workspace.workspace.get_workspace_sidebar",
    "frappe.desk.doctype.workspace.workspace.get_workspaces",
    "frappe.desk.desktop.get_workspace_sidebar",
]

for method in methods_to_test:
    req = urllib.request.Request(f"{SITE_URL}/api/method/{method}")
    try:
        resp = opener.open(req)
        print(f"SUCCESS on {method}:", resp.read().decode('utf-8')[:200])
    except urllib.error.HTTPError as e:
        print(f"FAILED on {method}: {e.code}")

