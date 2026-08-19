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

# Test login API response
login_req = urllib.request.Request(
    f"{SITE_URL}/api/method/login",
    data=json.dumps({'usr': USER, 'pwd': PWD}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
resp = opener.open(login_req)
login_data = json.loads(resp.read().decode('utf-8'))
print("=== LOGIN API RESPONSE ===")
print(json.dumps(login_data, indent=2, ensure_ascii=False))

# Fetch User doc
u_req = urllib.request.Request(f"{SITE_URL}/api/resource/User/{urllib.parse.quote(USER)}")
u_resp = opener.open(u_req)
u_doc = json.loads(u_resp.read().decode('utf-8'))['data']
print("\n=== USER DOC HOME PAGE FIELDS ===")
print("User home_page:", u_doc.get('home_page'))

# Fetch System Settings
sys_req = urllib.request.Request(f"{SITE_URL}/api/resource/System%20Settings/System%20Settings")
try:
    sys_resp = opener.open(sys_req)
    sys_doc = json.loads(sys_resp.read().decode('utf-8'))['data']
    print("\n=== SYSTEM SETTINGS HOME PAGE FIELDS ===")
    print("System Settings default_home_page:", sys_doc.get('default_home_page'))
except Exception as e:
    print("System settings fetch error:", e)

