import os
import sys
import time
import paramiko
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

# 1. 在数据库中创建一对具有红冲关联的蓝字和红字发票
HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

seed_cmd = """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 /home/frappe/frappe-bench/env/bin/python -c "
import frappe
from frappe.utils import now_datetime
from ashan_cn_procurement.services.tax_invoice_matcher import auto_reconcile_all_red_invoices
frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

# 清理历史测试数据
for no in ['26122000000088880001', '26122000000088880002']:
    if frappe.db.exists('Tax Invoice', no):
        frappe.delete_doc('Tax Invoice', no, force=1, ignore_permissions=True)

# 1. 蓝字发票 (金额 5650.00, 待录入)
blue = frappe.new_doc('Tax Invoice')
blue.invoice_no = '26122000000088880001'
blue.issue_date = '2026-08-10'
blue.invoice_type = '电子发票(增值税专用发票)'
blue.company = '天津吉众机电设备安装工程有限公司'
blue.seller_name = '天津某某自动化控制设备有限公司'
blue.seller_tax_id = '91120000MA0123456X'
blue.buyer_name = '天津吉众机电设备安装工程有限公司'
blue.buyer_tax_id = '911200000000000000'
blue.amount_without_tax = 5000.00
blue.tax_amount = 650.00
blue.invoice_grand_total = 5650.00
blue.payable_total = 5650.00
blue.display_summary = '*自动化设备* 控制器'
blue.business_status = '待录入'
blue.match_status = '未匹配'
blue.is_red_invoice = 0
blue.insert(ignore_permissions=True)

# 2. 红字发票 (金额 -5650.00, 原发票指向蓝字发票)
red = frappe.new_doc('Tax Invoice')
red.invoice_no = '26122000000088880002'
red.issue_date = '2026-08-12'
red.invoice_type = '电子发票(增值税专用发票)'
red.company = '天津吉众机电设备安装工程有限公司'
red.seller_name = '天津某某自动化控制设备有限公司'
red.seller_tax_id = '91120000MA0123456X'
red.buyer_name = '天津吉众机电设备安装工程有限公司'
red.buyer_tax_id = '911200000000000000'
red.amount_without_tax = -5000.00
red.tax_amount = -650.00
red.invoice_grand_total = -5650.00
red.payable_total = -5650.00
red.display_summary = '*自动化设备* 控制器(红字冲销)'
red.business_status = '待录入'
red.match_status = '未匹配'
red.is_red_invoice = 1
red.original_invoice_no = '26122000000088880001'
red.credit_note_no = 'HZ202608120001'
red.insert(ignore_permissions=True)

frappe.db.commit()

# 执行自动红冲对冲
res = auto_reconcile_all_red_invoices()
print('Auto Reconcile Result:', res)

b_doc = frappe.get_doc('Tax Invoice', '26122000000088880001')
r_doc = frappe.get_doc('Tax Invoice', '26122000000088880002')
print('Blue Status:', b_doc.business_status, 'Offset:', b_doc.offset_invoice)
print('Red Status:', r_doc.business_status, 'Offset:', r_doc.offset_invoice)

frappe.destroy()
"
"""
print("Executing seeding and reconciliation...")
stdin, stdout, stderr = client.exec_command(seed_cmd)
print(stdout.read().decode('utf-8', errors='replace'))
print("ERR:", stderr.read().decode('utf-8', errors='replace'))
client.close()

# 2. 启动 Playwright 进行实机验收与截图
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1500, "height": 950})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    print("Navigating to tax-invoice-center...")
    page.goto(f"{SITE_URL}/desk/tax-invoice-center")
    page.wait_for_selector(".tax-inv-wrapper", state="visible", timeout=15000)
    time.sleep(3)

    # 截图 1: 全览总表（展示已红冲对冲 KPI 与待录入统计）
    shot_overview = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tax_invoice_offset_kpi_overview.png"
    page.screenshot(path=shot_overview)
    print("Saved Overview Shot:", shot_overview)

    # 点击【已红冲对冲 (无需录入)】KPI 卡片
    print("Clicking 已红冲对冲 KPI Card...")
    page.click('.tax-kpi-card.card-offset')
    time.sleep(2)

    # 截图 2: 对冲发票专项列表（清晰展示双向冲销发票号与无需录入状态）
    shot_offset_list = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tax_invoice_offset_items_list.png"
    page.screenshot(path=shot_offset_list)
    print("Saved Offset Items Shot:", shot_offset_list)

    browser.close()

print("\n[ALL RED INVOICE AUTO OFFSET TESTS & SCREENSHOTS COMPLETED!]")
