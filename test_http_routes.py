import os
import requests

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

SITE_URL = "http://192.168.8.11:6888"

# 1. Test root URL
r1 = requests.get(f"{SITE_URL}/", allow_redirects=False)
print("GET / -> Status:", r1.status_code, "Location:", r1.headers.get('Location'))

# 2. If it redirects, where?
r2 = requests.get(f"{SITE_URL}/", allow_redirects=True)
print("GET / (follow redirects) -> URL:", r2.url, "Status:", r2.status_code)
if "not found" in r2.text.lower():
    print("Contains 'not found': YES")
    print("First 300 chars of body:", r2.text[:300])

# 3. Test /desk
r3 = requests.get(f"{SITE_URL}/desk", allow_redirects=False)
print("\nGET /desk -> Status:", r3.status_code, "Location:", r3.headers.get('Location'))

# 4. Test /login
r4 = requests.get(f"{SITE_URL}/login", allow_redirects=False)
print("GET /login -> Status:", r4.status_code, "Location:", r4.headers.get('Location'))

# 5. Check ashan_cn_sidebar.js content right now
r5 = requests.get(f"{SITE_URL}/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js")
print("\nashan_cn_sidebar.js status:", r5.status_code, "length:", len(r5.text), "has ASHAN_SIDEBAR_KEY:", "ASHAN_SIDEBAR_KEY" in r5.text)

