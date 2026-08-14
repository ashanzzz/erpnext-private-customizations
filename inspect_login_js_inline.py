import urllib.request
import re

SITE_URL = 'http://192.168.8.11:6888'

req = urllib.request.Request(f"{SITE_URL}/login")
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8')

scripts = re.findall(r'<script.*?>(.*?)</script>', html, re.DOTALL)
for idx, s in enumerate(scripts):
    if '// login.js' in s:
        print(f"=== FULL INLINE LOGIN.JS (Script {idx}) ===")
        print(s)

