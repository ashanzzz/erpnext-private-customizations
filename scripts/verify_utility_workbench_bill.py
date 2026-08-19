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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1050})

    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")

    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 前往水电费工作台
    page.goto(f"{SITE_URL}/desk/property-settlement-workbench")
    page.wait_for_selector("#btn-preview-bills", state="visible", timeout=15000)
    time.sleep(2)

    # 点击 [ 🖨️ 单证预览/打印 ]
    page.click("#btn-preview-bills")
    page.wait_for_selector(".modal.show, .modal-dialog", state="visible", timeout=5000)
    time.sleep(2)

    shot_utility_bill = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_utility_bill_decomposed_tax.png"
    page.screenshot(path=shot_utility_bill)
    print("Saved Utility Bill Shot:", shot_utility_bill)

    browser.close()
