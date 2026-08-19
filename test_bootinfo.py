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
PWD = os.getenv('ERPNEXT_PASSWORD', '')

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_req = urllib.request.Request(
    f"{SITE_URL}/api/method/login",
    data=json.dumps({'usr': USER, 'pwd': PWD}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
opener.open(login_req)

# Fetch bootinfo
boot_req = urllib.request.Request(f"{SITE_URL}/api/method/frappe.boot.get_bootinfo")
boot_resp = opener.open(boot_req)
boot_data = json.loads(boot_resp.read().decode('utf-8'))['message']

print("=== BOOTINFO KEYS ===")
print(list(boot_data.keys()))
print("\nBootinfo home_page:", boot_data.get('home_page'))
print("Bootinfo default_route:", boot_data.get('default_route'))
if 'user' in boot_data:
    print("User home_page in bootinfo:", boot_data['user'].get('home_page'))
    print("User defaults in bootinfo:", boot_data['user'].get('defaults'))

