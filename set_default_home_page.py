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

# Update System Settings default_home_page
print("Setting System Settings default_home_page to 'app/my-business'...")
call_api('/api/resource/System%20Settings/System%20Settings', method='PUT', data={
    "default_home_page": "app/my-business"
})

# Update User home_page
print("Setting User home_page to 'app/my-business'...")
call_api(f'/api/resource/User/{urllib.parse.quote(USER)}', method='PUT', data={
    "home_page": "app/my-business"
})

# Re-test login response
login_resp = call_api('/api/method/login', method='POST', data={'usr': USER, 'pwd': PWD})
print("\nNew Login Response:", json.dumps(login_resp, indent=2, ensure_ascii=False))

