# -*- coding: utf-8 -*-
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
ERPNEXT_USER = os.getenv('ERPNEXT_USER', 'Administrator')
ERPNEXT_PASS = os.getenv('ERPNEXT_PASSWORD', '')

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_req = urllib.request.Request(
    f"{SITE_URL}/api/method/login",
    data=json.dumps({'usr': ERPNEXT_USER, 'pwd': ERPNEXT_PASS}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
opener.open(login_req)

def call_api(endpoint, method='GET', data=None):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    quoted_endpoint = urllib.parse.quote(endpoint, safe='/:?=&')
    req_url = f"{SITE_URL.rstrip('/')}{quoted_endpoint}"
    encoded = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(req_url, data=encoded, headers=headers, method=method)
    try:
        with opener.open(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        print(f"HTTPError {e.code} on {method} {endpoint}: {e.read().decode('utf-8')}")
        return None

# 1. 确保有一个测试供应商
supp = call_api('/api/resource/Supplier/天津市某某科技有限公司')
if not supp or not supp.get('data'):
    supp = call_api('/api/resource/Supplier', method='POST', data={
        "doctype": "Supplier",
        "supplier_name": "天津市某某科技有限公司",
        "supplier_group": "所有供应商组"
    })
print("Supplier:", supp.get('data', {}).get('name'))

# 2. 确保有测试物料
item1 = call_api('/api/resource/Item/ITEM-GOODS-13')
if not item1 or not item1.get('data'):
    item1 = call_api('/api/resource/Item', method='POST', data={
        "doctype": "Item",
        "item_code": "ITEM-GOODS-13",
        "item_name": "工业紧固件",
        "item_group": "所有物料组",
        "stock_uom": "件",
        "is_stock_item": 0
    })

item2 = call_api('/api/resource/Item/ITEM-TRANS-9')
if not item2 or not item2.get('data'):
    item2 = call_api('/api/resource/Item', method='POST', data={
        "doctype": "Item",
        "item_code": "ITEM-TRANS-9",
        "item_name": "干线物流运输服务",
        "item_group": "所有物料组",
        "stock_uom": "次",
        "is_stock_item": 0
    })

item3 = call_api('/api/resource/Item/ITEM-SERV-6')
if not item3 or not item3.get('data'):
    item3 = call_api('/api/resource/Item', method='POST', data={
        "doctype": "Item",
        "item_code": "ITEM-SERV-6",
        "item_name": "设备技术咨询服务",
        "item_group": "所有物料组",
        "stock_uom": "次",
        "is_stock_item": 0
    })

comp = call_api('/api/resource/Company?limit=1')['data'][0]['name']

# 3. 创建多税率采购发票
pi_doc = {
    "doctype": "Purchase Invoice",
    "company": comp,
    "supplier": "天津市某某科技有限公司",
    "currency": "CNY",
    "items": [
        {
            "item_code": "ITEM-GOODS-13",
            "qty": 10,
            "custom_gross_rate": 113.0,
            "custom_tax_rate": 13.0,
            "custom_spec_model": "M10*50 高强螺栓"
        },
        {
            "item_code": "ITEM-TRANS-9",
            "qty": 1,
            "custom_gross_rate": 109.0,
            "custom_tax_rate": 9.0,
            "custom_spec_model": "天津-北京 往返运输"
        },
        {
            "item_code": "ITEM-SERV-6",
            "qty": 1,
            "custom_gross_rate": 106.0,
            "custom_tax_rate": 6.0,
            "custom_spec_model": "现场调试与指导"
        }
    ]
}

res = call_api('/api/resource/Purchase%20Invoice', method='POST', data=pi_doc)

if res and res.get('data'):
    doc_name = res['data']['name']
    saved = call_api(f'/api/resource/Purchase%20Invoice/{urllib.parse.quote(doc_name)}')['data']
    print("\n==================================================")
    print(f" [OK] 采购发票创建成功: {saved.get('name')}")
    print("==================================================")
    print(f"不含税总计 (Net Total)   : ¥{saved.get('net_total')}")
    print(f"增值税总计 (Total Taxes) : ¥{saved.get('total_taxes_and_charges')}")
    print(f"价税合计 (Grand Total)   : ¥{saved.get('grand_total')}")
    
    print("\n--- 各行多税率明细 ---")
    for row in saved.get('items', []):
        print(f"  [{row.get('custom_tax_rate')}% 税率] {row.get('item_name')} ({row.get('custom_spec_model')})")
        print(f"       数量: {row.get('qty')} | 含税单价: ¥{row.get('custom_gross_rate')} -> 不含税金额: ¥{row.get('amount')} | 税额: ¥{row.get('custom_tax_amount')} | 价税合计: ¥{row.get('custom_gross_amount')}")

    # 提交发票过账
    submit_res = call_api(f'/api/resource/Purchase%20Invoice/{urllib.parse.quote(doc_name)}', method='PUT', data={"docstatus": 1})
    print(f"\n[OK] 成功过账提交发票 (docstatus=1)")

    # 检查 GL Entry 会计分录
    gl_entries = call_api(f'/api/resource/GL%20Entry?filters=[["voucher_no","=","{doc_name}"]]&fields=["account","debit","credit"]')
    print("\n==================================================")
    print(" 财务会计分录 (GL Entries)")
    print("==================================================")
    for gle in gl_entries.get('data', []):
        d = f"¥{gle['debit']}" if gle['debit'] > 0 else "-"
        c = f"¥{gle['credit']}" if gle['credit'] > 0 else "-"
        print(f"  {gle['account']:<30} | 借(Dr): {d:<12} | 贷(Cr): {c:<12}")
    print("==================================================")
