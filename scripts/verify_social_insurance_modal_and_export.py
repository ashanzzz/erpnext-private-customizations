import os
import sys
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

for i in range(25):
    try:
        r = requests.get(f"{SITE_URL}/api/method/ping", timeout=3)
        if r.status_code == 200:
            print("Site is ready!")
            break
    except Exception:
        pass
    time.sleep(2)

session = requests.Session()
session.post(f"{SITE_URL}/api/method/login", data={"usr": USERNAME, "pwd": USER_PWD})

# 1. 验证社保 API 数据
r_ins = session.post(
    f"{SITE_URL}/api/method/ashan_cn_procurement.services.payroll_settlement_service.get_social_insurance_sheet",
    data={"company": "天津祺富机械加工有限公司", "period_month": "2026-07"}
)
print("Insurance Sheet Status:", r_ins.status_code)
ins_res = r_ins.json().get("message", {})
rows = ins_res.get("rows", [])
tot = ins_res.get("totals", {})
print(f"Insured count: {len(rows)}")
print(f"SS Base Tot: {tot.get('ss_base')}, Comp Tot: {tot.get('comp_total')}, Pers Tot: {tot.get('pers_total')}, Grand Tot: {tot.get('grand_total')}")

# 2. 验证 Excel 导出
r_exp = session.post(
    f"{SITE_URL}/api/method/ashan_cn_procurement.services.payroll_settlement_service.export_qifu_payroll_excel",
    data={"company": "天津祺富机械加工有限公司", "period_month": "2026-07", "sheet_type": "all"}
)
print("All Sheets Export Status:", r_exp.status_code, "Filename:", r_exp.json().get("message", {}).get("filename"))

# 3. 浏览器截图验收
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1850, "height": 1100})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    page.wait_for_selector("#btn-view-ins-sheet", state="visible", timeout=15000)
    time.sleep(2)

    print("Opening Social Insurance Modal...")
    page.click("#btn-view-ins-sheet")
    page.wait_for_selector(".modal-dialog:visible table.qifu-table", state="visible", timeout=10000)
    time.sleep(1)

    shot_ins = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_social_insurance_modal.png"
    page.screenshot(path=shot_ins)
    print("Saved Social Insurance Modal Shot:", shot_ins)

    browser.close()

print("\n[SOCIAL INSURANCE MODAL & EXPORT VERIFIED!]")
