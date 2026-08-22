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
USER = os.getenv('ERPNEXT_USER', 'Administrator')
PWD = os.getenv('ERPNEXT_PASSWORD', '')

session = requests.Session()
session.post(f"{SITE_URL}/api/method/login", data={"usr": USER, "pwd": PWD})

r = session.get(f"{SITE_URL}/")
print("Full HTML of GET /:\n", r.text)
