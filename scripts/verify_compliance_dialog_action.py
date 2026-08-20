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
    page = browser.new_page(viewport={"width": 1440, "height": 950})

    # 1. 登录
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")

    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/my-business")
    page.wait_for_selector(".btn-open-dialog", state="visible", timeout=15000)
    time.sleep(2)

    # 2. 点击第一条临期项目的 [安排检测 ➔] 按钮，弹出 Dialog
    page.click(".btn-open-dialog:first-of-type")
    page.wait_for_selector(".modal.show, .modal-dialog", state="visible", timeout=5000)
    time.sleep(1)

    dialog_shot = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_compliance_dialog.png"
    page.screenshot(path=dialog_shot)
    print(f"Saved Dialog Screenshot: {dialog_shot}")

    # 3. 在弹窗中点击【确认并更新台账】
    page.click(".modal.show .btn-primary, .modal-dialog .btn-primary")
    time.sleep(3)

    # 4. 截取更新后的主页（查看该项是否已自动推进/刷新）
    after_shot = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_compliance_after_update.png"
    page.screenshot(path=after_shot)
    print(f"Saved After Update Screenshot: {after_shot}")

    browser.close()
