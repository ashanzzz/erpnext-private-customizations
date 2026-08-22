import os
import requests
from bs4 import BeautifulSoup

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
print("Title in HTML:")
soup = BeautifulSoup(r.text, 'html.parser')
print("title:", soup.title.string if soup.title else "No title")
print("h1:", [h.get_text(strip=True) for h in soup.find_all('h1')])
print("p:", [p.get_text(strip=True) for p in soup.find_all('p')][:5])

# Print first 500 characters of clean text
print("\nBody text:\n", soup.body.get_text(strip=True)[:500] if soup.body else "No body")
