import os
import urllib.request

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')

# Try different URL patterns
urls = [
    f"{SITE_URL}/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js",
    f"{SITE_URL}/files/ashan_cn_sidebar.js",
    f"http://192.168.8.11:6888/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js",
]

for url in urls:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode('utf-8', errors='replace')
            status = resp.status
            print(f"[{status}] {url}")
            if 'ASHAN_SIDEBAR_KEY' in content:
                print("  -> Contains ASHAN_SIDEBAR_KEY (fix confirmed!)")
            elif status == 200:
                print(f"  -> Content: {content[:100]}")
    except Exception as e:
        print(f"[ERR] {url}: {e}")
