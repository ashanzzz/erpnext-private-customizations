import os
import sys
import base64
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

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

# 1. 直接以 base64 调接口完成 2026.7 薪资导入
with open(r"d:\SynologyDrive团队\antigravity\erpnext16\祺富工资2026.7.xlsx", "rb") as f:
    b64_content = base64.b64encode(f.read()).decode("utf-8")
    b64_uri = f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_content}"

print("Calling upload_and_import_qifu_salary via API...")
r_imp = session.post(
    f"{SITE_URL}/api/method/ashan_cn_procurement.services.payroll_settlement_service.upload_and_import_qifu_salary",
    data={
        "company": "天津祺富机械加工有限公司",
        "file_data": b64_uri,
        "filename": "祺富工资2026.7.xlsx",
        "period_month": "2026-07"
    }
)
print("Import status:", r_imp.status_code)
res_msg = r_imp.json().get("message", {})
print("Imported total:", res_msg.get("total_imported"), "Message:", res_msg.get("message"))

# 2. Playwright 打开两个模态框并截图
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1850, "height": 1100})

    print("Logging in to Desk...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    page.wait_for_selector("#btn-view-salary-dist", state="visible", timeout=15000)
    time.sleep(2)

    # 1. 打开 24 列《薪资发放表》模态框并截图
    print("Opening 24-Column Salary Distribution Modal...")
    page.click("#btn-view-salary-dist")
    page.wait_for_selector(".modal-title:has-text('薪资发放表')", state="visible", timeout=10000)
    time.sleep(1)

    shot_dist = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_24col_salary_distribution_modal.png"
    page.screenshot(path=shot_dist)
    print("Saved 24-Col Distribution Modal Shot:", shot_dist)

    # 关闭当前模态框
    page.click(".modal-dialog:visible .modal-footer .btn-primary")
    time.sleep(1)

    # 2. 打开 11 列《记账工资表》模态框并截图
    print("Opening 11-Column Accounting Sheet Modal...")
    page.click("#btn-view-acc-sheet")
    page.wait_for_selector(".modal-title:has-text('记账工资表')", state="visible", timeout=10000)
    time.sleep(1)

    shot_acc = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_11col_accounting_sheet_modal.png"
    page.screenshot(path=shot_acc)
    print("Saved 11-Col Accounting Sheet Modal Shot:", shot_acc)

    browser.close()

print("\n[ALL 24-COL AND 11-COL MODALS SUCCESSFULLY CAPTURED!]")
