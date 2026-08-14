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

spa_script = """
// Frappe 16 Native Workspace SPA Router Click Interceptor & Navigation Stabilizer

(function() {
    function setup_spa_navigation() {
        if (window._ashan_spa_bound) return;
        window._ashan_spa_bound = true;
        console.log('[Ashan CN] SPA navigation click interceptor initialized.');

        // Intercept clicks on sidebar workspace links to prevent full page reloads
        $(document).on('click', 'a[href^="/desk/"], a[href^="/app/"]', function(e) {
            var href = $(this).attr('href');
            if (!href) return;
            
            // Skip external links, files, and API calls
            if ($(this).attr('target') === '_blank' || href.includes('/api/') || href.includes('/files/')) return;
            
            var route = href.replace(/^\\/(desk|app)\\//, '');
            if (route && window.frappe && frappe.set_route) {
                e.preventDefault();
                e.stopPropagation();
                console.log('[Ashan SPA] Smoothly set route to: ' + route);
                frappe.set_route(route);
            }
        });
    }

    if (typeof $ !== 'undefined') {
        $(document).ready(setup_spa_navigation);
    }
    setup_spa_navigation();
})();

// Intercept /login success for seamless redirection
(function() {
    function patch_login() {
        if (window.location.pathname.toLowerCase() === '/login') {
            if (window.login && window.login.login_handlers && window.login.login_handlers[200]) {
                if (!window.login._ashan_login_patched) {
                    window.login._ashan_login_patched = true;
                    var orig_200 = window.login.login_handlers[200];
                    window.login.login_handlers[200] = function(data) {
                        if (data && data.message === "Logged In") {
                            window.location.href = "/desk/my-business";
                            return;
                        }
                        if (orig_200) orig_200(data);
                    };
                }
            }
        }
    }
    patch_login();
    if (typeof $ !== 'undefined') {
        $(document).ready(patch_login);
    }
    setTimeout(patch_login, 200);
})();
"""

res = call_api('/api/resource/Website%20Script/Website%20Script', method='PUT', data={"javascript": spa_script})
print("Updated Website Script with SPA click interceptor:", res is not None)

