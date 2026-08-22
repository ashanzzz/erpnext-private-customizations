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

# Update Default value via frappe.defaults API or User Settings
print("Setting desktop:home_page in Default Value doctype...")
payload = {
    "doctype": "DefaultValue",
    "defkey": "desktop:home_page",
    "defvalue": "my-business",
    "parent": USER,
    "parenttype": "User"
}

# Fetch existing default value if any
res = call_api('/api/resource/DefaultValue?filters=[["defkey","=","desktop:home_page"]]')
if res and 'data' in res:
    for dv in res['data']:
        name = dv['name']
        print(f"Updating DefaultValue {name} -> my-business")
        call_api(f'/api/resource/DefaultValue/{urllib.parse.quote(name)}', method='PUT', data={"defvalue": "my-business"})

# Also insert global default value
try:
    call_api('/api/resource/DefaultValue', method='POST', data=payload)
    print("Inserted user DefaultValue for desktop:home_page -> my-business")
except Exception as e:
    print("DefaultValue insert:", e)

