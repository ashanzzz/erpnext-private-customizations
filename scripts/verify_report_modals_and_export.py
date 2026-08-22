import os
import sys
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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1750, "height": 1100})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    page.wait_for_selector("#btn-view-salary-dist", state="visible", timeout=15000)
    time.sleep(2)

    # 1. 打开薪资发放表 (整合版) 模态框并截图
    print("Opening Salary Distribution Modal...")
    page.click("#btn-view-salary-dist")
    page.wait_for_selector(".modal-title:has-text('薪资发放表')", state="visible", timeout=10000)
    time.sleep(1)

    shot_dist = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_salary_distribution_modal.png"
    page.screenshot(path=shot_dist)
    print("Saved Distribution Modal Shot:", shot_dist)

    # 关闭当前模态框
    page.click(".modal-dialog:visible .btn-primary:has-text('关闭')")
    time.sleep(1)

    # 2. 打开会计记账工资表 模态框并截图
    print("Opening Accounting Sheet Modal...")
    page.click("#btn-view-acc-sheet")
    page.wait_for_selector(".modal-title:has-text('会计记账工资表')", state="visible", timeout=10000)
    time.sleep(1)

    shot_acc = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_accounting_sheet_modal.png"
    page.screenshot(path=shot_acc)
    print("Saved Accounting Sheet Modal Shot:", shot_acc)

    browser.close()

print("\n[ALL REPORT MODALS CAPTURED!]")
