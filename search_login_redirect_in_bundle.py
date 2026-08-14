import urllib.request
import re

SITE_URL = 'http://192.168.8.11:6888'
js_url = f"{SITE_URL}/assets/frappe/dist/js/frappe-web.bundle.NLXIWM34.js"

req = urllib.request.Request(js_url)
with urllib.request.urlopen(req) as resp:
    js = resp.read().decode('utf-8')

# Search for login form submit handler
matches = re.finditer(r'login_email|btn-login|window\.location', js)
count = 0
for m in matches:
    start = max(0, m.start() - 150)
    end = min(len(js), m.end() + 150)
    print(f"=== MATCH {count} ===")
    print(js[start:end])
    count += 1
    if count >= 10:
        break

