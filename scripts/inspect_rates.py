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
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

site_url = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
token = os.getenv('ERPNEXT_TOKEN')
headers = {'Authorization': token} if token else {}

r_rates = requests.get(site_url + '/api/resource/Property Charge Rate?limit_page_length=100', headers=headers)
print('Property Charge Rates in DB count:', len(r_rates.json().get('data', [])))
for rate in r_rates.json().get('data', []):
    r_detail = requests.get(site_url + f'/api/resource/Property Charge Rate/{rate["name"]}', headers=headers)
    print('  Rate:', json.dumps(r_detail.json().get('data', {}), ensure_ascii=False))

r_leases = requests.get(site_url + '/api/resource/Property Lease?limit_page_length=100', headers=headers)
print('Property Leases in DB count:', len(r_leases.json().get('data', [])))
for l in r_leases.json().get('data', []):
    r_detail = requests.get(site_url + f'/api/resource/Property Lease/{l["name"]}', headers=headers)
    print('  Lease:', json.dumps(r_detail.json().get('data', {}), ensure_ascii=False))
