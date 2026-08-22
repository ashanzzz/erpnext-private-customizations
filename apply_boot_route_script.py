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

def call_api(endpoint, method='GET', data=None):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    req_url = f"{SITE_URL.rstrip('/')}{endpoint}"
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    
    req = urllib.request.Request(req_url, data=encoded_data, headers=headers, method=method)
    try:
        with opener.open(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        print(f"API Error {e.code}: {e.read().decode('utf-8')}")
        return None

# Read boot route JS
js_path = os.path.join("ashan_cn_procurement", "ashan_cn_procurement", "public", "js", "ashan_cn_boot_route.js")
with open(js_path, 'r', encoding='utf-8') as f:
    js_code = f.read()

# Register Client Script for Workspace
script_name = "Ashan Default Dashboard Landing Script"
payload = {
    "dt": "Workspace",
    "script": js_code,
    "enabled": 1
}

enc_name = urllib.parse.quote(script_name)
existing = call_api(f'/api/resource/Client%20Script/{enc_name}')
if existing and 'data' in existing:
    call_api(f'/api/resource/Client%20Script/{enc_name}', method='PUT', data=payload)
else:
    payload["name"] = script_name
    call_api('/api/resource/Client%20Script', method='POST', data=payload)

print("Applied default dashboard landing Client Script!")
