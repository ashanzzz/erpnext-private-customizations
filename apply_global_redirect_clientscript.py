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

js_code = """
(function() {
    function auto_redirect_to_dashboard() {
        var path = window.location.pathname.toLowerCase();
        var hash = window.location.hash.toLowerCase();
        
        if (path === '/desk' || path === '/desk/' || path === '/desk#' || path === '/app' || path === '/app/' || hash === '' || hash === '#') {
            console.log('[Ashan CN Boot] Auto-redirecting login landing from ' + path + ' to /app/my-business...');
            window.location.replace('/app/my-business');
        }
    }

    auto_redirect_to_dashboard();
    if (typeof $ !== 'undefined') {
        $(document).on('app_ready route-change page-change', auto_redirect_to_dashboard);
        $(document).ready(auto_redirect_to_dashboard);
    }
    setTimeout(auto_redirect_to_dashboard, 100);
    setTimeout(auto_redirect_to_dashboard, 500);
})();
"""

for dt in ["DocType", "User", "Workspace"]:
    script_name = f"Ashan Global Login Redirect for {dt}"
    payload = {
        "dt": dt,
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
    print(f"Updated Client Script for {dt}")

