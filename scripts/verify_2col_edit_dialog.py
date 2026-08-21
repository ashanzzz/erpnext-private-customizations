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
    page.wait_for_selector(".qifu-tab-btn[data-tab='employees']", state="visible", timeout=15000)
    time.sleep(2)

    # 切换到 Tab 2
    page.click(".qifu-tab-btn[data-tab='employees']")
    page.wait_for_selector("#tbody-qifu-emp tr", state="visible", timeout=10000)
    time.sleep(1)

    # 点击第一位员工的修改档案
    page.click("#tbody-qifu-emp tr:first-child .btn-qifu-edit-emp")
    page.wait_for_selector(".modal-title:has-text('修改员工薪酬档案')", state="visible", timeout=10000)
    time.sleep(1)

    shot_2col = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_employee_edit_dialog_2col.png"
    page.screenshot(path=shot_2col)
    print("Saved 2-Col Edit Dialog Shot:", shot_2col)

    browser.close()

print("\n[2-COL DIALOG CAPTURED!]")
