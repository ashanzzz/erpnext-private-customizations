import os
import sys
import time
import paramiko
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# 1. 种子数据
HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

seed_cmd = """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 /home/frappe/frappe-bench/env/bin/python -c "
import frappe
from ashan_cn_procurement.services.tax_invoice_matcher import update_tax_invoice_match_state
frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

inv_no = '26122000000099990001'
if frappe.db.exists('Tax Invoice', inv_no):
    frappe.delete_doc('Tax Invoice', inv_no, force=1, ignore_permissions=True)

# 创建税局发票 (金额 ¥3,390.00)
doc = frappe.new_doc('Tax Invoice')
doc.invoice_no = inv_no
doc.issue_date = '2026-08-18'
doc.invoice_type = '电子发票(增值税专用发票)'
doc.company = '天津吉众机电设备有限公司'
doc.seller_name = '天津市某某科技有限公司'
doc.buyer_name = '天津吉众机电设备有限公司'
doc.amount_without_tax = 3000.00
doc.tax_amount = 390.00
doc.invoice_grand_total = 3390.00
doc.payable_total = 3390.00
doc.display_summary = '*自动化配件* 传感器'
doc.business_status = '待录入'
doc.match_status = '未匹配'
doc.insert(ignore_permissions=True)

# 模拟 ERP 采购发票金额填写错误 (ERP 录成了 ¥3,000.00, 与税局 ¥3,390.00 不一致)
pi_dict = {
    'name': 'ACC-PINV-2026-00088',
    'bill_no': inv_no,
    'grand_total': 3000.00,
    'rounded_total': 3000.00,
    'docstatus': 0
}
update_tax_invoice_match_state(doc, matched_pis=[pi_dict])
frappe.db.commit()
print('Seeded and match updated successfully!')
frappe.destroy()
"
"""
stdin, stdout, stderr = client.exec_command(seed_cmd)
print("SEED OUT:", stdout.read().decode('utf-8', errors='replace'))
print("SEED ERR:", stderr.read().decode('utf-8', errors='replace'))
client.close()

# 2. 启动 Playwright 截图
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 950})
    page.goto(os.getenv('ERPNEXT_SITE_URL') + '/login')
    page.fill('#login_email', os.getenv('ERPNEXT_USERNAME'))
    page.fill('#login_password', os.getenv('ERPNEXT_PASSWORD'))
    page.click("button[type='submit']")
    page.wait_for_url('**/desk**')
    page.goto(os.getenv('ERPNEXT_SITE_URL') + '/desk/tax-invoice-center')
    page.wait_for_selector('.tax-inv-wrapper')
    time.sleep(2)
    
    # 搜索该发票
    page.fill('#filter-search', '26122000000099990001')
    time.sleep(3)
    
    shot_path = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tax_invoice_exact_mismatch_single_view.png"
    page.screenshot(path=shot_path)
    print("Saved single view shot:", shot_path)
    browser.close()
