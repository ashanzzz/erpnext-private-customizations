# -*- coding: utf-8 -*-
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
ERPNEXT_USER = os.getenv('ERPNEXT_USER', 'Administrator')
ERPNEXT_PASS = os.getenv('ERPNEXT_PASSWORD', 'admin')

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_req = urllib.request.Request(
    f"{SITE_URL}/api/method/login",
    data=json.dumps({'usr': ERPNEXT_USER, 'pwd': ERPNEXT_PASS}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
opener.open(login_req)

def call_api(endpoint, method='GET', data=None):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    quoted_endpoint = urllib.parse.quote(endpoint, safe='/:?=&')
    req_url = f"{SITE_URL.rstrip('/')}{quoted_endpoint}"
    encoded = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(req_url, data=encoded, headers=headers, method=method)
    try:
        with opener.open(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        print(f"HTTPError {e.code} on {method} {endpoint}: {e.read().decode('utf-8')}")
        return None

# 1. 查找基础主数据
sg = call_api('/api/resource/Supplier%20Group?limit=5')
print("Supplier Groups:", sg)
ig = call_api('/api/resource/Item%20Group?limit=5')
print("Item Groups:", ig)
uom = call_api('/api/resource/UOM?limit=5')
print("UOMs:", uom)
