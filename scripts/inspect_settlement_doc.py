import os, sys, io, requests, json

def load_env():
    env_file = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()
site_url = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
token = os.getenv('ERPNEXT_TOKEN')
headers = {'Authorization': token} if token else {}

r = requests.get(site_url + '/api/resource/Property Monthly Settlement/PROP-SET-2026-08-01', headers=headers)
doc = r.json().get('data', {})
print('lease_charges in Doc:')
for l in doc.get('lease_charges', []):
    print(' ', l)
