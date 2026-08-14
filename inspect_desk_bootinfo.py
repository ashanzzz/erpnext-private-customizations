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
matches = re.findall(r'frappe\.boot\s*=\s*(\{.*?\});', html, re.DOTALL)
if matches:
    print("Found frappe.boot snippet length:", len(matches[0]))
    try:
        boot = json.loads(matches[0])
        print("boot.home_page:", boot.get('home_page'))
        print("boot.default_route:", boot.get('default_route'))
        if 'user' in boot:
            print("user.home_page:", boot['user'].get('home_page'))
    except Exception as e:
        print("JSON parse error:", e)
else:
    print("frappe.boot pattern not found via simple regex, searching strings...")
    for line in html.splitlines():
        if 'home_page' in line or 'default_route' in line:
            print("LINE:", line[:120])
