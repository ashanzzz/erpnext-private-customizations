import os
import json
import urllib.request
import re
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

req = urllib.request.Request(f"{SITE_URL}/desk")
resp = opener.open(req)
html = resp.read().decode('utf-8')

# Search for frappe.boot in html
match = re.search(r'frappe\.boot\s*=\s*({.*?});\s*frappe\.', html, re.DOTALL)
if match:
    boot_str = match.group(1)
    boot = json.loads(boot_str)
    print("=== BOOT JSON ANALYSIS ===")
    print("boot.home_page:", boot.get('home_page'))
    print("boot.default_route:", boot.get('default_route'))
    print("boot.desk_settings:", boot.get('desk_settings'))
    if 'sysdefaults' in boot:
        print("boot.sysdefaults:", boot.get('sysdefaults'))
    if 'user' in boot:
        print("boot.user.home_page:", boot['user'].get('home_page'))
        print("boot.user.defaults:", boot['user'].get('defaults'))
else:
    print("frappe.boot match failed")

