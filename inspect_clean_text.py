import os
import re
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
USER = os.getenv('ERPNEXT_USER', 'Administrator')
PWD = os.getenv('ERPNEXT_PASSWORD', '')

session = requests.Session()
session.post(f"{SITE_URL}/api/method/login", data={"usr": USER, "pwd": PWD})

r = session.get(f"{SITE_URL}/")
print("Status:", r.status_code)
print("URL:", r.url)

title_match = re.search(r'<title>(.*?)</title>', r.text, re.IGNORECASE)
print("Title:", title_match.group(1) if title_match else "No title")

h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', r.text, re.IGNORECASE | re.DOTALL)
print("h1 matches:", h1_matches)

# Print entire text without scripts/styles
clean_text = re.sub(r'<script.*?</script>', '', r.text, flags=re.DOTALL)
clean_text = re.sub(r'<style.*?</style>', '', clean_text, flags=re.DOTALL)
clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
clean_text = ' '.join(clean_text.split())
print("\nVisible text content:\n", clean_text[:500])

# Also check GET /my-business
r_mb = session.get(f"{SITE_URL}/my-business")
clean_mb = re.sub(r'<script.*?</script>', '', r_mb.text, flags=re.DOTALL)
clean_mb = re.sub(r'<style.*?</style>', '', clean_mb, flags=re.DOTALL)
clean_mb = re.sub(r'<[^>]+>', ' ', clean_mb)
print("\nGET /my-business text:\n", ' '.join(clean_mb.split())[:500])

