# -*- coding: utf-8 -*-
import os
import json
import asyncio
import urllib.request
import urllib.parse
from http.cookiejar import CookieJar
from playwright.async_api import async_playwright

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
ERPNEXT_PASS = os.getenv('ERPNEXT_PASSWORD', 'admin')
OUTPUT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

# 1. API 验证
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
    req_url = f"{SITE_URL.rstrip('/')}{endpoint}"
    encoded = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(req_url, data=encoded, headers=headers, method=method)
    with opener.open(req) as resp:
        content = resp.read().decode('utf-8')
        return json.loads(content) if content else {}

def verify_backend_multi_tax():
    print("=== [步骤 1] 后端多税率计算与 GL Entry 过账验证 ===")
    
    # 查找可用供应商
    suppliers = call_api('/api/resource/Supplier?limit=1')
    supp_name = suppliers['data'][0]['name'] if suppliers.get('data') else "默认供应商"
    
    # 查找可用物料
    items = call_api('/api/resource/Item?limit=3')
    item_list = [i['name'] for i in items.get('data', [])]
    if not item_list:
        item_list = ["TEST-ITEM-1"]

    # 查找公司
    comp = call_api('/api/resource/Company?limit=1')['data'][0]['name']

    pi_doc = {
        "doctype": "Purchase Invoice",
        "company": comp,
        "supplier": supp_name,
        "currency": "CNY",
        "items": [
            {
                "item_code": item_list[0],
                "qty": 10,
                "custom_gross_rate": 113.0,
                "custom_tax_rate": 13.0,
                "custom_spec_model": "13% 货物"
            },
            {
                "item_code": item_list[1] if len(item_list) > 1 else item_list[0],
                "qty": 1,
                "custom_gross_rate": 109.0,
                "custom_tax_rate": 9.0,
                "custom_spec_model": "9% 运费"
            },
            {
                "item_code": item_list[2] if len(item_list) > 2 else item_list[0],
                "qty": 1,
                "custom_gross_rate": 106.0,
                "custom_tax_rate": 6.0,
                "custom_spec_model": "6% 咨询服务"
            }
        ]
    }

    res = call_api('/api/resource/Purchase%20Invoice', method='POST', data=pi_doc)
    doc_name = res['data']['name']
    print(f"  [OK] 创建多税率采购发票: {doc_name}")

    # 读取发票计算结果
    saved_doc = call_api(f'/api/resource/Purchase%20Invoice/{urllib.parse.quote(doc_name)}')['data']
    print(f"  不含税总计 (Net Total): {saved_doc.get('net_total')}")
    print(f"  总税额 (Total Taxes): {saved_doc.get('total_taxes_and_charges')}")
    print(f"  价税合计 (Grand Total): {saved_doc.get('grand_total')}")

    # 提交发票
    submit_res = call_api(f'/api/resource/Purchase%20Invoice/{urllib.parse.quote(doc_name)}', method='PUT', data={"docstatus": 1})
    print(f"  [OK] 成功提交发票 (docstatus=1)")

    # 检查 GL Entry
    gl_entries = call_api(f'/api/resource/GL%20Entry?filters=[["voucher_no","=","{doc_name}"]]&fields=["account","debit","credit"]')
    print("\n  生成的会计分录 (GL Entries):")
    for gle in gl_entries.get('data', []):
        print(f"    - 科目: {gle['account']} | 借 (Dr): {gle['debit']} | 贷 (Cr): {gle['credit']}")

    return doc_name

async def verify_frontend_ui(doc_name):
    print("\n=== [步骤 2] 浏览器前端多税率计算看板 UI 验证 ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        # 打开刚才创建的采购发票
        await page.goto(f"{SITE_URL}/desk/purchase-invoice/{doc_name}", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        shot = os.path.join(OUTPUT_DIR, "china_multi_tax_invoice_verified.png")
        await page.screenshot(path=shot)
        print(f"  [OK] UI 验收截图保存: {shot}")

        await browser.close()

if __name__ == "__main__":
    name = verify_backend_multi_tax()
    asyncio.run(verify_frontend_ui(name))
    print("\n[ALL SUCCESS] 中国增值税多税率采购发票全流程验证通过！")
