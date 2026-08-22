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

website_js = """
// Ashan CN Procurement - Auto Redirect Login & Desk to My Business Workspace

(function() {
    // 1. Intercept login callback on /login page
    function patch_login_handler() {
        if (window.login && window.login.login_handlers && window.login.login_handlers[200]) {
            if (!window.login._patched_ashan) {
                window.login._patched_ashan = true;
                var orig_200 = window.login.login_handlers[200];
                window.login.login_handlers[200] = function(data) {
                    if (data && data.message === "Logged In") {
                        console.log("[Ashan Login Redirect] Intercepted post-login, redirecting to /desk/my-business");
                        window.location.href = "/desk/my-business";
                        return;
                    }
                    if (orig_200) orig_200(data);
                };
            }
        }
    }

    // 2. Redirect /desk or /app landing to /desk/my-business
    function redirect_desk_landing() {
        var path = window.location.pathname.toLowerCase();
        var hash = window.location.hash.toLowerCase();
        if (path === '/desk' || path === '/desk/' || path === '/desk#' || path === '/app' || path === '/app/') {
            if (!hash || hash === '' || hash === '#' || hash === '#desk' || hash === '#workspace/desktop') {
                console.log("[Ashan Desk Redirect] Intercepted " + path + ", redirecting to /desk/my-business");
                window.location.replace("/desk/my-business");
            }
        }
    }

    // Execute immediately
    patch_login_handler();
    redirect_desk_landing();

    // Bind event listeners
    if (typeof $ !== 'undefined') {
        $(document).ready(function() {
            patch_login_handler();
            redirect_desk_landing();
        });
        $(document).on('app_ready route-change page-change', redirect_desk_landing);
    }
    
    // Fallback checks
    setTimeout(patch_login_handler, 100);
    setTimeout(patch_login_handler, 500);
    setTimeout(redirect_desk_landing, 100);
    setTimeout(redirect_desk_landing, 500);
})();
"""

# Save to Website Script
payload = {
    "javascript": website_js
}

res = call_api('/api/resource/Website%20Script/Website%20Script', method='PUT', data=payload)
print("Updated Website Script:", res is not None)

