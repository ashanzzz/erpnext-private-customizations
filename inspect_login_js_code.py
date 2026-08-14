import os
import json
import urllib.request
import re

SITE_URL = 'http://192.168.8.11:6888'

req = urllib.request.Request(f"{SITE_URL}/login")
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8')

# Find js files in /login HTML
js_files = re.findall(r'src=["\'](/assets/.*\.js.*?)["\']', html)
print("Found JS files on /login page:")
for jf in js_files:
    print("-", jf)
    if 'login' in jf or 'website' in jf:
        req_js = urllib.request.Request(f"{SITE_URL}{jf}")
        with urllib.request.urlopen(req_js) as js_resp:
            js_content = js_resp.read().decode('utf-8')
            print(f"  Content length: {len(js_content)}")
            # Search for location.href or route or home_page
            for line in js_content.splitlines():
                if 'location.href' in line or 'home_page' in line or 'Logged In' in line:
                    print("  JS MATCH:", line[:120])

