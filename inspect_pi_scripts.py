import os
import json
import urllib.request
import urllib.parse
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
SITE_URL = os.getenv('ERPNEXT_SITE_URL_LOCAL', 'http://192.168.8.11:6888')
USER = os.getenv('ERPNEXT_USER', 'Administrator')
PWD = os.getenv('ERPNEXT_PASSWORD', 'admin')

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_req = urllib.request.Request(
    f"{SITE_URL}/api/method/login",
    data=json.dumps({'usr': USER, 'pwd': PWD}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
opener.open(login_req)

def call_api(endpoint):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    req_url = f"{SITE_URL.rstrip('/')}{endpoint}"
    req = urllib.request.Request(req_url, headers=headers, method='GET')
    try:
        with opener.open(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except Exception as e:
        print(f"Error {endpoint}: {e}")
        return None

# 1. 检查 Client Scripts
cs_list = call_api('/api/resource/Client%20Script?filters=[["dt","in",["Purchase%20Invoice","Purchase%20Invoice%20Item"]]]&fields=["name","dt","enabled","script"]')
print("Client Scripts found:")
for cs in (cs_list.get('data') or []):
    print(f"--- Client Script: {cs['name']} ({cs['dt']}) enabled={cs['enabled']} ---")
    cs_detail = call_api(f"/api/resource/Client%20Script/{urllib.parse.quote(cs['name'])}")
    if cs_detail and 'data' in cs_detail:
        print(cs_detail['data'].get('script', ''))

# 2. 检查 Server Scripts
ss_list = call_api('/api/resource/Server%20Script?filters=[["reference_doctype","in",["Purchase%20Invoice","Purchase%20Invoice%20Item"]]]&fields=["name","script_type","reference_doctype","disabled"]')
print("\nServer Scripts found:")
for ss in (ss_list.get('data') or []):
    print(f"--- Server Script: {ss['name']} ---")
    ss_detail = call_api(f"/api/resource/Server%20Script/{urllib.parse.quote(ss['name'])}")
    if ss_detail and 'data' in ss_detail:
        print(ss_detail['data'].get('script', ''))

