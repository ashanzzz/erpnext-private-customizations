import os
import json
import time
from playwright.sync_api import sync_playwright

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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

import urllib.request
for i in range(30):
    try:
        urllib.request.urlopen(f"{SITE_URL}/login", timeout=3)
        print("Server is up!")
        break
    except Exception:
        time.sleep(2)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1050})

    # 1. 登录
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")

    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 2. 前往年度房租与物业费工作台
    page.goto(f"{SITE_URL}/desk/lease-settlement-workbench")
    page.wait_for_selector("#dim-switch-group", state="visible", timeout=15000)
    time.sleep(2)

    # 3. 截取年度工作台主视图
    shot_annual_bench = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_annual_lease_workbench.png"
    page.screenshot(path=shot_annual_bench)
    print("Saved Annual Workbench Shot:", shot_annual_bench)

    # 4. 点击 [ 🔗 对账 ] 按钮，弹出极简发票对账 Dialog
    page.click(".btn-link-invoice:first-of-type")
    page.wait_for_selector(".modal.show, .modal-dialog", state="visible", timeout=5000)
    time.sleep(1)

    shot_invoice_modal = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_annual_invoice_link_modal.png"
    page.screenshot(path=shot_invoice_modal)
    print("Saved Invoice Modal Shot:", shot_invoice_modal)

    # 关闭弹窗
    page.keyboard.press("Escape")
    time.sleep(1)

    # 5. 点击 [ 🖨️ 年度对账单预览/打印 ]
    page.click("#btn-preview-bills")
    page.wait_for_selector(".modal.show, .modal-dialog", state="visible", timeout=5000)
    time.sleep(1.5)

    shot_annual_bill = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_annual_bill_preview_modal.png"
    page.screenshot(path=shot_annual_bill)
    print("Saved Annual Bill Modal Shot:", shot_annual_bill)

    browser.close()
