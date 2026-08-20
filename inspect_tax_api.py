import os
import json
import urllib.request
import urllib.parse
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
SITE_URL = os.getenv('ERPNEXT_SITE_URL_LOCAL', 'http://192.168.8.11:6888')
USER = os.getenv('ERPNEXT_USER', 'Administrator')
PWD = os.getenv('ERPNEXT_PASSWORD', 'admin')

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_req = urllib.request.Request(
    f"{SITE_URL}/api/method/login",
    data=json.dumps({'usr': USER, 'pwd': PWD}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
opener.open(login_req)

def call_api(endpoint):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    req_url = f"{SITE_URL.rstrip('/')}{endpoint}"
    req = urllib.request.Request(req_url, headers=headers, method='GET')
    try:
        with opener.open(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except Exception as e:
        print(f"Error {endpoint}: {e}")
        return None

# 1. 查询 Item Tax Template
item_tax_templates = call_api('/api/resource/Item%20Tax%20Template?fields=["name","company","disabled"]')
print("Item Tax Templates:", json.dumps(item_tax_templates, ensure_ascii=False, indent=2))

# 2. 查询 Purchase Taxes and Charges Template
ptc_templates = call_api('/api/resource/Purchase%20Taxes%20and%20Charges%20Template?fields=["name","company","is_default","disabled"]')
print("Purchase Taxes and Charges Templates:", json.dumps(ptc_templates, ensure_ascii=False, indent=2))

# 3. 查询 Tax Accounts
tax_accounts = call_api('/api/resource/Account?filters=[["account_type","in",["Tax","Chargeable"]]]&fields=["name","account_name","company","parent_account","account_type"]')
print("Tax Accounts:", json.dumps(tax_accounts, ensure_ascii=False, indent=2))

# 4. 查询 Custom Field on Purchase Invoice
custom_fields = call_api('/api/resource/Custom%20Field?filters=[["dt","in",["Purchase%20Invoice","Purchase%20Invoice%20Item"]]]&fields=["name","dt","fieldname","label","fieldtype","insert_after"]')
print("Custom Fields:", json.dumps(custom_fields, ensure_ascii=False, indent=2))

# 5. 查询 Purchase Invoice Meta
pi_meta = call_api('/api/method/frappe.desk.form.load.getdoctype?doctype=Purchase%20Invoice')
if pi_meta and 'docs' in pi_meta:
    doc = pi_meta['docs'][0]
    tax_fields = [f for f in doc.get('fields', []) if 'tax' in f.get('fieldname', '').lower() or '税' in f.get('label', '')]
    print(f"Purchase Invoice Tax Fields: {len(tax_fields)} found")
    for f in tax_fields:
        print(f"  - [{f.get('fieldtype')}] {f.get('label')} ({f.get('fieldname')})")

