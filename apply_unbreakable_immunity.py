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

immune_script = """
// 1. Hook jQuery $.fn.prepend to permanently drop legacy ashan-cn-sidebar-container injection
(function() {
    function patch_jquery() {
        if (typeof $ !== 'undefined' && $.fn && $.fn.prepend && !$.fn._ashan_patched) {
            $.fn._ashan_patched = true;
            var origPrepend = $.fn.prepend;
            $.fn.prepend = function() {
                for (var i = 0; i < arguments.length; i++) {
                    var arg = arguments[i];
                    if (typeof arg === 'string' && (arg.indexOf('ashan-cn-sidebar-container') !== -1 || arg.indexOf('ashan-sidebar-wrapper') !== -1)) {
                        console.log('[Ashan] Blocked legacy sidebar DOM injection!');
                        return this;
                    }
                }
                return origPrepend.apply(this, arguments);
            };
        }
    }
    patch_jquery();
    setInterval(patch_jquery, 50);
})();

// 2. Override find_sidebar_element
window.find_sidebar_element = function() { return null; };

// 3. Inject permanent CSS rule to hide any legacy DOM wrapper
(function() {
    var style = document.createElement('style');
    style.id = 'ashan-sidebar-blocker';
    style.innerHTML = '#ashan-cn-sidebar-container, .ashan-sidebar-wrapper { display: none !important; visibility: hidden !important; height: 0 !important; opacity: 0 !important; pointer-events: none !important; }';
    if (document.head) {
        document.head.appendChild(style);
    } else {
        document.addEventListener('DOMContentLoaded', function() { document.head.appendChild(style); });
    }
})();

// 4. MutationObserver & interval to immediately purge if already created
(function() {
    function purge() {
        var el = document.getElementById('ashan-cn-sidebar-container');
        if (el) el.remove();
        var wrappers = document.querySelectorAll('.ashan-sidebar-wrapper');
        wrappers.forEach(function(w) { w.remove(); });
    }
    purge();
    var observer = new MutationObserver(purge);
    if (document.documentElement) {
        observer.observe(document.documentElement, { childList: true, subtree: true });
    }
    setInterval(purge, 50);
})();

// 5. Intercept /login success for seamless redirection
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

res = call_api('/api/resource/Website%20Script/Website%20Script', method='PUT', data={"javascript": immune_script})
print("Updated Website Script with jQuery prepend hook:", res is not None)

