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

req = urllib.request.Request(f"{SITE_URL}/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js")
try:
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode('utf-8')
        with open("live_ashan_cn_sidebar.js", "w", encoding="utf-8") as f:
            f.write(content)
        print("Saved live_ashan_cn_sidebar.js successfully! Length:", len(content))
except Exception as e:
    print("Error fetching ashan_cn_sidebar.js:", e)

