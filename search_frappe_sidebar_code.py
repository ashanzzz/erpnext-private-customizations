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

# Fetch desk JS bundle or workspace bundle to inspect click handlers
req = urllib.request.Request(f"{SITE_URL}/assets/frappe/dist/js/desk.bundle.MDLVMAQZ.css")
# Let's inspect frappe desk JS bundle URL from /desk HTML
req_desk = urllib.request.Request(f"{SITE_URL}/desk/my-business")
resp = opener.open(req_desk)
html = resp.read().decode('utf-8')

import re
js_bundles = re.findall(r'src=["\'](/assets/.*\.js.*?)["\']', html)
print("Desk JS Bundles found:")
for jb in js_bundles:
    print("-", jb)

