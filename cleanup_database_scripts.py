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

cs_url = f"{SITE_URL}/api/resource/Client%20Script?fields=[\"name\",\"dt\",\"enabled\"]&limit_page_length=200"
resp = opener.open(urllib.request.Request(cs_url))
cs_list = json.loads(resp.read().decode('utf-8'))['data']

print("=== CLEANING UP CLIENT SCRIPTS ===")
for cs in cs_list:
    name = cs['name']
    if 'sidebar' in name.lower() or 'ashan' in name.lower():
        print(f"Deleting Client Script: {name}")
        del_req = urllib.request.Request(
            f"{SITE_URL}/api/resource/Client%20Script/{urllib.parse.quote(name)}",
            method='DELETE'
        )
        try:
            opener.open(del_req)
            print(f"Successfully deleted {name}")
        except Exception as e:
            print(f"Error deleting {name}: {e}")

