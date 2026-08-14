import urllib.request
import re

SITE_URL = 'http://192.168.8.11:6888'
js_url = f"{SITE_URL}/assets/frappe/dist/js/frappe-web.bundle.NLXIWM34.js"

req = urllib.request.Request(js_url)
with urllib.request.urlopen(req) as resp:
    js = resp.read().decode('utf-8')

print("JS Length:", len(js))
# Find occurrences of Logged In or home_page
matches = re.finditer(r'Logged In', js)
for m in matches:
    start = max(0, m.start() - 100)
    end = min(len(js), m.end() + 200)
    print("=== MATCH AROUND 'Logged In' ===")
    print(js[start:end])
    print("-" * 50)

