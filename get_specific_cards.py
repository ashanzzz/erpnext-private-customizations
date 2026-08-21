import os
import json
import urllib.request
import urllib.parse

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
TOKEN = os.getenv('ERPNEXT_TOKEN', '')

def call_api(endpoint, method='GET', data=None):
    headers = {
        'Authorization': TOKEN,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    req_url = f"{SITE_URL.rstrip('/')}{endpoint}"
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    
    req = urllib.request.Request(req_url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        return None

def main():
    names = ['近一个月采购总额', '本月油耗总支出', '待处理报销总额', '运行中油卡数量']
    
    for name in names:
        enc_name = urllib.parse.quote(name)
        res = call_api(f'/api/resource/Number%20Card/{enc_name}')
        if res and 'data' in res:
            print(f"--- {name} ---")
            print(json.dumps(res['data'], ensure_ascii=False, indent=2))
        else:
            print(f"--- {name} NOT FOUND ---")

if __name__ == '__main__':
    main()
