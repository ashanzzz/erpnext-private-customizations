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

script = """
frappe.ui.form.on('Workspace', {
    refresh: function(frm) {
        setup_spa_click_interceptor();
    }
});

function setup_spa_click_interceptor() {
    if (window._spa_interceptor_bound) return;
    window._spa_interceptor_bound = true;
    console.log('[Ashan SPA] Binding SPA click interceptor for Desk sidebar workspace links');

    $(document).on('click', 'a[href^="/desk/"], a[href^="/app/"]', function(e) {
        var href = $(this).attr('href');
        if (!href) return;
        if ($(this).attr('target') === '_blank' || href.includes('/api/') || href.includes('/files/')) return;
        
        var route = href.replace(/^\\/(desk|app)\\//, '');
        if (route && window.frappe && frappe.set_route) {
            e.preventDefault();
            e.stopPropagation();
            console.log('[Ashan SPA] Routing smoothly to workspace: ' + route);
            frappe.set_route(route);
        }
    });
}

setup_spa_click_interceptor();
"""

payload = {
    "dt": "Workspace",
    "name": "Ashan SPA Sidebar Link Interceptor",
    "script": script,
    "enabled": 1
}

res = call_api('/api/resource/Client%20Script', method='POST', data=payload)
print("Created Client Script for Workspace SPA Interceptor:", res is not None)

