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

req = urllib.request.Request(
    f"{SITE_URL}/api/method/frappe.client.set_value",
    data=json.dumps({"doctype": "User", "name": USER, "fieldname": "home_page", "value": "/app/my-business"}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
try:
    resp = opener.open(req)
    print("set_value User home_page success:", resp.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")

